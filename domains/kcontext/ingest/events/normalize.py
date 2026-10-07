"""공공 행사 API 응답 → ``EventRecord``. 필드 이름은 field_map 에서만 읽는다(코드에 API 필드 리터럴 금지).

field_map(JSON) 형식 — 값이 ``"[확인 필요]"`` 또는 빈 문자열인 필드는 없는 것으로 본다::

    {"provider": "tourapi",
     "items_path": ["response", "body", "items"],           # 응답에서 목록까지의 키 경로
     "fields": {"id": "...", "title": "...", "start_date": "...", "end_date": "...",
                "place": "...", "address": "...", "lat": "...", "lng": "...",
                "coord": "...",                               # "a,b" 한 칸일 때(coord_order 로 순서 지정)
                "url": "...", "updated": "...", "category": "...", "status": "...",
                "description": "..."},
     "date_format": "%Y%m%d",                                 # strptime 형식 → YYYY-MM-DD
     "coord_order": "lat_lng",                                # 또는 "lng_lat"
     "category_map": {"원본값": "festival"}, "status_map": {"원본값": "cancelled"}}
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from domains.kcontext.contract.errors import ContractError
from domains.kcontext.contract.records import (
    EVENT_CATEGORIES,
    EVENT_STATUSES,
    EventRecord,
    event_from_dict,
)
from domains.kcontext.regions import Region, regions_at, regions_in_text

__all__ = ["FieldMapMissing", "NormalizeResult", "load_field_map", "normalize", "pick_region"]

_PLACEHOLDER = "[확인 필요]"
_SOURCE_NAMES = {
    "tourapi": "한국관광공사 TourAPI",
    "seoul": "서울 열린데이터광장 문화행사",
}
_FILES = {"tourapi": "tourapi_festival.json", "seoul": "seoul_cultural.json"}


class FieldMapMissing(FileNotFoundError):
    pass


@dataclass(frozen=True)
class NormalizeResult:
    records: tuple[EventRecord, ...]
    problems: tuple[str, ...]
    skipped_out_of_region: int


def load_field_map(provider: Literal["tourapi", "seoul"], directory: Path | None = None) -> dict:
    base = Path(directory) if directory is not None else Path(__file__).parent / "field_maps"
    path = base / _FILES[provider]
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FieldMapMissing(f"{path.name} 이 없다") from None


def pick_region(
    lat: float | None, lng: float | None, text: str, regions: Mapping[str, Region]
) -> str | None:
    """좌표(bbox)가 있으면 먼저, 없거나 맞는 지역이 없으면 글(keywords)로 지역을 고른다."""
    if lat is not None and lng is not None:
        hits = regions_at(lat, lng, regions)
        if hits:
            return hits[0]
    hits = regions_in_text(text, regions)
    return hits[0] if hits else None


def _field(fm: Mapping, name: str) -> str | None:
    key = (fm.get("fields") or {}).get(name)
    if not isinstance(key, str) or not key.strip() or key.strip() == _PLACEHOLDER:
        return None
    return key


def _get(item: Mapping, fm: Mapping, name: str) -> str | None:
    key = _field(fm, name)
    if key is None or key not in item or item[key] is None:
        return None
    v = str(item[key]).strip()
    return v or None


def _to_float(v: str | None) -> float | None:
    try:
        return float(v) if v is not None else None
    except ValueError:
        return None


def _walk(raw: Any, path: Any) -> tuple[list | None, str | None]:
    cur = raw
    if not isinstance(path, list) or not all(isinstance(k, str) for k in path):
        return None, "items_path 는 문자열 목록이어야 한다"
    for i, key in enumerate(path):
        if isinstance(cur, list):
            return None, f"items_path[{i}]({key!r}) 앞에서 목록을 만났다"
        if not isinstance(cur, Mapping) or key not in cur:
            return None, f"items_path[{i}]({key!r}) 를 찾지 못했다"
        cur = cur[key]
    if isinstance(cur, Mapping):
        return [cur], None
    if isinstance(cur, list):
        return cur, None
    return None, "items_path 끝이 목록이 아니다"


def normalize(
    raw: Mapping | str,
    *,
    provider: str,
    field_map: Mapping,
    collected_at: str,
    regions: Mapping[str, Region],
) -> NormalizeResult:
    problems: list[str] = []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return NormalizeResult((), ("응답이 JSON 이 아니다",), 0)
    items, err = _walk(raw, field_map.get("items_path"))
    if items is None:
        return NormalizeResult((), (str(err),), 0)

    fmt = field_map.get("date_format")
    order = field_map.get("coord_order", "lat_lng")
    cat_map = field_map.get("category_map") or {}
    status_map = field_map.get("status_map") or {}
    name = _SOURCE_NAMES.get(provider, provider)
    records: dict[str, EventRecord] = {}
    skipped = 0

    def date_of(v: str | None, label: str, oid: str) -> str | None:
        if v is None:
            return None
        try:
            return datetime.strptime(v, fmt).date().isoformat()  # type: ignore[arg-type]  # noqa: DTZ007 - 날짜만 쓴다
        except (ValueError, TypeError):
            problems.append(f"{oid}: {label} 날짜를 읽지 못했다")
            return None

    for n, item in enumerate(items):
        if not isinstance(item, Mapping):
            problems.append(f"항목 {n}: 객체가 아니다")
            continue
        oid = _get(item, field_map, "id")
        title = _get(item, field_map, "title")
        if oid is None or title is None:
            problems.append(f"항목 {n}: id·제목이 없다")
            continue
        start = date_of(_get(item, field_map, "start_date"), "시작", oid)
        end = date_of(_get(item, field_map, "end_date"), "종료", oid)
        if start and end and end < start:
            problems.append(f"{oid}: 종료일이 시작일보다 빠르다 — 종료일을 비움")
            end = None
        lat = _to_float(_get(item, field_map, "lat"))
        lng = _to_float(_get(item, field_map, "lng"))
        coord = _get(item, field_map, "coord")
        if coord and lat is None and lng is None and "," in coord:
            a, b = (_to_float(x.strip()) for x in coord.split(",", 1))
            lat, lng = (a, b) if order == "lat_lng" else (b, a)
        if (lat is None) != (lng is None) or (
            lat is not None and lng is not None and not (-90 <= lat <= 90 and -180 <= lng <= 180)
        ):
            if lat is not None or lng is not None:
                problems.append(f"{oid}: 좌표가 올바르지 않아 버림")
            lat = lng = None
        place = _get(item, field_map, "place") or ""
        address = _get(item, field_map, "address") or ""
        region = pick_region(lat, lng, f"{address} {place} {title}", regions)
        if region is None:
            skipped += 1
            continue
        cat_raw = _get(item, field_map, "category")
        category = cat_map.get(cat_raw) if cat_raw else None
        if category not in EVENT_CATEGORIES:
            category = "other"
        st_raw = _get(item, field_map, "status")
        status = status_map.get(st_raw) if st_raw else None
        if status not in EVENT_STATUSES:
            status = "unknown"
        updated = date_of(_get(item, field_map, "updated"), "갱신", oid)
        url = _get(item, field_map, "url") or ""
        rec_raw = {
            "id": f"{provider}:{oid}", "region": region, "title": title, "category": category,
            "start_date": start, "end_date": end, "start_time": None, "end_time": None,
            "place_name": place, "lat": lat, "lng": lng, "geometry_type": "point",
            "radius_m": None, "status": status, "outdoor": None,
            "description": _get(item, field_map, "description") or "",
            "source": {
                "id": f"{provider}:{oid}", "tier": "B", "name": name,
                "locator": f"{updated} 갱신" if updated else f"{collected_at} 수집 · 갱신일 미제공",
                "url": url, "published": updated, "collected_at": collected_at,
                "quote": f"{title} / {start or '?'}–{end or '?'} / {place or '?'}",
            },
            "fetched_from": provider,
        }
        try:
            rec = event_from_dict(rec_raw)
        except ContractError as e:
            problems.append(f"{oid}: 계약 검증 실패 ({e})")
            continue
        if rec.id in records:
            problems.append(f"{oid}: id 중복 — 뒤 것만 남김")
        records[rec.id] = rec
    return NormalizeResult(tuple(records.values()), tuple(problems), skipped)
