"""행사 레코드 JSONL 저장과 색인 청크 변환."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from domains.kcontext.contract.records import EventRecord, event_from_dict
from domains.kcontext.contract.text import pick
from domains.kcontext.index.chunk import chunk_text, make_chunk_id
from domains.kcontext.index.store import Chunk

__all__ = ["read_jsonl", "to_chunks", "write_jsonl"]


def write_jsonl(records: Iterable[EventRecord], path: Path) -> int:
    """레코드마다 한 줄. 부모 폴더는 만든다. 쓴 줄 수를 돌려준다."""
    rows = [json.dumps(r.to_dict(), ensure_ascii=False) + "\n" for r in records]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(rows), encoding="utf-8")
    return len(rows)


def read_jsonl(path: Path) -> list[EventRecord]:
    """빈 줄은 건너뛴다. 계약에 어긋나는 줄이 있으면 ContractError."""
    out: list[EventRecord] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(event_from_dict(json.loads(line)))
    return out


def to_chunks(r: EventRecord) -> list[Chunk]:
    """행사 한 건 → 검색용 청크. 출처 메타는 레코드의 SourceRef 를 그대로 쓴다."""
    s = r.source
    span = r.start_date or "날짜 미상"
    if r.end_date and r.end_date != r.start_date:
        span = f"{span}–{r.end_date}"
    text = f"{pick(r.title, 'ko')}\n{span} {r.place_name}".rstrip()
    if r.description:
        text = f"{text}\n{r.description}"
    meta = {
        "kind": "event",
        "event_id": r.id,
        "category": r.category,
        "status": r.status,
        "fetched_from": r.fetched_from,
        "start_date": r.start_date or "",
        "end_date": r.end_date or "",
    }
    regions = (r.region,) if r.region else ()
    return [
        Chunk(
            chunk_id=make_chunk_id(s.id, s.locator, piece),
            source_id=s.id, tier=s.tier, name=s.name, locator=s.locator, url=s.url,
            published=s.published, collected_at=s.collected_at, text=piece, quote=s.quote,
            regions=regions, meta=meta,
        )
        for piece in chunk_text(text)
    ]
