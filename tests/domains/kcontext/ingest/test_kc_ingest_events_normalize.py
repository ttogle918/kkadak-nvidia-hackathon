import json
from pathlib import Path

import pytest

from domains.kcontext.ingest.events.normalize import (
    FieldMapMissing,
    load_field_map,
    normalize,
    pick_region,
)
from domains.kcontext.regions import Region

REGIONS = {
    "ra": Region("ra", {"ko": "가", "en": "A"}, ("가구",), (37.0, 127.0, 37.1, 127.1),
                 (37.05, 127.05), ("가구",), ()),
    "rb": Region("rb", {"ko": "나", "en": "B"}, ("나구",), None, None, ("나구", "나동"), ()),
}
FM = {
    "provider": "tourapi",
    "items_path": ["body", "items"],
    "fields": {"id": "○_id", "title": "○_title", "start_date": "○_start", "end_date": "○_end",
               "place": "○_place", "address": "○_addr", "lat": "○_lat", "lng": "○_lng",
               "url": "○_url", "updated": "○_upd", "category": "○_cat", "status": "○_st",
               "description": "[확인 필요]"},
    "date_format": "%Y%m%d",
    "coord_order": "lat_lng",
    "category_map": {"축제": "festival"},
    "status_map": {"취소": "cancelled"},
}


def item(**over):
    base = {"○_id": "1", "○_title": "○○ 축제", "○_start": "20261015", "○_end": "20261018",
            "○_place": "○○ 광장", "○_addr": "나구 ○○로", "○_cat": "축제", "○_st": "진행",
            "○_upd": "20261001", "○_url": "https://example.invalid/1"}
    base.update(over)
    return base


def norm(items, fm=FM, raw_wrap=True):
    raw = {"body": {"items": items}} if raw_wrap else items
    return normalize(raw, provider="tourapi", field_map=fm, collected_at="2026-10-07",
                     regions=REGIONS)


def test_basic_record():
    res = norm([item()])
    assert res.problems == () and res.skipped_out_of_region == 0
    r = res.records[0]
    assert (r.id, r.region, r.title, r.category, r.status) == (
        "tourapi:1", "rb", "○○ 축제", "festival", "unknown")
    assert (r.start_date, r.end_date, r.place_name) == ("2026-10-15", "2026-10-18", "○○ 광장")
    assert r.fetched_from == "tourapi" and r.geometry_type == "point" and r.lat is None
    s = r.source
    assert s.tier == "B" and s.name == "한국관광공사 TourAPI" and s.id == "tourapi:1"
    assert s.locator == "2026-10-01 갱신" and s.published == "2026-10-01"
    assert s.url == "https://example.invalid/1" and s.collected_at == "2026-10-07"
    assert s.quote == "○○ 축제 / 2026-10-15–2026-10-18 / ○○ 광장"


def test_no_update_date_and_no_url():
    r = norm([item(**{"○_upd": None, "○_url": None})]).records[0]
    assert r.source.locator == "2026-10-07 수집 · 갱신일 미제공"
    assert r.source.published is None and r.source.url == ""


def test_seoul_source_name():
    res = normalize({"body": {"items": [item()]}}, provider="seoul", field_map=FM,
                    collected_at="2026-10-07", regions=REGIONS)
    assert res.records[0].source.name == "서울 열린데이터광장 문화행사"
    assert res.records[0].fetched_from == "seoul"


def test_category_and_status_maps_and_unknown_values():
    r = norm([item(**{"○_cat": "기타", "○_st": "취소"})]).records[0]
    assert r.category == "other" and r.status == "cancelled"
    fm = {**FM}
    fm.pop("category_map")
    fm.pop("status_map")
    r = norm([item()], fm).records[0]
    assert r.category == "other" and r.status == "unknown"


def test_placeholder_and_blank_field_maps_are_ignored():
    fm = {**FM, "fields": {**FM["fields"], "place": "[확인 필요]", "address": "",
                           "end_date": "[확인 필요]"}}
    r = norm([item(**{"○_title": "○○ 나동 축제"})], fm).records[0]
    assert r.place_name == "" and r.end_date is None and r.region == "rb"  # 제목에서 지역


def test_region_by_coordinates_then_text():
    inside = norm([item(**{"○_lat": "37.05", "○_lng": "127.05", "○_addr": "알 수 없음"})])
    assert inside.records[0].region == "ra" and inside.records[0].lat == 37.05
    outside_coords_text_hit = norm([item(**{"○_lat": "10", "○_lng": "10"})])
    assert outside_coords_text_hit.records[0].region == "rb"
    nowhere = norm([item(**{"○_addr": "다구", "○_title": "○○ 축제"})])
    assert nowhere.records == () and nowhere.skipped_out_of_region == 1


def test_combined_coord_field_respects_order():
    fm = {**FM, "coord_order": "lng_lat", "fields": {**FM["fields"], "lat": "", "lng": "",
                                                      "coord": "○_xy"}}
    r = norm([item(**{"○_xy": "127.05, 37.05"})], fm).records[0]
    assert (r.lat, r.lng, r.region) == (37.05, 127.05, "ra")


def test_bad_values_become_problems_not_crashes():
    res = norm([item(**{"○_start": "2026/10/15"})])
    assert res.records[0].start_date is None and any("시작" in p for p in res.problems)
    res = norm([item(**{"○_lat": "95", "○_lng": "10"})])
    assert res.records[0].lat is None and any("좌표" in p for p in res.problems)
    res = norm([item(**{"○_lat": "abc", "○_lng": "10"})])
    assert res.records[0].lat is None
    res = norm([item(**{"○_start": "20261018", "○_end": "20261015"})])
    assert res.records[0].end_date is None and any("종료일" in p for p in res.problems)
    res = norm([item(**{"○_id": None}), "문자열", item(**{"○_title": None})])
    assert res.records == () and len(res.problems) == 3


def test_duplicate_ids_keep_the_later_one():
    res = norm([item(**{"○_title": "○○ 첫째"}), item(**{"○_title": "○○ 둘째"})])
    assert [r.title for r in res.records] == ["○○ 둘째"]
    assert any("중복" in p for p in res.problems)


def test_items_path_edge_cases():
    assert norm([]).records == () and norm([]).problems == ()
    res = normalize({"body": []}, provider="tourapi", field_map=FM, collected_at="2026-10-07",
                    regions=REGIONS)
    assert res.records == () and len(res.problems) == 1  # 중간이 list
    res = normalize({"x": 1}, provider="tourapi", field_map=FM, collected_at="2026-10-07",
                    regions=REGIONS)
    assert res.records == () and "찾지 못했다" in res.problems[0]
    res = normalize({"body": {"items": 3}}, provider="tourapi", field_map=FM,
                    collected_at="2026-10-07", regions=REGIONS)
    assert res.records == () and res.problems
    res = normalize({"body": {"items": item()}}, provider="tourapi", field_map=FM,
                    collected_at="2026-10-07", regions=REGIONS)
    assert len(res.records) == 1  # 항목 하나만 있는 응답


def test_json_string_input():
    raw = json.dumps({"body": {"items": [item()]}}, ensure_ascii=False)
    res = normalize(raw, provider="tourapi", field_map=FM, collected_at="2026-10-07",
                    regions=REGIONS)
    assert len(res.records) == 1
    res = normalize("not json", provider="tourapi", field_map=FM, collected_at="2026-10-07",
                    regions=REGIONS)
    assert res.records == () and res.problems


def test_load_field_map(tmp_path: Path):
    with pytest.raises(FieldMapMissing):
        load_field_map("tourapi", tmp_path)
    (tmp_path / "seoul_cultural.json").write_text(json.dumps(FM), encoding="utf-8")
    assert load_field_map("seoul", tmp_path)["provider"] == "tourapi"
    assert issubclass(FieldMapMissing, FileNotFoundError)


def test_pick_region_prefers_coordinates():
    assert pick_region(37.05, 127.05, "나구", REGIONS) == "ra"
    assert pick_region(None, None, "나동 ○○", REGIONS) == "rb"
    assert pick_region(None, None, "없음", REGIONS) is None
