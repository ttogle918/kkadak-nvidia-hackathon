"""T433 검색 색인 — 색인 경로와 전체 경로의 결과가 같고(순서까지), 후보만 변환하며, 무효 색인은 전체 경로로 폴백한다. 값은 합성."""

import json
import logging
from datetime import datetime, timedelta

import pytest
from kc_catalog_helpers import NOW, obs, session

from domains.kcontext.catalog import api
from domains.kcontext.catalog import store as store_mod
from domains.kcontext.catalog.merge import build_entries
from domains.kcontext.catalog.query import (
    REASON_CANCELLED,
    REASON_ENDED,
    REASON_NOT_IN_TARGET,
    REASON_TARGET_UNKNOWN,
)
from domains.kcontext.catalog.store import SEARCH_INDEX, CatalogStore

BUILT = "2026-10-07T12:00"
TRIP = {"from": "2026-10-15", "to": "2026-10-18"}


def _obs():
    return [
        obs("s:1", title="○○ 진행", venue_name="○○ 홀"),
        obs("s:2", title="○○ 바깥", in_target="no", venue_name="△△"),
        obs("s:3", title="○○ 미확인", in_target="unknown", venue_name="□□"),
        obs("s:4", title="○○ 취소", lifecycle="cancelled", venue_name="a"),
        obs("s:5", title="○○ 종료", start="2026-09-01", end="2026-09-02", venue_name="b"),
        obs("s:6", title="○○ 종료일 없음 오래됨", start="2025-01-01", end=None, venue_name="c"),
        obs("s:7", title="○○ 종료일 없음 최근", start="2026-06-01", end=None, venue_name="d"),
        obs("s:8", title="○○ 연기", lifecycle="postponed", venue_name="e"),
        obs("s:9", title="○○ 데모", demo=True, venue_name="f"),
        obs("s:10", title="○○ 데모 바깥", demo=True, in_target="no", venue_name="g"),
        obs("s:11", title="○○ 회차", sessions=(session("2026-10-16"),), venue_name="h"),
        obs("s:12", title="○○ 날짜 밖", start="2026-11-20", end="2026-11-21", venue_name="i"),
    ]


@pytest.fixture
def store(tmp_path):
    st = CatalogStore(tmp_path / "cat")
    st.save_entries(build_entries(_obs(), now=NOW), BUILT)
    return st


def _full(store, args, now):
    raw = store.read_entries_raw()
    from domains.kcontext.catalog.model import entry_from_dict
    from domains.kcontext.catalog.query import search_events

    entries = [entry_from_dict(e) for e in raw["entries"]]
    return search_events(entries, args, now=now, coverage={"entries_built_at": raw["built_at"], "sources": []})


def _indexed(store, args, now):
    idx = store.load_search_index(now)
    assert idx is not None
    from domains.kcontext.catalog.model import entry_from_dict
    from domains.kcontext.catalog.query import search_events

    return search_events(
        [entry_from_dict(c["entry"]) for c in idx["candidates"]], args, now=now,
        coverage={"entries_built_at": idx["built_at"], "sources": []},
        positions=[c["pos"] for c in idx["candidates"]],
        pre_excluded=[(p["pos"], {"id": p["id"], "title": p["title"], "reason": p["reason"]})
                      for p in idx["pre_excluded"]])


@pytest.mark.parametrize("include_demo", [False, True])
@pytest.mark.parametrize("extra", [{}, {"interests": ["회차"], "require_interest": True},
                                   {"trip": {"from": "x", "to": "y"}}])
def test_indexed_result_equals_full_result(store, include_demo, extra):
    args = {"trip": TRIP, "include_demo": include_demo, **extra}
    now = NOW + timedelta(hours=3)
    a, b = _full(store, args, now), _indexed(store, args, now)
    assert a == b
    assert json.dumps(a["excluded"], ensure_ascii=False) == json.dumps(b["excluded"], ensure_ascii=False)
    assert a["counts"] == b["counts"] and a["coverage"] == b["coverage"]


def test_index_splits_pre_excluded_with_shared_reasons(store):
    idx = store.load_search_index(NOW)
    reasons = {p["id"]: p["reason"] for p in idx["pre_excluded"]}
    assert set(reasons.values()) == {REASON_NOT_IN_TARGET, REASON_TARGET_UNKNOWN, REASON_CANCELLED, REASON_ENDED}
    titles = {c["entry"]["title"] for c in idx["candidates"]}
    assert "○○ 데모" in titles and "○○ 데모 바깥" in titles  # demo 는 항상 후보
    assert idx["total"] == len(idx["candidates"]) + len(idx["pre_excluded"])
    assert [p["pos"] for p in idx["pre_excluded"]] == sorted(p["pos"] for p in idx["pre_excluded"])


def test_only_candidates_are_converted(store, monkeypatch):
    calls = []
    real = api.entry_from_dict
    monkeypatch.setattr(api, "entry_from_dict", lambda d: (calls.append(1), real(d))[1])
    idx = store.load_search_index(NOW)
    res = api._search({"trip": TRIP}, store, [], NOW, provider=None)
    assert len(calls) == len(idx["candidates"]) < idx["total"]
    assert res["counts"]["excluded"] > len(idx["candidates"]) - res["counts"]["events"] - 1
    assert res["catalog_empty"] is False


def test_api_search_same_with_and_without_index(store):
    a = api._search({"trip": TRIP, "include_demo": True}, store, [], NOW, provider=None)
    (store.dir / SEARCH_INDEX).unlink()
    b = api._search({"trip": TRIP, "include_demo": True}, store, [], NOW, provider=None)
    assert a == b


def _fallback(store, caplog, now=NOW):
    with caplog.at_level(logging.WARNING, logger="kc.catalog.index"):
        assert store.load_search_index(now) is None
    assert any("전체 경로" in r.message for r in caplog.records)
    # 폴백이어도 검색 결과는 정상
    return api._search({"trip": TRIP}, store, [], now, provider=None)


def test_fallback_missing_index(store, caplog):
    (store.dir / SEARCH_INDEX).unlink()
    assert _fallback(store, caplog)["counts"]["events"] > 0


def test_fallback_schema_mismatch(store, caplog):
    p = store.dir / SEARCH_INDEX
    d = json.loads(p.read_text(encoding="utf-8"))
    d["schema"] = "kc-search-index/v0"
    p.write_text(json.dumps(d), encoding="utf-8")
    _fallback(store, caplog)


def test_fallback_built_at_mismatch(store, caplog):
    store._write_json("entries.json", {**store.read_entries_raw(), "built_at": "2026-10-08T00:00"})
    _fallback(store, caplog)


def test_fallback_now_before_indexed_at(store, caplog):
    _fallback(store, caplog, now=datetime.fromisoformat(BUILT) - timedelta(days=1))


def test_fallback_corrupt_index(store, caplog):
    (store.dir / SEARCH_INDEX).write_text("{깨짐", encoding="utf-8")
    _fallback(store, caplog)


def test_entries_built_at_does_not_reparse_entries(store, monkeypatch):
    monkeypatch.setattr(store_mod.CatalogStore, "_read_json",
                        lambda *a, **k: pytest.fail("entries.json 을 다시 파싱했다"))
    assert store.entries_built_at() == BUILT


def test_reindex_rebuilds_and_reports(store):
    (store.dir / SEARCH_INDEX).unlink()
    info = store.reindex(now=NOW)
    assert info["total"] == 12 and info["bytes"] > 0 and store.load_search_index(NOW) is not None


def test_broken_index_element_falls_back_to_full_path(tmp_path, caplog):
    # 리뷰 경고 5: 최상위 형식은 맞고 원소가 깨진 색인도 조용히 전체 경로로 간다(bad_request 가 아니라).
    import json as _json

    from domains.kcontext.catalog import api as api_mod
    from domains.kcontext.catalog.store import SEARCH_INDEX, CatalogStore

    store = CatalogStore(tmp_path)
    store.save_entries([], built_at="2026-10-01T00:00")
    p = tmp_path / SEARCH_INDEX
    idx = _json.loads(p.read_text(encoding="utf-8"))
    idx["candidates"] = [{"broken": True}]
    p.write_text(_json.dumps(idx), encoding="utf-8")
    from datetime import datetime, timedelta, timezone

    now = datetime(2026, 10, 10, tzinfo=timezone(timedelta(hours=9)))
    with caplog.at_level("WARNING", logger="kc.catalog.index"):
        res = api_mod.handle("search", {"trip": {"from": "2026-10-15", "to": "2026-10-15"}},
                             store=store, now=now, actor=None, env={})
    assert res["catalog_empty"] is True and res["events"] == []
    assert any("전체 경로" in r.getMessage() for r in caplog.records)
