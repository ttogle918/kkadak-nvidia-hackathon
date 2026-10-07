"""손으로 넣는 공지(구청 공지·변경 공지)와 합성 자료. ``EventRecord`` 모양 JSON 배열을 읽는다."""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping
from pathlib import Path

from domains.kcontext.contract.errors import ContractError
from domains.kcontext.contract.records import EventRecord, event_from_dict
from domains.kcontext.contract.text import pick
from domains.kcontext.regions import Region

from .normalize import NormalizeResult, pick_region

__all__ = ["load_manual"]


def load_manual(path: Path, *, regions: Mapping[str, Region]) -> NormalizeResult:
    problems: list[str] = []
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return NormalizeResult((), (f"{Path(path).name}: 읽을 수 없다 ({type(e).__name__})",), 0)
    if not isinstance(raw, list):
        return NormalizeResult((), (f"{Path(path).name}: 최상위가 배열이 아니다",), 0)
    records: dict[str, EventRecord] = {}
    skipped = 0
    for n, item in enumerate(raw):
        try:
            rec = event_from_dict(item)
        except ContractError as e:
            problems.append(f"항목 {n}: 계약 검증 실패 ({e})")
            continue
        if rec.fetched_from != "manual":
            problems.append(f"{rec.id}: fetched_from 이 manual 이 아니다 — 버림")
            continue
        if rec.region is not None and rec.region not in regions:
            problems.append(f"{rec.id}: 알 수 없는 지역 {rec.region!r} — 버림")
            skipped += 1
            continue
        if rec.region is None:
            text = f"{pick(rec.title, 'ko')} {rec.place_name} {rec.description}"
            region = pick_region(rec.lat, rec.lng, text, regions)
            if region is None:
                skipped += 1
                continue
            rec = dataclasses.replace(rec, region=region)
        if rec.id in records:
            problems.append(f"{rec.id}: id 중복 — 뒤 것만 남김")
        records[rec.id] = rec
    return NormalizeResult(tuple(records.values()), tuple(problems), skipped)
