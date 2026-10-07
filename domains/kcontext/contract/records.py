"""파이프라인 내부 레코드(AGENT_CONTEXT 3.3 밖). frozen dataclass + ``from_dict`` / ``to_dict``.

``from_dict`` 는 모르는 키·잘못된 형식이면 ``ContractError`` 를 던진다. 이야기·행사 파일은
신뢰할 수 없는 입력이므로 (필수 키가 빠졌거나 모르는 키가 있으면) 조용히 넘어가지 않는다.
기본값이 없는 필드는 키가 반드시 있어야 한다(값이 null 이어도 키는 쓴다).
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import MISSING, dataclass, fields
from typing import Any, Literal

from .card import REJECT_REASONS, validate_geometry
from .errors import ContractError
from .source import validate_source
from .text import Text, is_date, is_hhmm, is_nonempty_str, is_number, is_text
from .verdict import STANCES

EVENT_CATEGORIES = (
    "festival",
    "performance",
    "exhibition",
    "market",
    "night_market",
    "bar",
    "other",
)
CLAIM_KINDS = ("fact", "lore", "inference")
ALIGNMENTS = ("exact", "approx")
EVENT_GEOMETRY_TYPES = ("point", "area", "approx")
EVENT_STATUSES = ("scheduled", "cancelled", "changed", "unknown")
FETCHED_FROM = ("tourapi", "seoul", "manual", "web", "fixture")
BLOCK_VERDICTS = ("injection", "suspicious")
# 월·연도가 적히지 않은 일자를 게시일 기준으로 보충한 레코드의 source.locator 에 붙는 표시(D12).
INFERRED_DATE_NOTE = "날짜 게시일 기준 추정"

__all__ = [
    "ALIGNMENTS",
    "BLOCK_VERDICTS",
    "CLAIM_KINDS",
    "EVENT_CATEGORIES",
    "EVENT_GEOMETRY_TYPES",
    "EVENT_STATUSES",
    "FETCHED_FROM",
    "INFERRED_DATE_NOTE",
    "Blocked",
    "EventRecord",
    "Evidence",
    "Rejection",
    "SourceRef",
    "StoryClaim",
    "StoryRecord",
    "event_from_dict",
    "story_from_dict",
]


def _plain(v: Any) -> Any:
    """dataclass·tuple·Mapping 을 JSON 으로 쓸 수 있는 dict·list 로."""
    if hasattr(v, "to_dict"):
        return v.to_dict()
    if isinstance(v, Mapping):
        return {k: _plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    return v


def _to_dict(obj: Any) -> dict[str, Any]:
    return {f.name: _plain(getattr(obj, f.name)) for f in fields(obj)}


def _check_keys(d: object, cls: type, at: str) -> list[str]:
    if not isinstance(d, Mapping):
        return [f"{at}: 객체가 아님"]
    names = {f.name for f in fields(cls)}
    required = {
        f.name for f in fields(cls) if f.default is MISSING and f.default_factory is MISSING
    }
    p = [f"{at}.{k}: 모르는 키" for k in d if k not in names]
    p += [f"{at}.{k}: 필수 키 없음" for k in sorted(required) if k not in d]
    return p


def _str_or_none(d: Mapping, k: str, at: str, p: list[str]) -> None:
    if d.get(k) is not None and not isinstance(d[k], str):
        p.append(f"{at}.{k}: 문자열 또는 null")


@dataclass(frozen=True)
class SourceRef:
    id: str
    tier: str
    name: str
    locator: str
    url: str
    published: str | None
    collected_at: str
    quote: str
    bib: str | None = None

    @classmethod
    def from_dict(cls, d: Mapping, at: str = "source") -> SourceRef:
        p = _check_keys(d, cls, at)
        if not p:
            p = validate_source(d, at)
        if p:
            raise ContractError(p)
        return cls(**{f.name: d[f.name] for f in fields(cls) if f.name in d})

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(self)


@dataclass(frozen=True)
class Evidence:
    source: SourceRef
    stance: Literal["support", "contradict"]
    says: str | None = None
    claim_kind: Literal["fact", "lore", "inference"] = "fact"

    @classmethod
    def from_dict(cls, d: Mapping, at: str = "evidence") -> Evidence:
        p = _check_keys(d, cls, at)
        if not p:
            if d["stance"] not in STANCES:
                p.append(f"{at}.stance: {'|'.join(STANCES)}")
            _str_or_none(d, "says", at, p)
            if d.get("claim_kind", "fact") not in CLAIM_KINDS:
                p.append(f"{at}.claim_kind: {'|'.join(CLAIM_KINDS)}")
        if p:
            raise ContractError(p)
        src = SourceRef.from_dict(d["source"], f"{at}.source")
        return cls(src, d["stance"], d.get("says"), d.get("claim_kind", "fact"))

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(self)


@dataclass(frozen=True)
class StoryClaim:
    text: Text
    evidence: tuple[Evidence, ...]

    @classmethod
    def from_dict(cls, d: Mapping, at: str = "claim") -> StoryClaim:
        p = _check_keys(d, cls, at)
        if not p:
            if not is_text(d["text"]):
                p.append(f"{at}.text")
            if not isinstance(d["evidence"], (list, tuple)):
                p.append(f"{at}.evidence: 배열")
        if p:
            raise ContractError(p)
        ev = tuple(
            Evidence.from_dict(e, f"{at}.evidence[{i}]") for i, e in enumerate(d["evidence"])
        )
        return cls(copy.deepcopy(d["text"]), ev)

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(self)


@dataclass(frozen=True)
class StoryRecord:
    id: str
    region: str
    title: Text
    theme: str
    era: str | None
    geometry: Mapping  # 카드 geometry 와 같은 모양, space 는 "geo"
    alignment: Literal["exact", "approx"]
    claims: tuple[StoryClaim, ...]
    narration: Text | None = None
    synthetic: bool = False

    @classmethod
    def from_dict(cls, d: Mapping, at: str = "story") -> StoryRecord:
        at = f"{at}[{d.get('id') if isinstance(d, Mapping) else None}]"
        p = _check_keys(d, cls, at)
        if not p:
            for k in ("id", "region", "theme"):
                if not is_nonempty_str(d[k]):
                    p.append(f"{at}.{k}: 문자열 필요")
            if not is_text(d["title"]):
                p.append(f"{at}.title")
            _str_or_none(d, "era", at, p)
            g = d["geometry"]
            if isinstance(g, Mapping) and g.get("space", "geo") != "geo":
                p.append(f'{at}.geometry.space: 이야기 레코드는 "geo"')
            p.extend(validate_geometry(g, at))
            if d["alignment"] not in ALIGNMENTS:
                p.append(f"{at}.alignment: {'|'.join(ALIGNMENTS)}")
            if not isinstance(d["claims"], (list, tuple)):
                p.append(f"{at}.claims: 배열")
            if d.get("narration") is not None and not is_text(d["narration"]):
                p.append(f"{at}.narration: Text 또는 null")
            if "synthetic" in d and not isinstance(d["synthetic"], bool):
                p.append(f"{at}.synthetic: boolean")
        if p:
            raise ContractError(p)
        claims = tuple(
            StoryClaim.from_dict(c, f"{at}.claims[{i}]") for i, c in enumerate(d["claims"])
        )
        return cls(
            id=d["id"],
            region=d["region"],
            title=copy.deepcopy(d["title"]),
            theme=d["theme"],
            era=d["era"],
            geometry=copy.deepcopy(dict(d["geometry"])),
            alignment=d["alignment"],
            claims=claims,
            narration=copy.deepcopy(d.get("narration")),
            synthetic=d.get("synthetic", False),
        )

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(self)


@dataclass(frozen=True)
class EventRecord:
    id: str
    region: str | None
    title: Text
    category: str
    start_date: str | None
    end_date: str | None  # "YYYY-MM-DD"
    start_time: str | None
    end_time: str | None  # "HH:MM"
    place_name: str
    lat: float | None
    lng: float | None
    geometry_type: Literal["point", "area", "approx"]
    radius_m: int | None
    status: Literal["scheduled", "cancelled", "changed", "unknown"]
    outdoor: bool | None
    description: str
    source: SourceRef
    fetched_from: Literal["tourapi", "seoul", "manual", "web", "fixture"]
    synthetic: bool = False

    @classmethod
    def from_dict(cls, d: Mapping, at: str = "event") -> EventRecord:
        at = f"{at}[{d.get('id') if isinstance(d, Mapping) else None}]"
        p = _check_keys(d, cls, at)
        if not p:
            if not is_nonempty_str(d["id"]):
                p.append(f"{at}.id: 문자열 필요")
            _str_or_none(d, "region", at, p)
            if not is_text(d["title"]):
                p.append(f"{at}.title")
            if d["category"] not in EVENT_CATEGORIES:
                p.append(f"{at}.category: {'|'.join(EVENT_CATEGORIES)}")
            for k in ("start_date", "end_date"):
                if d[k] is not None and not is_date(d[k]):
                    p.append(f"{at}.{k}: YYYY-MM-DD 또는 null")
            for k in ("start_time", "end_time"):
                if d[k] is not None and not is_hhmm(d[k]):
                    p.append(f"{at}.{k}: HH:MM 또는 null")
            if (
                is_date(d["start_date"])
                and is_date(d["end_date"])
                and d["start_date"] > d["end_date"]
            ):
                p.append(f"{at}: start_date 가 end_date 보다 늦음")
            if not isinstance(d["place_name"], str):
                p.append(f"{at}.place_name: 문자열 필요")
            for k, lo, hi in (("lat", -90, 90), ("lng", -180, 180)):
                if d[k] is not None and not (is_number(d[k]) and lo <= d[k] <= hi):
                    p.append(f"{at}.{k}: 숫자({lo}..{hi}) 또는 null")
            if (d["lat"] is None) != (d["lng"] is None):
                p.append(f"{at}: lat·lng 는 둘 다 있거나 둘 다 null")
            if d["geometry_type"] not in EVENT_GEOMETRY_TYPES:
                p.append(f"{at}.geometry_type: {'|'.join(EVENT_GEOMETRY_TYPES)}")
            r = d["radius_m"]
            if r is not None and (isinstance(r, bool) or not isinstance(r, int) or r <= 0):
                p.append(f"{at}.radius_m: 양의 정수 또는 null")
            if d["geometry_type"] == "approx" and r is None:
                p.append(f"{at}.radius_m: approx 는 필요")
            if d["status"] not in EVENT_STATUSES:
                p.append(f"{at}.status: {'|'.join(EVENT_STATUSES)}")
            if d["outdoor"] is not None and not isinstance(d["outdoor"], bool):
                p.append(f"{at}.outdoor: boolean 또는 null")
            if not isinstance(d["description"], str):
                p.append(f"{at}.description: 문자열 필요")
            if d["fetched_from"] not in FETCHED_FROM:
                p.append(f"{at}.fetched_from: {'|'.join(FETCHED_FROM)}")
            if "synthetic" in d and not isinstance(d["synthetic"], bool):
                p.append(f"{at}.synthetic: boolean")
        if p:
            raise ContractError(p)
        src = SourceRef.from_dict(d["source"], f"{at}.source")
        vals = {f.name: d[f.name] for f in fields(cls) if f.name in d}
        vals["title"] = copy.deepcopy(d["title"])
        vals["source"] = src
        return cls(**vals)

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(self)


# 판정 공통 출력 (T211a·T211b 가 함께 쓴다 — 같은 스테이지 병렬 import 충돌 방지용으로 여기에 둔다)
@dataclass(frozen=True)
class Rejection:
    target_id: str
    claim: str
    reason: str  # REJECT_REASONS 중 하나
    detail: str

    def __post_init__(self) -> None:
        if self.reason not in REJECT_REASONS:
            raise ValueError(f"reason 은 REJECT_REASONS 중 하나여야 한다: {self.reason!r}")

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(self)


@dataclass(frozen=True)
class Blocked:
    source_id: str
    verdict: Literal["injection", "suspicious"]
    rules: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.verdict not in BLOCK_VERDICTS:
            raise ValueError(f"verdict 는 {'|'.join(BLOCK_VERDICTS)} 중 하나여야 한다")
        if not isinstance(self.rules, tuple) or not all(isinstance(r, str) for r in self.rules):
            raise ValueError("rules 는 문자열 tuple 이어야 한다")

    def to_dict(self) -> dict[str, Any]:
        return _to_dict(self)


def story_from_dict(d: Mapping) -> StoryRecord:
    return StoryRecord.from_dict(d)


def event_from_dict(d: Mapping) -> EventRecord:
    return EventRecord.from_dict(d)
