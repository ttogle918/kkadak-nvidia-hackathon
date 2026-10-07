"""내부 레코드(StoryRecord·EventRecord·Rejection·Blocked) 테스트."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

from domains.kcontext.contract import (
    EVENT_CATEGORIES,
    REJECT_REASONS,
    Blocked,
    ContractError,
    EventRecord,
    Rejection,
    SourceRef,
    StoryRecord,
    event_from_dict,
    story_from_dict,
)

CONTRACT = Path(__file__).resolve().parents[4] / "domains" / "kcontext" / "contract"
SRC = json.loads((CONTRACT / "examples" / "source.json").read_text(encoding="utf-8"))


def story() -> dict:
    return copy.deepcopy(
        {
            "id": "story_example_1",
            "region": "region_example",
            "title": {"ko": "○○ 길 (합성 예시)", "en": "○○ Road (synthetic example)"},
            "theme": "○○",
            "era": None,
            "geometry": {
                "type": "segment",
                "coords": [[37.0, 127.0], [37.001, 127.001]],
                "basis": "합성 예시 — 실제 위치 아님",
                "space": "geo",
            },
            "alignment": "approx",
            "claims": [
                {
                    "text": "○○ 기록에 나온다 (합성 예시)",
                    "evidence": [
                        {"source": SRC, "stance": "support", "claim_kind": "fact"},
                        {"source": SRC, "stance": "contradict", "says": "○○ (합성)"},
                    ],
                }
            ],
            "synthetic": True,
        }
    )


def event() -> dict:
    return copy.deepcopy(
        {
            "id": "event_example_1",
            "region": None,
            "title": "○○ 야장 (합성 예시)",
            "category": "night_market",
            "start_date": "2026-10-15",
            "end_date": "2026-10-18",
            "start_time": "19:30",
            "end_time": None,
            "place_name": "○○ 골목",
            "lat": 37.0,
            "lng": 127.0,
            "geometry_type": "approx",
            "radius_m": 150,
            "status": "scheduled",
            "outdoor": True,
            "description": "합성 예시",
            "source": SRC,
            "fetched_from": "fixture",
            "synthetic": True,
        }
    )


def test_source_ref_roundtrip() -> None:
    s = SourceRef.from_dict(SRC)
    assert s.tier == "S" and s.bib is not None
    assert s.to_dict() == SRC
    d = {k: v for k, v in SRC.items() if k != "bib"}
    assert SourceRef.from_dict(d).bib is None


def test_source_ref_rejects_bad_and_unknown() -> None:
    with pytest.raises(ContractError):
        SourceRef.from_dict({**SRC, "tier": "Z"})
    with pytest.raises(ContractError) as ei:
        SourceRef.from_dict({**SRC, "extra": 1})
    assert "모르는 키" in str(ei.value)


def test_story_roundtrip_is_json_serializable() -> None:
    d = story()
    rec = story_from_dict(d)
    assert isinstance(rec, StoryRecord)
    assert rec.claims[0].evidence[1].says == "○○ (합성)"
    assert rec.claims[0].evidence[0].claim_kind == "fact"
    out = rec.to_dict()
    json.dumps(out, ensure_ascii=False)
    assert out["claims"][0]["evidence"][0]["source"]["id"] == SRC["id"]
    again = story_from_dict(out)
    assert again == rec


def test_story_is_frozen_and_copies_input() -> None:
    d = story()
    rec = story_from_dict(d)
    with pytest.raises(AttributeError):
        rec.id = "x"  # type: ignore[misc]
    d["geometry"]["coords"].append([1.0, 1.0])
    assert len(rec.geometry["coords"]) == 2


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(extra=1),
        lambda d: d.pop("title"),
        lambda d: d.pop("era"),
        lambda d: d.update(alignment="maybe"),
        lambda d: d["geometry"].update(space="schematic"),
        lambda d: d["geometry"].update(coords=[[127.0, 37.0], [127.1, 37.1]]),
        lambda d: d["claims"][0]["evidence"][0].update(stance="neutral"),
        lambda d: d["claims"][0]["evidence"][0]["source"].pop("quote"),
        lambda d: d["claims"][0]["evidence"][0].update(claim_kind="rumor"),
        lambda d: d.update(claims="x"),
        lambda d: d.update(synthetic="yes"),
    ],
)
def test_story_from_dict_rejects(mutate) -> None:
    d = story()
    mutate(d)
    with pytest.raises(ContractError):
        story_from_dict(d)


def test_story_with_no_evidence_is_allowed_to_load() -> None:
    d = story()
    d["claims"][0]["evidence"] = []
    assert story_from_dict(d).claims[0].evidence == ()


def test_event_roundtrip() -> None:
    rec = event_from_dict(event())
    assert isinstance(rec, EventRecord) and rec.category in EVENT_CATEGORIES
    assert rec.source.id == SRC["id"]
    out = rec.to_dict()
    json.dumps(out, ensure_ascii=False)
    assert event_from_dict(out) == rec
    d = event()
    del d["synthetic"]
    assert event_from_dict(d).synthetic is False


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(extra=1),
        lambda d: d.pop("status"),
        lambda d: d.update(category="concert"),
        lambda d: d.update(start_date="2026/10/15"),
        lambda d: d.update(start_date="2026-10-19"),
        lambda d: d.update(start_time="7:30"),
        lambda d: d.update(lat=None),
        lambda d: d.update(lat=95.0),
        lambda d: d.update(radius_m=0),
        lambda d: d.update(radius_m=None),
        lambda d: d.update(geometry_type="segment"),
        lambda d: d.update(status="open"),
        lambda d: d.update(outdoor="yes"),
        lambda d: d.update(fetched_from="crawl"),
        lambda d: d["source"].update(tier="Z"),
    ],
)
def test_event_from_dict_rejects(mutate) -> None:
    d = event()
    mutate(d)
    with pytest.raises(ContractError):
        event_from_dict(d)


def test_event_without_coordinates_is_allowed() -> None:
    d = event()
    d.update(lat=None, lng=None, geometry_type="point", radius_m=None)
    assert event_from_dict(d).lat is None


def test_non_mapping_input() -> None:
    with pytest.raises(ContractError):
        story_from_dict([])  # type: ignore[arg-type]
    with pytest.raises(ContractError):
        event_from_dict(None)  # type: ignore[arg-type]


def test_rejection_reason_checked() -> None:
    for r in REJECT_REASONS:
        assert Rejection("t", "c", r, "d").reason == r
    with pytest.raises(ValueError):
        Rejection("t", "c", "모르는 값", "d")
    assert Rejection("t", "c", "중복", "d").to_dict() == {
        "target_id": "t", "claim": "c", "reason": "중복", "detail": "d",
    }  # fmt: skip


def test_blocked() -> None:
    b = Blocked("doc_1", "injection", ("r1", "r2"))
    assert b.to_dict() == {"source_id": "doc_1", "verdict": "injection", "rules": ["r1", "r2"]}
    with pytest.raises(ValueError):
        Blocked("doc_1", "bad", ())  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        Blocked("doc_1", "suspicious", ["r1"])  # type: ignore[arg-type]


def test_contract_package_has_no_region_literals_or_forbidden_imports() -> None:
    forbidden = ["종" + "로", "을지" + "로", "신" + "촌"]  # 지역 리터럴은 코드에 쓰지 않는다
    for p in CONTRACT.rglob("*"):
        if p.suffix not in {".py", ".json"}:
            continue
        text = p.read_text(encoding="utf-8")
        assert not any(w in text for w in forbidden), p
        if p.suffix == ".py":
            for m in re.finditer(r"^\s*(?:from|import)\s+(\S+)", text, re.MULTILINE):
                mod = m.group(1)
                assert not mod.startswith(("backend", "mcp_server", "core", "domains.kcontext.")), (
                    p,
                    mod,
                )


def test_event_fetched_from_web_is_allowed() -> None:
    d = event()
    d.update(fetched_from="web")
    assert event_from_dict(d).fetched_from == "web"
