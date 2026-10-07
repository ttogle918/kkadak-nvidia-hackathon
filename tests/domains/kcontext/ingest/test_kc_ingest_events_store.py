import json
from pathlib import Path

import pytest

from domains.kcontext.contract.errors import ContractError
from domains.kcontext.contract.records import event_from_dict
from domains.kcontext.index.store import LocalIndex
from domains.kcontext.ingest.events.store import read_jsonl, to_chunks, write_jsonl


def rec(**over):
    base = {
        "id": "e1", "region": "r", "title": "○○ 가을 야시장", "category": "night_market",
        "start_date": "2026-10-15", "end_date": "2026-10-18", "start_time": None,
        "end_time": None, "place_name": "○○ 골목", "lat": None, "lng": None,
        "geometry_type": "point", "radius_m": None, "status": "scheduled", "outdoor": None,
        "description": "합성 설명", "fetched_from": "manual", "synthetic": True,
        "source": {"id": "s1", "tier": "B", "name": "○○구청", "locator": "2026-10-01 게시",
                   "url": "", "published": "2026-10-01", "collected_at": "2026-10-07",
                   "quote": "○○ 가을 야시장 2026-10-15"},
    }
    base.update(over)
    return event_from_dict(base)


def test_jsonl_roundtrip_creates_parent(tmp_path: Path):
    path = tmp_path / "a" / "b" / "ev.jsonl"
    assert write_jsonl([rec(), rec(id="e2")], path) == 2
    back = read_jsonl(path)
    assert [r.id for r in back] == ["e1", "e2"] and back[0] == rec()


def test_read_skips_blank_lines_and_rejects_bad_rows(tmp_path: Path):
    path = tmp_path / "ev.jsonl"
    path.write_text(json.dumps(rec().to_dict(), ensure_ascii=False) + "\n\n", encoding="utf-8")
    assert len(read_jsonl(path)) == 1
    path.write_text('{"id": "x"}\n', encoding="utf-8")
    with pytest.raises(ContractError):
        read_jsonl(path)


def test_to_chunks_keeps_source_meta_and_regions():
    (c,) = to_chunks(rec())
    assert c.source_id == "s1" and c.tier == "B" and c.name == "○○구청"
    assert c.quote == "○○ 가을 야시장 2026-10-15" and c.regions == ("r",)
    assert c.text.startswith("○○ 가을 야시장\n2026-10-15–2026-10-18 ○○ 골목")
    assert c.meta["kind"] == "event" and c.meta["event_id"] == "e1"
    assert c.meta["start_date"] == "2026-10-15" and c.meta["status"] == "scheduled"


def test_to_chunks_without_dates_or_region():
    (c,) = to_chunks(rec(start_date=None, end_date=None, region=None, description=""))
    assert "날짜 미상" in c.text and c.regions == () and c.meta["start_date"] == ""


def test_long_description_splits_into_distinct_chunks():
    chunks = to_chunks(rec(description=("문장입니다. " * 300)))
    assert len(chunks) > 1 and len({c.chunk_id for c in chunks}) == len(chunks)


def test_chunks_can_be_indexed_and_found():
    with LocalIndex(":memory:") as idx:
        idx.add(to_chunks(rec()))
        hits = idx.search("야시장", regions=["r"])
        assert hits and hits[0].chunk.source_id == "s1"
        assert idx.search("야시장", regions=["other"]) == []
