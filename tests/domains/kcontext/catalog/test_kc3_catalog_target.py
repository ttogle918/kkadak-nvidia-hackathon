"""T319 — 카탈로그 대상 지역: 하나·여럿·오류·합성 행 판정·웹 레코드 거르기."""

from types import SimpleNamespace

import pytest

from domains.kcontext.catalog import web_events
from domains.kcontext.catalog.seoul import observation_from_row
from domains.kcontext.catalog.target import ENV, region_ids, target_region
from domains.kcontext.regions import load_regions

ALL = load_regions()
IDS = ["jung", "jongno", "mapo", "gangnam"]


def test_single_returns_the_loaded_region():
    assert target_region("jung") == ALL["jung"]
    assert region_ids(ALL["jung"]) == ("jung",)


def test_default_comes_from_env_then_fallback(monkeypatch):
    monkeypatch.delenv(ENV, raising=False)
    assert target_region().id == "jung"
    monkeypatch.setenv(ENV, "mapo")
    assert target_region().id == "mapo"


def test_multiple_merges_without_touching_loaded_regions():
    r = target_region(",".join(reversed(IDS)))
    assert r.id == "+".join(sorted(IDS)) and region_ids(r) == tuple(sorted(IDS))
    assert r.bbox is None and r.center is None and r.sillok_keywords == ()
    for i in IDS:
        assert set(ALL[i].gu) <= set(r.gu)
        assert set(ALL[i].keywords) <= set(r.keywords)
        assert ALL[i].name["ko"] in r.name["ko"].split("·")
    assert len(set(r.gu)) == len(r.gu)
    assert r.id not in load_regions() and r.id not in ALL


def test_duplicates_and_spaces_collapse():
    assert target_region(" jung , jung ") == ALL["jung"]


@pytest.mark.parametrize("spec", ["", "  ", "nowhere", "jung,nowhere", "jung,,mapo", ","])
def test_bad_spec_raises(spec):
    with pytest.raises(ValueError):
        target_region(spec)


def _row(gu):
    return {"CODENAME": "콘서트", "GUNAME": gu, "TITLE": "○○ 음악회 (합성)", "PLACE": "○○ 홀",
            "STRTDATE": "2026-10-16 00:00:00.0", "END_DATE": "2026-10-16 00:00:00.0",
            "DATE": "2026-10-16~2026-10-16", "ORG_LINK": "https://example.invalid/1",
            "HMPG_ADDR": "https://culture.seoul.go.kr/view.do?cultcode=1&menuNo=1"}


def test_synthetic_seoul_rows_judged_by_gu_against_merged_region():
    merged = target_region(",".join(IDS))
    for i in IDS:
        for gu in ALL[i].gu:
            o = observation_from_row(_row(gu), region=merged, collected_at="2026-10-07")
            assert o.venue.in_target == "yes", gu
    other = observation_from_row(_row("○○구"), region=merged, collected_at="2026-10-07")
    assert other.venue.in_target == "no"
    one = observation_from_row(_row(ALL["mapo"].gu[0]), region=ALL["jung"], collected_at="2026-10-07")
    assert one.venue.in_target == "no"


def test_web_records_filtered_by_covered_region_ids(monkeypatch):
    monkeypatch.setattr(web_events, "observation_from_record", lambda r, **kw: r.region)
    monkeypatch.setattr(web_events, "load_places", lambda: None)
    recs = [SimpleNamespace(region=i) for i in [*IDS, "elsewhere", None]]
    merged = target_region("jung,mapo")
    assert web_events.observations_from_records(recs, region=merged) == ["jung", "mapo"]
    assert web_events.observations_from_records(recs, region=ALL["jung"]) == ["jung"]
