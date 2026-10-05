import asyncio
import json

import pytest

from core.audit import AuditLog, MemorySink
from core.llm import (
    LlmCallError,
    LlmClient,
    LlmConfigError,
    LlmUnavailable,
    TransportResponse,
    UnknownFeature,
    parse_config,
)

KEY_A1 = "nvapi-" + "a" * 24  # 런타임 조립
KEY_A2 = "nvapi-" + "b" * 24
KEY_B = "nvapi-" + "c" * 24
ENV = {"K_A1": KEY_A1, "K_A2": KEY_A2, "K_B": KEY_B}
BODY = "SECRET-BODY-" + "z" * 8  # 메시지 본문 표지


def _cfg(conc_a=2, conc_b=2, cooldown=10.0, timeout=5.0):
    return parse_config(
        {
            "providers": {
                "pa": {"api_key_envs": ["K_A1", "K_A2"], "base_url": "http://a",
                       "max_concurrency": conc_a, "cooldown_s": cooldown, "timeout_s": timeout},
                "pb": {"api_key_envs": ["K_B"], "base_url": "http://b",
                       "max_concurrency": conc_b, "cooldown_s": cooldown, "timeout_s": timeout},
            },
            "features": {
                "feature1": {"provider": "pa", "model": "model-a"},
                "feature2": {"provider": "pb", "model": "model-b"},
            },
        },
        ENV,
    )


class FakeTransport:
    def __init__(self, delays=None, statuses=None, raises=None):
        self.delays = delays or {}
        self.statuses = list(statuses or [])
        self.raises = raises
        self.calls = []  # (provider, model, api_key)
        self.active = {}
        self.peak = {}

    async def send(self, *, provider, model, api_key, messages):
        self.calls.append((provider.name, model, api_key))
        n = self.active.get(provider.name, 0) + 1
        self.active[provider.name] = n
        self.peak[provider.name] = max(self.peak.get(provider.name, 0), n)
        try:
            await asyncio.sleep(self.delays.get(provider.name, 0))
            if self.raises:
                raise self.raises
            status = self.statuses.pop(0) if self.statuses else 200
            return TransportResponse(status, f"ok:{provider.name}:{model}")
        finally:
            self.active[provider.name] -= 1


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    async def sleep(self, s):
        self.t += s


def _client(transport, cfg=None, clock=None):
    sink = MemorySink()
    log = AuditLog(sink, run_id="r1", actor="llm-test")
    clock = clock or Clock()
    c = LlmClient(cfg or _cfg(), transport, log, env=ENV, clock=clock, sleep=clock.sleep)
    return c, sink, clock


MSGS = [{"role": "user", "content": BODY}]


async def test_routing_by_feature():
    t = FakeTransport()
    c, _, _ = _client(t)
    assert await c.complete("feature1", MSGS) == "ok:pa:model-a"
    assert await c.complete("feature2", MSGS) == "ok:pb:model-b"
    assert [x[:2] for x in t.calls] == [("pa", "model-a"), ("pb", "model-b")]


async def test_unknown_feature_and_bad_messages():
    t = FakeTransport()
    c, sink, _ = _client(t)
    with pytest.raises(UnknownFeature):
        await c.complete("nope", MSGS)
    for bad in ([], "hi", [{"role": "user"}], [{"content": "x"}]):
        with pytest.raises(ValueError):
            await c.complete("feature1", bad)
    assert t.calls == [] and sink.events == []


def test_missing_env_at_construction_names_only():
    sink = MemorySink()
    log = AuditLog(sink, run_id="r", actor="a")
    with pytest.raises(LlmConfigError) as ei:
        LlmClient(_cfg(), FakeTransport(), log, env={"K_A1": KEY_A1, "K_B": KEY_B})
    assert "K_A2" in str(ei.value)
    assert KEY_A1 not in str(ei.value) and KEY_B not in str(ei.value)


async def test_round_robin_keys_across_calls():
    t = FakeTransport()
    c, _, _ = _client(t)
    for _ in range(3):
        await c.complete("feature1", MSGS)
    assert [x[2] for x in t.calls] == [KEY_A1, KEY_A2, KEY_A1]


async def test_429_cools_key_and_retries_next_then_recovers():
    t = FakeTransport(statuses=[429])
    c, _, clock = _client(t)
    assert await c.complete("feature1", MSGS) == "ok:pa:model-a"
    assert [x[2] for x in t.calls] == [KEY_A1, KEY_A2]  # A1 쿨다운 → A2 로 재시도
    # A1 은 쉬는 중: 다음 두 호출은 모두 A2
    await c.complete("feature1", MSGS)
    await c.complete("feature1", MSGS)
    assert [x[2] for x in t.calls][2:] == [KEY_A2, KEY_A2]
    clock.t += 10.0  # 복귀
    await c.complete("feature1", MSGS)
    await c.complete("feature1", MSGS)
    assert KEY_A1 in [x[2] for x in t.calls][4:]


async def test_5xx_cools_and_all_keys_failing_raises_call_error():
    t = FakeTransport(statuses=[503, 500])
    c, sink, _ = _client(t)
    with pytest.raises(LlmCallError):
        await c.complete("feature1", MSGS)
    assert [e.phase for e in sink.events] == ["call", "error"]


async def test_non_retryable_4xx_no_cooldown():
    t = FakeTransport(statuses=[400, 200])
    c, _, _ = _client(t)
    with pytest.raises(LlmCallError):
        await c.complete("feature1", MSGS)
    await c.complete("feature1", MSGS)
    assert [x[2] for x in t.calls] == [KEY_A1, KEY_A2]  # 쿨다운 없이 라운드로빈 계속


async def test_all_keys_cooling_times_out_unavailable():
    t = FakeTransport(statuses=[429, 429])
    c, sink, _ = _client(t, _cfg(cooldown=100.0, timeout=5.0))
    with pytest.raises(LlmCallError):
        await c.complete("feature1", MSGS)  # 두 키 모두 쿨다운
    with pytest.raises(LlmUnavailable):
        await c.complete("feature1", MSGS)
    assert len(t.calls) == 2
    assert [e.phase for e in sink.events] == ["call", "error", "call", "error"]
    assert sink.events[-1].data["error_type"] == "LlmUnavailable"


async def test_slow_provider_a_does_not_block_provider_b():
    t = FakeTransport(delays={"pa": 0.3, "pb": 0.0})
    c, _, _ = _client(t)
    done = []

    async def run(feature):
        await c.complete(feature, MSGS)
        done.append(feature)

    await asyncio.gather(run("feature1"), run("feature2"))
    assert done == ["feature2", "feature1"]


async def test_slow_provider_saturated_still_serves_other_provider():
    t = FakeTransport(delays={"pa": 0.2})
    c, _, _ = _client(t, _cfg(conc_a=1))
    done = []

    async def run(feature):
        await c.complete(feature, MSGS)
        done.append(feature)

    tasks = [asyncio.create_task(run("feature1")) for _ in range(3)]
    await asyncio.sleep(0.01)
    await run("feature2")
    assert done == ["feature2"]
    await asyncio.gather(*tasks)


async def test_max_concurrency_respected():
    t = FakeTransport(delays={"pa": 0.02, "pb": 0.02})
    c, _, _ = _client(t, _cfg(conc_a=2, conc_b=1))
    await asyncio.gather(
        *[c.complete("feature1", MSGS) for _ in range(6)],
        *[c.complete("feature2", MSGS) for _ in range(4)],
    )
    assert t.peak["pa"] == 2
    assert t.peak["pb"] == 1
    assert len(t.calls) == 10


async def test_audit_events_have_no_key_or_body():
    t = FakeTransport()
    c, sink, _ = _client(t)
    await c.complete("feature1", MSGS)
    assert [e.phase for e in sink.events] == ["call", "result"]
    call = sink.events[0]
    assert call.name == "llm:feature1"
    assert call.data["args"] == {"model": "model-a", "messages": 1}
    dump = "\n".join(e.to_json() for e in sink.events)
    for secret in (KEY_A1, KEY_A2, KEY_B, BODY):
        assert secret not in dump


async def test_transport_exception_error_event_and_key_cooldown():
    leak = RuntimeError(f"boom {KEY_A1} {BODY}")
    t = FakeTransport(raises=leak)
    c, sink, _ = _client(t)
    with pytest.raises(LlmCallError) as ei:
        await c.complete("feature1", MSGS)
    assert KEY_A1 not in str(ei.value) and "RuntimeError" in str(ei.value)
    assert [e.phase for e in sink.events] == ["call", "error"]
    err = sink.events[1]
    assert err.data["ok"] is False
    dump = "\n".join(e.to_json() for e in sink.events)
    assert KEY_A1 not in dump and BODY not in dump
    json.loads(sink.events[1].to_json())
    # 예외를 낸 키 A1 은 쉬는 중이라 다음 호출은 A2
    t.raises = None
    await c.complete("feature1", MSGS)
    assert t.calls[-1][2] == KEY_A2
