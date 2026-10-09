"""D15 보충 2 — QUOTE_NOT_FOUND 부분 결과: 예산 안 1회 재시도 + 캐시 제외. 가짜 complete·가짜 clock."""

import json

import pytest

from domains.kcontext.index import LocalIndex
from domains.kcontext.pipeline import __main__ as cli
from domains.kcontext.pipeline.run import run_story_pipeline
from domains.kcontext.places import load_places
from domains.kcontext.schedule import ScheduleCache, key_for, understand_with_meta

TRIP = ("2026-10-15", "2026-10-16")
TEXT = "10/15 10시에 ○○궁, 2시 ○○동"
TRIPKW = {"trip_from": TRIP[0], "trip_to": TRIP[1]}
A1 = {"type": "visit", "name": "○○궁", "date": "10-15", "from": "10:00", "to": None,
      "quote": "10/15 10시에 ○○궁"}  # fmt: skip
A2 = {"type": "visit", "name": "○○동", "date": "10-15", "from": "14:00", "to": None,
      "quote": "10/15 10시에 ○○궁, 2시 ○○동"}  # fmt: skip
BAD = {"type": "visit", "name": "○○동", "date": "10-15", "from": "14:00", "to": None,
       "quote": "원문에 없는 구절"}  # fmt: skip


def reply(*anchors):
    return json.dumps({"anchors": list(anchors)}, ensure_ascii=False)


ONE = reply(A1, BAD)  # 앵커 1 + QUOTE_NOT_FOUND
TWO = reply(A1, A2)  # 앵커 2, 문제 없음


class Seq:
    def __init__(self, replies, step=0.0):
        self.replies, self.step, self.now, self.n = list(replies), step, 0.0, 0

    def __call__(self, system, user):
        r = self.replies[min(self.n, len(self.replies) - 1)]
        self.n += 1
        self.now += self.step
        if isinstance(r, Exception):
            raise r
        return r

    def clock(self):
        return self.now


def codes(r):
    return [p["code"] for p in r["problems"]]


def run(s, **kw):
    kw.setdefault("max_attempts", 2)
    return understand_with_meta(TEXT, complete=s, clock=s.clock, **TRIPKW, **kw)


def test_partial_retry_second_has_more_anchors_is_selected():
    s = Seq([ONE, TWO])
    r, meta = run(s)
    assert len(r["anchors"]) == 2 and meta["attempts"] == 2 and s.n == 2
    assert codes(r)[0] == "LLM_RETRY" and "QUOTE_NOT_FOUND" not in codes(r)
    assert r["problems"][0]["message"] == "1회차 QUOTE_NOT_FOUND 후 재시도"


@pytest.mark.parametrize("second", [ONE, reply(A1), reply(BAD, A1)])
def test_partial_retry_second_not_better_keeps_first(second):
    s = Seq([ONE, second])
    r, meta = run(s)
    assert len(r["anchors"]) == 1 and meta["attempts"] == 2
    assert codes(r)[0] == "LLM_RETRY" and "QUOTE_NOT_FOUND" in codes(r)


def test_partial_retry_second_llm_failure_keeps_first():
    s = Seq([ONE, RuntimeError("x")])
    r, meta = run(s)
    assert len(r["anchors"]) == 1 and s.n == 2 and meta["attempts"] == 2
    assert "LLM_FAILED" not in codes(r) and "QUOTE_NOT_FOUND" in codes(r)
    assert codes(r)[0] == "LLM_RETRY"


def test_partial_retry_skipped_when_budget_short():
    s = Seq([ONE, TWO], step=50)
    r, meta = run(s, budget_s=75, attempt_timeout_s=40)
    assert s.n == 1 and meta["attempts"] == 1 and len(r["anchors"]) == 1
    assert codes(r)[0] == "RETRY_SKIPPED_BUDGET" and "QUOTE_NOT_FOUND" in codes(r)


def test_partial_retry_counts_key_wait():
    s = Seq([ONE, TWO])
    r, _ = run(s, budget_s=75, attempt_timeout_s=40, key_wait=lambda: 40.0)
    assert s.n == 1 and "RETRY_SKIPPED_BUDGET" in codes(r)


def test_partial_retry_off_switch():
    s = Seq([ONE, TWO])
    r, meta = run(s, retry_partial=False)
    assert s.n == 1 and meta["attempts"] == 1 and codes(r).count("LLM_RETRY") == 0


def test_llm_failure_then_partial_total_calls_capped_at_two():
    s = Seq([RuntimeError("x"), ONE, TWO])
    r, meta = run(s)
    assert s.n == 2 and meta["attempts"] == 2 and "QUOTE_NOT_FOUND" in codes(r)


def test_no_partial_retry_without_quote_not_found():
    s = Seq([TWO, ONE])
    _, meta = run(s)
    assert s.n == 1 and meta["attempts"] == 1


# ---- 캐시


@pytest.fixture
def env(tmp_path):
    rows = [{"name": n, "aliases": [], "lat": 37.5, "lng": 127.0, "source": "합성",
             "verified_at": "2026-10-07", "note": ""} for n in ("○○궁", "○○동")]  # fmt: skip
    p = tmp_path / "places.json"
    p.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    cache = ScheduleCache(tmp_path / "cache")
    key = key_for(TEXT, TRIP)
    with LocalIndex(":memory:") as idx:

        def go(complete, **kw):
            return run_story_pipeline(TEXT, complete=complete, db=idx, trip=TRIP,
                                      places=load_places(p), cache=cache, cache_key=key, **kw)  # fmt: skip

        yield go, cache, key


def test_cache_saved_when_retry_resolves_partial(env):
    go, cache, key = env
    b = go(Seq([ONE, TWO]))
    assert len(b["itinerary"]["anchors"]) == 2 and "QUOTE_NOT_FOUND" not in codes(b)
    assert cache.get(key) is not None


def test_cache_skipped_when_quote_not_found_remains(env):
    go, cache, key = env
    b = go(Seq([ONE, ONE]))
    assert "QUOTE_NOT_FOUND" in codes(b) and cache.get(key) is None


def test_cache_skipped_when_budget_skips_retry(env):
    go, cache, key = env
    s = Seq([ONE, TWO])
    # 파이프라인은 실제 시계를 쓰므로 키 대기로 예산을 넘긴다
    b = go(s, budget_s=75, attempt_timeout_s=40, key_wait=lambda: 100.0)
    assert s.n == 1 and "RETRY_SKIPPED_BUDGET" in codes(b) and cache.get(key) is None


def test_cli_env_off_disables_partial_retry(tmp_path, monkeypatch):
    llm = Seq([ONE, TWO])
    monkeypatch.setattr(cli, "_make_complete", lambda: llm)
    monkeypatch.setenv("KC_VAR_DIR", str(tmp_path / "var"))
    monkeypatch.setenv("KC_SCHEDULE_CACHE", "off")
    monkeypatch.setenv("KC_SCHEDULE_RETRY_PARTIAL", "off")
    db, txt = tmp_path / "i.db", tmp_path / "t.txt"
    LocalIndex(db).close()
    txt.write_text(TEXT, encoding="utf-8")
    args = ["--text-file", str(txt), "--trip-from", TRIP[0], "--trip-to", TRIP[1],
            "--db", str(db), "--out", str(tmp_path / "o")]  # fmt: skip
    assert cli.main(args) == 0
    assert llm.n == 1


def _write_cache(cache, key, res, v=2):
    cache.root.mkdir(parents=True, exist_ok=True)
    body = {"v": v, "created_at": "2026-10-01T00:00:00Z", "meta": {"model": "m", "prompt_sha": "p"},
            "result": res}  # fmt: skip
    (cache.root / f"{key}.json").write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")


def _res(problems):
    return {"anchors": [dict(A1)], "free_slots": [], "problems": problems}


def test_cache_partial_entry_is_not_a_hit(env):
    go, cache, key = env
    _write_cache(cache, key, _res([{"code": "QUOTE_NOT_FOUND", "message": "x"}]))
    s = Seq([TWO])
    b = go(s)
    assert s.n == 1 and b["schedule"]["source"] == "llm" and len(b["itinerary"]["anchors"]) == 2


def test_cache_v1_entry_is_not_a_hit(env):
    go, cache, key = env
    _write_cache(cache, key, _res([]), v=1)
    s = Seq([TWO])
    b = go(s)
    assert s.n == 1 and b["schedule"]["source"] == "llm"


def test_cache_clean_entry_is_a_hit(env):
    go, cache, key = env
    _write_cache(cache, key, _res([]))
    s = Seq([TWO])
    b = go(s)
    assert s.n == 0 and b["schedule"]["source"] == "cache"


ZERO = reply(BAD)  # 후보가 전부 quote 검증에서 버려짐 → 앵커 0 + QUOTE_NOT_FOUND


def test_default_zero_anchors_quote_not_found_second_better_is_selected(env):
    go, _, _ = env
    s = Seq([ZERO, TWO])
    b = go(s)  # 기본 설정: retry_partial 켬, retry_unverified 끔
    assert s.n == 2 and len(b["itinerary"]["anchors"]) == 2
    assert "QUOTE_NOT_FOUND" not in codes(b)


def test_default_zero_anchors_second_also_zero_keeps_first_no_cache(env):
    go, cache, key = env
    s = Seq([ZERO, ZERO])
    b = go(s)
    assert s.n == 2 and len(b["itinerary"]["anchors"]) == 0
    assert "QUOTE_NOT_FOUND" in codes(b) and cache.get(key) is None
    assert not list(cache.root.glob("*.json")) if cache.root.exists() else True
