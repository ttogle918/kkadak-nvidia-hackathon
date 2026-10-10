"""T320 — 검색 수집 출처가 지역별로 갈린다(web_source 키, 출처별 JSONL, 합친 Region 거르기)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from domains.kcontext.catalog import web_events
from domains.kcontext.catalog.sources import SourceError, load_sources, make_fetcher
from domains.kcontext.catalog.target import target_region
from domains.kcontext.contract.records import EventRecord, event_from_dict
from domains.kcontext.ingest.events.web import load_web_source
from domains.kcontext.regions import load_regions

NOW = datetime(2026, 10, 10, tzinfo=UTC)
WEB = {s["id"]: s["web_source"] for s in load_sources() if "web_source" in s}
GANGNAM_ID = next(k for k, v in WEB.items() if load_web_source(v)["region"] == "gangnam")
OTHER_ID = next(k for k in WEB if k != GANGNAM_ID)
REGIONS = load_regions()


_SRC = json.loads((Path(__file__).resolve().parents[4] / "domains" / "kcontext" / "contract"
                  / "examples" / "source.json").read_text(encoding="utf-8"))


def _rec(region: str, n: int, place: str) -> dict:
    return {
        "id": f"web:{region}:{n}", "region": region, "title": f"○○ 합성 행사 {n}",
        "category": "festival", "start_date": "2026-10-20", "end_date": "2026-10-21",
        "start_time": None, "end_time": None, "place_name": place, "lat": None, "lng": None,
        "geometry_type": "approx", "radius_m": 150, "status": "unknown", "outdoor": None,
        "description": "", "source": _SRC, "fetched_from": "web", "synthetic": False,
    }


def _write(path: Path, rows: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return path


def _records(rows: list[dict]) -> list[EventRecord]:
    return [event_from_dict(r) for r in rows]


def test_registry_declares_web_source_for_each_search_entry():
    by = {s["id"]: s for s in load_sources()}
    gs = by[GANGNAM_ID]
    ws = load_web_source(gs["web_source"])
    assert gs["method"] == "search" and gs["status"] == "partial"
    assert gs["env_keys"] == ["TAVILY_SEARCH_KEY", "TAVILY_API_KEY"]
    assert gs["url"] == ws["allow_url_prefixes"][0]
    assert ws["status"] == "confirmed"
    assert by[OTHER_ID]["web_source"] != gs["web_source"]


def test_default_events_file_per_source_and_legacy(tmp_path, monkeypatch):
    monkeypatch.setattr(web_events, "var_dir", lambda: tmp_path)
    d = tmp_path / "data" / "events"
    d.mkdir(parents=True)
    assert web_events.default_events_file() == d / "web.jsonl"
    assert web_events.default_events_file("x") == d / "web.x.jsonl"  # 아무 파일도 없으면 새 이름
    (d / "web.jsonl").write_text("", encoding="utf-8")
    assert web_events.default_events_file("x") == d / "web.jsonl"  # 예전 파일 호환
    (d / "web.x.jsonl").write_text("", encoding="utf-8")
    assert web_events.default_events_file("x") == d / "web.x.jsonl"


def test_gangnam_records_become_observations_with_own_source_id(tmp_path):
    g = "gangnam"
    merged = target_region(",".join(REGIONS))
    path = _write(tmp_path / "w.jsonl", [
        _rec(g, 1, "○○ 합성 장소"),
        _rec(next(i for i in REGIONS if i != g), 2, "○○ 합성 장소"),  # 다른 지역 레코드
        _rec("elsewhere", 3, "○○ 합성 장소"),
    ])
    fetch = make_fetcher(GANGNAM_ID, region=merged, now=NOW, web_events=path)
    obs = fetch()
    assert [o.obs_id for o in obs] == [f"web:{g}:1"]
    o = obs[0]
    assert o.evidence.source_id == GANGNAM_ID and o.evidence.kind == "ai_extracted"
    assert "미확인" in o.evidence.source_name
    assert o.venue.in_target != "yes"  # 장소가 구로 확인되지 않으면 대상 지역 확정이 아니다


def test_merged_region_filter_drops_uncovered_region_records():
    recs = _records([_rec("gangnam", 1, "○○"), _rec("elsewhere", 2, "○○")])
    one = web_events.observations_from_records(recs, region=REGIONS["gangnam"], source_id="s")
    assert [o.obs_id for o in one] == ["web:gangnam:1"]
    other = next(r for i, r in REGIONS.items() if i != "gangnam")
    assert web_events.observations_from_records(recs, region=other, source_id="s") == []


def test_unconfirmed_or_missing_web_source_is_source_error(tmp_path, monkeypatch):
    f = _write(tmp_path / "w.jsonl", [])
    src = [{"id": "t_site", "web_source": "nope"}]
    with pytest.raises(SourceError):
        make_fetcher("t_site", region=REGIONS["gangnam"], now=NOW, web_events=f, sources=src)
    from domains.kcontext.catalog import sources as mod

    real = load_web_source(WEB[GANGNAM_ID])
    monkeypatch.setattr(mod, "load_web_source", lambda wid: {**real, "status": "unconfirmed"})
    with pytest.raises(SourceError, match="confirmed"):
        make_fetcher(GANGNAM_ID, region=REGIONS["gangnam"], now=NOW, web_events=f)


def test_missing_events_file_is_source_error(tmp_path):
    with pytest.raises(SourceError):
        make_fetcher(GANGNAM_ID, region=REGIONS["gangnam"], now=NOW, web_events=tmp_path / "none.jsonl")
