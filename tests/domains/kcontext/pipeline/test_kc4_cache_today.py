"""T405 — 캐시 키와 해석이 같은 today 를 쓴다 · 잘못된 trip · LLM_BACKEND* · 캐시 v5."""

import json
from datetime import date

from domains.kcontext.pipeline import __main__ as cli
from domains.kcontext.pipeline import run as run_mod
from domains.kcontext.schedule import ScheduleCache, key_for
from domains.kcontext.schedule import cache as cache_mod

TEXT = "10/15 10시에 ○○궁"
A, B = date(2026, 10, 10), date(2026, 10, 11)


def test_invalid_trip_keyed_by_today(tmp_path):
    bad = ("2026-10-20", "2026-10-15")  # from > to
    assert key_for(TEXT, bad, root=tmp_path, today=A) != key_for(TEXT, bad, root=tmp_path, today=B)
    assert key_for(TEXT, bad, root=tmp_path, today=A) != key_for(TEXT, None, root=tmp_path, today=B)
    assert key_for(TEXT, ("x", "y"), root=tmp_path, today=A) != key_for(TEXT, ("x", "y"), root=tmp_path, today=B)  # fmt: skip
    ok = ("2026-10-15", "2026-10-16")
    assert key_for(TEXT, ok, root=tmp_path, today=A) == key_for(TEXT, ok, root=tmp_path, today=B)
    assert key_for(TEXT, bad, root=tmp_path, today=A) != key_for(TEXT, ok, root=tmp_path, today=A)


def test_llm_backend_in_key(tmp_path):
    base = key_for(TEXT, None, root=tmp_path, today=A, env={})
    assert key_for(TEXT, None, root=tmp_path, today=A, env={"LLM_BACKEND": "api"}) != base
    assert key_for(TEXT, None, root=tmp_path, today=A, env={"LLM_BACKEND": "local"}) != key_for(
        TEXT, None, root=tmp_path, today=A, env={"LLM_BACKEND": "api"})
    assert key_for(TEXT, None, root=tmp_path, today=A, env={"LLM_BACKEND_X": "a"}) != base
    assert key_for(TEXT, None, root=tmp_path, today=A, env={"OTHER": "a"}) == base


def test_llm_backend_default_env_is_os_environ(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    a = key_for(TEXT, None, root=tmp_path, today=A)
    monkeypatch.setenv("LLM_BACKEND", "local")
    assert key_for(TEXT, None, root=tmp_path, today=A) != a


def test_v4_cache_ignored(tmp_path):
    c = ScheduleCache(tmp_path)
    k = key_for(TEXT, None, root=tmp_path, today=A)
    body = {"v": 4, "created_at": "x", "meta": {}, "result": {"anchors": [], "free_slots": [], "problems": []}}  # fmt: skip
    (tmp_path / f"{k}.json").write_text(json.dumps(body), encoding="utf-8")
    assert c.get(k) is None
    c.put(k, body["result"], {})
    assert c.get(k) is not None and cache_mod._VERSION == 5


def test_main_passes_same_today_to_key_and_pipeline(tmp_path, monkeypatch):
    """자정 경계: kst_today 가 호출마다 다른 날을 돌려줘도 한 번만 구해 둘에 같이 넘긴다."""
    days = iter([A, B, B, B])
    monkeypatch.setattr(cli, "kst_today", lambda: next(days))
    monkeypatch.setenv("KC_SCHEDULE_CACHE", "on")
    monkeypatch.setenv("KC_VAR_DIR", str(tmp_path / "var"))
    seen = {}

    def fake_key(text, trip, **kw):
        seen["key_today"] = kw.get("today")
        return "0" * 64

    def fake_run(text, **kw):
        seen["run_today"] = kw.get("today")
        return {"schedule": {}, "cards": [], "problems": []}

    monkeypatch.setattr(cli, "key_for", fake_key)
    monkeypatch.setattr(cli, "run_story_pipeline", fake_run)
    monkeypatch.setattr(cli, "write_bundle", lambda *a, **k: None)
    monkeypatch.setattr(cli, "summarize", lambda b: {"ok": True})
    monkeypatch.setattr(cli, "make_lazy_complete", lambda f: (lambda s, u: ""))
    (tmp_path / "t.txt").write_text(TEXT, encoding="utf-8")
    (tmp_path / "i.db").write_bytes(b"")
    rc = cli.main(["--text-file", str(tmp_path / "t.txt"), "--db", str(tmp_path / "i.db"),
                   "--out", str(tmp_path / "out")])
    assert rc == 0
    assert seen["key_today"] == seen["run_today"] == A


def test_run_pipeline_forwards_today(monkeypatch):
    got = {}

    def fake_uwm(text, **kw):
        got["today"] = kw.get("today")
        raise RuntimeError("stop")

    monkeypatch.setattr(run_mod, "understand_with_meta", fake_uwm)
    try:
        run_mod.run_story_pipeline(TEXT, complete=lambda s, u: "", db=":memory:", trip=None,
                                   today=A)
    except RuntimeError:
        pass
    assert got["today"] == A
