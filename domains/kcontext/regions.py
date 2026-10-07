"""지역 설정 로더. 지역 이름·구·좌표·검색어는 data/regions/*.json 에서만 읽는다."""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from domains.kcontext.paths import data_dir

__all__ = ["Region", "RegionConfigError", "load_regions", "regions_at", "regions_in_text"]

_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_KEYS = {
    "id", "name", "gu", "bbox", "center", "keywords", "sillok_keywords", "note", "synthetic",
}
_REQUIRED = {"id", "name", "gu", "bbox", "center", "keywords"}


class RegionConfigError(ValueError):
    """지역 설정 오류. 메시지에 파일 이름이 들어간다."""


@dataclass(frozen=True)
class Region:
    id: str
    name: dict[str, str]
    gu: tuple[str, ...]
    bbox: tuple[float, float, float, float] | None  # (south, west, north, east)
    center: tuple[float, float] | None  # (lat, lng)
    keywords: tuple[str, ...]
    sillok_keywords: tuple[str, ...]


def _is_num(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _str_list(v: object, what: str, fname: str, *, allow_empty_list: bool) -> tuple[str, ...]:
    if not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v):
        raise RegionConfigError(f"{fname}: {what} 는 비어 있지 않은 문자열 목록이어야 한다")
    if not v and not allow_empty_list:
        raise RegionConfigError(f"{fname}: {what} 가 비었다")
    return tuple(v)


def _parse(path: Path) -> Region:
    fname = path.name
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise RegionConfigError(f"{fname}: 읽을 수 없다 ({type(e).__name__})") from e
    if not isinstance(raw, dict):
        raise RegionConfigError(f"{fname}: 최상위가 객체가 아니다")
    unknown = set(raw) - _KEYS
    if unknown:
        raise RegionConfigError(f"{fname}: 모르는 키 {sorted(unknown)}")
    missing = _REQUIRED - set(raw)
    if missing:
        raise RegionConfigError(f"{fname}: 빠진 키 {sorted(missing)}")
    rid = raw["id"]
    if not isinstance(rid, str) or not _ID_RE.match(rid):
        raise RegionConfigError(f"{fname}: id 형식 오류")
    if rid != path.stem:
        raise RegionConfigError(f"{fname}: id({rid}) 가 파일 이름과 다르다")
    name = raw["name"]
    if (
        not isinstance(name, dict)
        or set(name) != {"ko", "en"}
        or not all(isinstance(x, str) and x.strip() for x in name.values())
    ):
        raise RegionConfigError(f"{fname}: name 은 {{ko, en}} 문자열이어야 한다")
    gu = _str_list(raw["gu"], "gu", fname, allow_empty_list=True)
    keywords = _str_list(raw["keywords"], "keywords", fname, allow_empty_list=False)
    sillok = _str_list(raw.get("sillok_keywords", []), "sillok_keywords", fname,
                       allow_empty_list=True)
    bbox = raw["bbox"]
    if bbox is not None:
        if not (isinstance(bbox, list) and len(bbox) == 4 and all(_is_num(x) for x in bbox)):
            raise RegionConfigError(f"{fname}: bbox 는 숫자 4개 [south, west, north, east]")
        s, w, n, e = bbox
        if not (s <= n and w <= e):
            raise RegionConfigError(f"{fname}: bbox 순서 오류 (south<=north, west<=east)")
        bbox = (float(s), float(w), float(n), float(e))
    center = raw["center"]
    if center is not None:
        if not (isinstance(center, list) and len(center) == 2 and all(_is_num(x) for x in center)):
            raise RegionConfigError(f"{fname}: center 는 숫자 2개 [lat, lng]")
        center = (float(center[0]), float(center[1]))
    return Region(rid, dict(name), gu, bbox, center, keywords, sillok)


def load_regions(directory: Path | None = None) -> dict[str, Region]:
    """directory(기본 data_dir()/regions)의 *.json 을 이름순으로 읽는다."""
    base = Path(directory) if directory is not None else data_dir() / "regions"
    if not base.is_dir():
        raise RegionConfigError(f"{base.name}: 지역 폴더가 없다")
    files = sorted(base.glob("*.json"))
    if not files:
        raise RegionConfigError(f"{base.name}: 지역 파일이 없다")
    out: dict[str, Region] = {}
    for f in files:
        r = _parse(f)
        if r.id in out:
            raise RegionConfigError(f"{f.name}: id 중복 {r.id}")
        out[r.id] = r
    return out


def regions_at(lat: float, lng: float, regions: Mapping[str, Region]) -> list[str]:
    """좌표가 bbox 안(경계 포함)인 지역 id. bbox 없는 지역은 건너뛴다."""
    hits = []
    for rid, r in regions.items():
        if r.bbox is None:
            continue
        s, w, n, e = r.bbox
        if s <= lat <= n and w <= lng <= e:
            hits.append(rid)
    return sorted(hits)


def regions_in_text(
    text: str,
    regions: Mapping[str, Region],
    *,
    field: Literal["keywords", "sillok_keywords"] = "keywords",
) -> list[str]:
    """NFKC 정규화 후 부분 문자열이 일치한 지역 id (정렬·중복 없음)."""
    if field not in ("keywords", "sillok_keywords"):
        raise ValueError(f"field: {field}")
    hay = unicodedata.normalize("NFKC", text)
    hits = set()
    for rid, r in regions.items():
        for kw in getattr(r, field):
            k = unicodedata.normalize("NFKC", kw)
            if k and k in hay:
                hits.add(rid)
                break
    return sorted(hits)
