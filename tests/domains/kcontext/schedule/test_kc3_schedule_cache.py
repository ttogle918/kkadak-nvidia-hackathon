"""일정 이해 결과 캐시(D15 ④) — 저장 내용·키·손상 처리."""

import json

import pytest

from domains.kcontext.schedule import ScheduleCache, key_for
from domains.kcontext.schedule.cache import cache_enabled

RES = {"anchors": [{"type": "visit", "name": "○○궁"}], "free_slots": [], "problems": []}
META = {"source": "llm", "attempts": 1, "prompt_sha": "abc", "model": "m"}
TEXT = "SECRET-TEXT-○○ 10/15 ○○궁"


def test_put_get_roundtrip_without_input_text(tmp_path):
    c = ScheduleCache(tmp_path / "cache")
    k = key_for(TEXT, ("2026-10-15", "2026-10-16"))
    assert c.get(k) is None
    c.put(k, RES, META)
    got = c.get(k)
    assert got["result"] == RES and got["meta"] == META and got["created_at"].endswith("Z")
    blob = (tmp_path / "cache" / f"{k}.json").read_text(encoding="utf-8")
    assert "SECRET-TEXT" not in blob and not list((tmp_path / "cache").glob(".*tmp"))


def test_key_changes_with_inputs(tmp_path, monkeypatch):
    monkeypatch.delenv("SCHEDULE_MODEL", raising=False)
    monkeypatch.delenv("CHAT_MODEL", raising=False)
    trip = ("2026-10-15", "2026-10-16")
    base = key_for(TEXT, trip, root=tmp_path)
    assert base == key_for(TEXT, trip, root=tmp_path) and len(base) == 64
    assert key_for(TEXT + "x", trip, root=tmp_path) != base
    assert key_for(TEXT, None, root=tmp_path) != base
    assert key_for(TEXT, ("2026-10-15", "2026-10-17"), root=tmp_path) != base
    monkeypatch.setenv("SCHEDULE_MODEL", "other")
    assert key_for(TEXT, trip, root=tmp_path) != base
    monkeypatch.delenv("SCHEDULE_MODEL")
    (tmp_path / "deploy").mkdir()
    (tmp_path / "deploy" / "llm.chat.yaml").write_text("a: 1", encoding="utf-8")
    assert key_for(TEXT, trip, root=tmp_path) != base
    # NFKC 정규화: 전각 숫자는 같은 키
    assert key_for("１０/１５", trip, root=tmp_path) == key_for("10/15", trip, root=tmp_path)


@pytest.mark.parametrize("junk", ["not json", "[]", '{"v": 9}',
                                  json.dumps({"v": 1, "result": {}, "meta": {}, "created_at": "x"})])
def test_corrupt_entry_is_a_miss_and_overwritable(tmp_path, junk):
    c = ScheduleCache(tmp_path)
    k = key_for(TEXT, None)
    (tmp_path / f"{k}.json").write_text(junk, encoding="utf-8")
    assert c.get(k) is None
    c.put(k, RES, META)
    assert c.get(k) is not None


def test_bad_key_rejected(tmp_path):
    c = ScheduleCache(tmp_path)
    assert c.get("../etc/passwd") is None
    with pytest.raises(ValueError):
        c.put("../etc/passwd", RES, META)


def test_cache_env_switch():
    assert cache_enabled({}) and cache_enabled({"KC_SCHEDULE_CACHE": "on"})
    assert not cache_enabled({"KC_SCHEDULE_CACHE": "off"})


def test_key_includes_today_only_without_trip(tmp_path):
    from datetime import date
    a, b = date(2026, 10, 10), date(2026, 10, 11)
    assert key_for(TEXT, None, root=tmp_path, today=a) != key_for(TEXT, None, root=tmp_path, today=b)
    trip = ("2026-10-15", "2026-10-16")
    assert key_for(TEXT, trip, root=tmp_path, today=a) == key_for(TEXT, trip, root=tmp_path, today=b)
