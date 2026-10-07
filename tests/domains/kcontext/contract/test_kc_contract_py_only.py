"""Python 전용 규칙 — JS schema.js 가 검사하지 않는 것(예제 파일이 아니라 dict 로 만든다)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from domains.kcontext.contract import REJECT_REASONS, ROUTE_BADGES, validate_card, validate_route

EX = Path(__file__).resolve().parents[4] / "domains" / "kcontext" / "contract" / "examples"


def ex(name: str) -> dict:
    return copy.deepcopy(json.loads((EX / name).read_text(encoding="utf-8")))


def has(problems: list[str], part: str) -> bool:
    return any(part in p for p in problems)


def test_coord_range() -> None:
    c = ex("card_story.json")
    c["geometry"]["coords"] = [[91.0, 127.0], [37.0, 127.0]]
    assert has(validate_card(c), "coords[0]: [lat,lng] 범위 밖")
    c["geometry"]["coords"] = [[37.0, 181.0], [37.0, 127.0]]
    assert has(validate_card(c), "coords[0]")


def test_swapped_lat_lng_is_caught_by_range() -> None:
    c = ex("card_story.json")
    c["geometry"]["coords"] = [[127.0, 37.0], [127.001, 37.001]]  # [lng, lat] 로 뒤바뀜
    p = validate_card(c)
    assert has(p, "coords[0]") and has(p, "coords[1]")


def test_schematic_space_skips_range_but_unknown_space_fails() -> None:
    c = ex("card_story.json")
    c["geometry"]["space"] = "schematic"
    c["geometry"]["coords"] = [[90, 700], [210, 100]]
    assert validate_card(c) == []
    c["geometry"]["space"] = "mercator"
    assert has(validate_card(c), "geometry.space")


def test_space_absent_means_geo() -> None:
    c = ex("card_story.json")
    del c["geometry"]["space"]
    assert validate_card(c) == []
    c["geometry"]["coords"] = [[300, 100], [300, 170]]
    assert has(validate_card(c), "범위 밖")


def test_rejected_reason_must_be_known() -> None:
    c = ex("card_story.json")
    c["rejected"] = [{"claim": "○○", "reason": "마음에 안 듦"}]
    assert has(validate_card(c), "rejected[0].reason")
    for reason in REJECT_REASONS:
        c["rejected"] = [{"claim": "○○", "reason": reason}]
        assert validate_card(c) == [], reason
    c["rejected"] = [{"reason": "중복"}]
    assert has(validate_card(c), "rejected[0].claim")


def test_route_badges_delta_and_estimated() -> None:
    r = ex("route.json")
    r["badges"] = ["최고"]
    assert has(validate_route(r), "badges")
    for b in ROUTE_BADGES:
        r["badges"] = [b]
        assert validate_route(r) == []
    r["delta_min"] = -1
    assert has(validate_route(r), "delta_min")
    r = ex("route.json")
    r["estimated"] = "yes"
    assert has(validate_route(r), "estimated")
    r["estimated"] = 1
    assert has(validate_route(r), "estimated")
    del r["estimated"]
    assert validate_route(r) == []


def test_facts_ref_range() -> None:
    c = ex("card_story.json")
    n = len(c["sources"])
    for bad in (0, n + 1, True, 1.5, "1"):
        c["facts"][0]["ref"] = bad
        assert has(validate_card(c), "facts[0].ref"), bad
    c["facts"][0]["ref"] = n
    assert validate_card(c) == []


def test_approx_radius() -> None:
    c = ex("card_now.json")
    for bad in (0, -5, None, True):
        c["geometry"]["radius_m"] = bad
        assert has(validate_card(c), "radius_m"), bad
    del c["geometry"]["radius_m"]
    assert has(validate_card(c), "radius_m")
    c["geometry"]["radius_m"] = 150
    assert validate_card(c) == []


def test_narration_null_allowed() -> None:
    c = ex("card_story.json")
    c["narration"] = None
    assert validate_card(c) == []
    del c["narration"]
    assert validate_card(c) == []
    c["narration"] = {"ko": "가"}
    assert has(validate_card(c), "narration")
    c["narration"] = ""
    assert has(validate_card(c), "narration")


def test_extension_fields_optional_and_checked() -> None:
    c = ex("card_story.json")
    for k in ("era", "facts", "alternatives", "checks", "poster", "only", "warning", "kind_label"):
        c.pop(k, None)
    assert validate_card(c) == []
    c["checks"] = [{"level": "great", "text": "x"}]
    assert has(validate_card(c), "checks[0]")
    c = ex("card_story.json")
    c["alternatives"] = [{"label": "x"}]
    assert has(validate_card(c), "alternatives[0]")
    c = ex("card_story.json")
    c["warning"] = {"title": "x"}
    assert has(validate_card(c), "warning")
    c = ex("card_story.json")
    c["sources"][0]["bib"] = 5
    assert has(validate_card(c), "bib")


def test_route_segment_coords_optional() -> None:
    r = ex("route.json")
    for s in r["segments"]:
        s.pop("coords", None)
    assert validate_route(r) == []
