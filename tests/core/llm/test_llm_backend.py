"""API ↔ 로컬 백엔드 스위치 — 키는 provider 단위, 바뀌는 것은 엔드포인트뿐."""

import asyncio

import pytest

from core.audit import AuditLog, MemorySink
from core.llm import LlmClient, LlmConfigError, TransportResponse, parse_config, resolve_backend

KEY_A = "nvapi-" + "a" * 24  # 런타임 조립
KEY_B = "nvapi-" + "b" * 24
KEY_LA = "local-" + "l" * 16
ENV = {"K_A": KEY_A, "K_B": KEY_B, "K_LA": KEY_LA}
MSGS = [{"role": "user", "content": "hi"}]


def _data(local_a=True, local_b=True, local_keys_a=("K_LA",)):
    pa = {"api_key_envs": ["K_A"], "base_url": "http://api-a", "max_concurrency": 2}
    pb = {"api_key_envs": ["K_B"], "base_url": "http://api-b", "max_concurrency": 2}
    if local_a:
        pa.update(local_base_url="http://local-a", local_api_key_envs=list(local_keys_a))
    if local_b:
        pb.update(local_base_url="http://local-b")  # 키 없는 로컬
    return {
        "providers": {"pa": pa, "pb": pb},
        "features": {
            "feature1": {"provider": "pa", "model": "m-a"},
            "feature2": {"provider": "pb", "model": "m-b"},
        },
    }


class FakeTransport:
    def __init__(self, delay=0.0, statuses=None):
        self.full = []  # (provider, base_url, api_key)
        self.delay = delay
        self.statuses = list(statuses or [])

    async def send(self, *, provider, model, base_url, api_key, messages):
        self.full.append((provider.name, base_url, api_key))
        await asyncio.sleep(self.delay)
        return TransportResponse(self.statuses.pop(0) if self.statuses else 200, "ok")


def _client(env, data=None, transport=None):
    sink = MemorySink()
    log = AuditLog(sink, run_id="r", actor="t")
    cfg = parse_config(data or _data())
    return LlmClient(cfg, transport or FakeTransport(), log, env=env), sink


def test_resolve_backend_precedence():
    assert resolve_backend("feature1", {}) == "api"
    assert resolve_backend("feature1", {"LLM_BACKEND": "local"}) == "local"
    env = {"LLM_BACKEND": "local", "LLM_BACKEND_FEATURE1": "api"}
    assert resolve_backend("feature1", env) == "api"
    assert resolve_backend("feature2", env) == "local"
    assert resolve_backend("my.feat-1", {"LLM_BACKEND_MY_FEAT_1": "local"}) == "local"


@pytest.mark.parametrize("bad", ["LOCAL", "", "remote", " local"])
def test_invalid_value_rejected_names_only(bad):
    with pytest.raises(LlmConfigError) as ei:
        resolve_backend("feature1", {"LLM_BACKEND_FEATURE1": bad})
    assert "LLM_BACKEND_FEATURE1" in str(ei.value) and "local" in str(ei.value)
    if bad.strip():
        assert bad not in str(ei.value).replace("local", "").replace("LLM_BACKEND_FEATURE1", "")
    with pytest.raises(LlmConfigError, match="LLM_BACKEND "):
        resolve_backend("feature1", {"LLM_BACKEND": bad})


def test_local_without_local_base_url_fails_closed_at_construction():
    d = _data(local_a=False)
    with pytest.raises(LlmConfigError, match="local_base_url"):
        _client({**ENV, "LLM_BACKEND_FEATURE1": "local"}, d)
    # api 로 쓰는 provider 에는 local_base_url 이 없어도 된다
    _client({**ENV, "LLM_BACKEND_FEATURE2": "local"}, d)
    # parse_config(env) 단계에서도 막는다
    with pytest.raises(LlmConfigError, match="local_base_url"):
        parse_config(d, {**ENV, "LLM_BACKEND": "local"})


def test_local_keys_validated_by_name_only_and_api_keys_not_needed_for_local():
    env = {"LLM_BACKEND": "local"}  # api 키는 하나도 없다
    c, _ = _client({**env, "K_LA": KEY_LA})
    assert c is not None
    with pytest.raises(LlmConfigError) as ei:
        _client(env)
    assert "K_LA" in str(ei.value) and KEY_LA not in str(ei.value)


async def test_default_is_api():
    t = FakeTransport()
    c, sink = _client(ENV, transport=t)
    await c.complete("feature1", MSGS)
    assert t.full == [("pa", "http://api-a", KEY_A)]
    assert sink.events[0].data["args"]["backend"] == "api"


async def test_global_local_and_feature_override_and_audit_backend():
    t = FakeTransport()
    c, sink = _client({**ENV, "LLM_BACKEND": "local", "LLM_BACKEND_FEATURE2": "api"}, transport=t)
    await c.complete("feature1", MSGS)
    await c.complete("feature2", MSGS)
    assert t.full == [("pa", "http://local-a", KEY_LA), ("pb", "http://api-b", KEY_B)]
    calls = [e for e in sink.events if e.phase == "call"]
    assert [e.data["args"]["backend"] for e in calls] == ["local", "api"]
    dump = repr(sink.events)
    assert KEY_A not in dump and KEY_B not in dump and KEY_LA not in dump


async def test_local_without_keys_sends_none():
    t = FakeTransport()
    c, _ = _client({**ENV, "LLM_BACKEND": "local"}, transport=t)
    await c.complete("feature2", MSGS)
    assert t.full == [("pb", "http://local-b", None)]


async def test_mixed_backends_concurrently_do_not_mix_pools_or_urls():
    t = FakeTransport(delay=0.02)
    env = {**ENV, "LLM_BACKEND_FEATURE1": "local"}
    c, _ = _client(env, transport=t)
    await asyncio.gather(*[c.complete(f, MSGS) for f in ("feature1", "feature2") * 3])
    assert set(t.full) == {("pa", "http://local-a", KEY_LA), ("pb", "http://api-b", KEY_B)}
    assert len(t.full) == 6


async def test_same_provider_two_backends_have_separate_pools_and_cooldown():
    d = _data()
    d["features"]["feature3"] = {"provider": "pa", "model": "m-a3"}
    t = FakeTransport(statuses=[429])
    c, _ = _client({**ENV, "LLM_BACKEND_FEATURE3": "local"}, d, t)
    with pytest.raises(Exception, match="모든 키"):
        await c.complete("feature1", MSGS)  # api 키 하나뿐 → 429 로 쿨다운
    await c.complete("feature3", MSGS)  # local 풀은 영향 없음
    assert t.full[-1] == ("pa", "http://local-a", KEY_LA)


# ---- 세마포어: (provider, backend) 별 ----------------------------------------------------------


class GaugeTransport:
    """백엔드(base_url)별 동시 진행 수와 최대치를 잰다. 이름 `local` 이 든 URL 만 느리다."""

    def __init__(self, local_delay=0.1, api_delay=0.0):
        self.cur: dict[str, int] = {}
        self.peak: dict[str, int] = {}
        self.delays = {"http://local-a": local_delay, "http://api-a": api_delay}

    async def send(self, *, provider, model, base_url, api_key, messages):
        self.cur[base_url] = self.cur.get(base_url, 0) + 1
        self.peak[base_url] = max(self.peak.get(base_url, 0), self.cur[base_url])
        await asyncio.sleep(self.delays.get(base_url, 0.0))
        self.cur[base_url] -= 1
        return TransportResponse(200, "ok")


def _two_feature_same_provider(**pa_extra):
    d = _data(local_b=False)
    d["providers"]["pa"].update(pa_extra)
    d["features"]["feature3"] = {"provider": "pa", "model": "m-a3"}  # 이 기능만 local
    return d


async def test_slow_local_does_not_block_api_of_same_provider():
    t = GaugeTransport(local_delay=0.3)
    d = _two_feature_same_provider()  # max_concurrency=2
    c, _ = _client({**ENV, "LLM_BACKEND_FEATURE3": "local"}, d, t)
    slow = [asyncio.create_task(c.complete("feature3", MSGS)) for _ in range(4)]
    await asyncio.sleep(0.05)  # local 이 상한(2)까지 점유 중
    assert t.cur["http://local-a"] == 2
    loop = asyncio.get_running_loop()
    start = loop.time()
    await asyncio.wait_for(c.complete("feature1", MSGS), timeout=0.2)
    assert loop.time() - start < 0.2
    await asyncio.gather(*slow)


async def test_each_backend_respects_its_own_limit():
    t = GaugeTransport(local_delay=0.05, api_delay=0.05)
    d = _two_feature_same_provider(local_max_concurrency=1)  # api 2, local 1
    c, _ = _client({**ENV, "LLM_BACKEND_FEATURE3": "local"}, d, t)
    await asyncio.gather(
        *[c.complete(f, MSGS) for f in ("feature1", "feature3") * 4],
    )
    assert t.peak["http://api-a"] == 2
    assert t.peak["http://local-a"] == 1


async def test_local_limit_defaults_to_max_concurrency_with_separate_semaphore():
    t = GaugeTransport(local_delay=0.05, api_delay=0.05)
    d = _two_feature_same_provider()  # local_max_concurrency 없음 → 2
    c, _ = _client({**ENV, "LLM_BACKEND_FEATURE3": "local"}, d, t)
    await asyncio.gather(*[c.complete(f, MSGS) for f in ("feature1", "feature3") * 4])
    assert t.peak["http://api-a"] == 2
    assert t.peak["http://local-a"] == 2


@pytest.mark.parametrize("bad", [0, -1, 1.5, True, "2", None])
def test_local_max_concurrency_validated(bad):
    d = _data()
    d["providers"]["pa"]["local_max_concurrency"] = bad
    with pytest.raises(LlmConfigError, match="local_max_concurrency"):
        parse_config(d)


# ---- api 키가 로컬 서버로 가는 것을 막는다 -------------------------------------------------------


def test_local_keys_overlapping_same_provider_api_keys_rejected_names_only():
    d = _data(local_keys_a=("K_A",))
    with pytest.raises(LlmConfigError) as ei:
        parse_config(d)
    assert "K_A" in str(ei.value) and KEY_A not in str(ei.value)
    with pytest.raises(LlmConfigError):
        parse_config(d, ENV)


def test_local_keys_overlapping_other_provider_api_keys_rejected():
    d = _data(local_keys_a=("K_B",))  # pa 의 local 이 pb 의 api 키를 가리킨다
    with pytest.raises(LlmConfigError) as ei:
        parse_config(d)
    assert "K_B" in str(ei.value) and KEY_B not in str(ei.value)


def test_distinct_local_keys_accepted_and_local_overlap_between_locals_allowed():
    d = _data(local_keys_a=("K_LA",))
    d["providers"]["pb"]["local_api_key_envs"] = ["K_LA"]  # local 끼리 공유는 허용
    parse_config(d)


# ---- LLM_BACKEND_<FEATURE> 이름 충돌 -----------------------------------------------------------


@pytest.mark.parametrize("names", [("a.b", "a-b"), ("a_b", "A_B"), ("a.b", "a_b")])
def test_feature_env_name_collision_rejected(names):
    d = _data()
    d["features"] = {n: {"provider": "pa", "model": "m"} for n in names}
    with pytest.raises(LlmConfigError, match="LLM_BACKEND_A_B"):
        parse_config(d)


def test_non_colliding_feature_names_accepted():
    d = _data()
    d["features"]["a.b"] = {"provider": "pa", "model": "m"}
    d["features"]["a.c"] = {"provider": "pa", "model": "m"}
    parse_config(d)
