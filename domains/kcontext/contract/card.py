"""카드(AGENT_CONTEXT 3.3 출력 + 3.3 보충) 검증기.

프론트 ``src/api/schema.js`` 의 ``validateCard`` 규칙을 모두 옮기고, Python 전용 규칙을 더한다.
문제 문구 형식은 schema.js 와 같다(``card[<id>].<필드>: <이유>``).

한계(프론트와 다른 점)
- schema.js 의 ``isCoord`` 는 "숫자 2개짜리 배열"인지만 본다. **좌표 순서를 구분하지 못한다.**
  이 모듈은 ``geometry.space`` 가 없거나 ``"geo"`` 이면 ``[lat, lng]`` 로 보고 범위
  (-90..90, -180..180)를 검사하므로 ``[lng, lat]`` 로 뒤바뀐 값이 범위 밖일 때만 잡힌다.
  범위 안에 우연히 들어가는 뒤바뀐 값은 어느 쪽도 잡지 못한다.
- ``space == "schematic"`` 좌표(목업 viewBox)는 범위를 검사하지 않는다.
- schema.js 는 story 카드에 narration 을 필수로 요구하지만 이 모듈은 Text 또는 null 을 허용한다
  (계약 보충 5).
"""

from __future__ import annotations

from collections.abc import Mapping

from .source import validate_source
from .text import is_nonempty_str, is_number, is_text

KINDS = ("story", "now")
GEOMETRY_TYPES = ("point", "segment", "area", "approx")
GEOMETRY_SPACES = ("geo", "schematic")
STORY_BADGES = ("기록", "전승", "추정")
NOW_BADGES = ("확인됨", "확인 필요", "보류")
USER_STATES = ("proposed", "added", "visited", "skipped")
CHECK_LEVELS = ("ok", "warn", "bad")
REJECT_REASONS = (
    "관련 없음",
    "중복",
    "신뢰 불가",
    "기간 지남",
    "동선에서 너무 멂",
    "관심사 불일치",
    "상황 부적합",
    "지시문 포함",
    "위치 미상",
    "취소됨",
)

__all__ = [
    "CHECK_LEVELS",
    "GEOMETRY_SPACES",
    "GEOMETRY_TYPES",
    "KINDS",
    "NOW_BADGES",
    "REJECT_REASONS",
    "STORY_BADGES",
    "USER_STATES",
    "coord_in_range",
    "is_coord",
    "validate_card",
    "validate_geometry",
]


def is_coord(c: object) -> bool:
    return isinstance(c, (list, tuple)) and len(c) == 2 and all(is_number(n) for n in c)


def coord_in_range(c: object) -> bool:
    """``[lat, lng]`` 범위 안인가."""
    return is_coord(c) and -90 <= c[0] <= 90 and -180 <= c[1] <= 180  # type: ignore[index]


def validate_geometry(g: object, at: str) -> list[str]:
    """``at`` 은 ``card[x]`` 같은 접두사. 문제 문구는 ``{at}.geometry...`` 로 시작한다."""
    if not isinstance(g, Mapping) or g.get("type") not in GEOMETRY_TYPES:
        return [f"{at}.geometry.type: {'|'.join(GEOMETRY_TYPES)}"]
    p: list[str] = []
    coords = g.get("coords")
    if (
        not isinstance(coords, (list, tuple))
        or len(coords) == 0
        or not all(is_coord(c) for c in coords)
    ):
        p.append(f"{at}.geometry.coords: [[a,b],…]")
        coords = None
    if g["type"] == "segment" and coords is not None and len(coords) < 2:
        p.append(f"{at}.geometry: segment 는 좌표 2개 이상")
    if not is_text(g.get("basis")):
        p.append(f"{at}.geometry.basis")
    space = g.get("space")
    if space is not None and space not in GEOMETRY_SPACES:
        p.append(f"{at}.geometry.space: {'|'.join(GEOMETRY_SPACES)}")
    elif space in (None, "geo") and coords is not None:
        for i, c in enumerate(coords):
            if not coord_in_range(c):
                p.append(
                    f"{at}.geometry.coords[{i}]: [lat,lng] 범위 밖(lat -90..90, lng -180..180)"
                )
    r = g.get("radius_m")
    if g["type"] == "approx":
        if not is_number(r) or r <= 0:
            p.append(f"{at}.geometry.radius_m: approx 는 양수 필요")
    elif r is not None and (not is_number(r) or r <= 0):
        p.append(f"{at}.geometry.radius_m: 양수")
    return p


def _is_int(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _text_or_none(c: Mapping, k: str, at: str, p: list[str]) -> None:
    if c.get(k) is not None and not is_text(c[k]):
        p.append(f"{at}.{k}: Text 또는 null")


def _validate_extensions(c: Mapping, at: str, n_sources: int, p: list[str]) -> None:
    """계약 보충 3 — 있으면 형식만 검사하고 없어도 통과."""
    for k in ("era", "only", "kind_label"):
        _text_or_none(c, k, at, p)
    facts = c.get("facts")
    if facts is not None:
        if not isinstance(facts, list):
            p.append(f"{at}.facts: 배열")
        else:
            for i, f in enumerate(facts):
                fa = f"{at}.facts[{i}]"
                if not isinstance(f, Mapping) or not is_text(f.get("text")):
                    p.append(f"{fa}.text")
                ref = f.get("ref") if isinstance(f, Mapping) else None
                if not _is_int(ref) or not 1 <= ref <= n_sources:
                    p.append(f"{fa}.ref: 1..{n_sources} 정수(sources 번호)")
    alts = c.get("alternatives")
    if alts is not None:
        if not isinstance(alts, list):
            p.append(f"{at}.alternatives: 배열")
        else:
            for i, a in enumerate(alts):
                if not (
                    isinstance(a, Mapping) and is_text(a.get("label")) and is_text(a.get("text"))
                ):
                    p.append(f"{at}.alternatives[{i}]: {{label, text}}")
    checks = c.get("checks")
    if checks is not None:
        if not isinstance(checks, list):
            p.append(f"{at}.checks: 배열")
        else:
            for i, x in enumerate(checks):
                if not (
                    isinstance(x, Mapping)
                    and x.get("level") in CHECK_LEVELS
                    and is_text(x.get("text"))
                ):
                    p.append(f"{at}.checks[{i}]: {{level: {'|'.join(CHECK_LEVELS)}, text}}")
    if c.get("poster") is not None and not isinstance(c["poster"], Mapping):
        p.append(f"{at}.poster: 객체 또는 null")
    w = c.get("warning")
    if w is not None and not (
        isinstance(w, Mapping) and is_text(w.get("title")) and is_text(w.get("body"))
    ):
        p.append(f"{at}.warning: {{title, body}} 또는 null")


def validate_card(c: Mapping) -> list[str]:
    cid = c.get("id") if isinstance(c, Mapping) else None
    at = f"card[{cid}]"
    if not isinstance(c, Mapping):
        return [f"{at}: 객체가 아님"]
    p: list[str] = []
    if not is_nonempty_str(c.get("id")):
        p.append(f"{at}.id")
    kind = c.get("kind")
    if kind not in KINDS:
        p.append(f"{at}.kind: story|now")
    if not is_text(c.get("title")):
        p.append(f"{at}.title")
    if not is_text(c.get("body")):
        p.append(f"{at}.body")
    p.extend(validate_geometry(c.get("geometry"), at))
    badge = c.get("badge")
    bk = "story" if badge in STORY_BADGES else "now" if badge in NOW_BADGES else None
    if bk is None:
        p.append(f'{at}.badge: 알 수 없는 딱지 "{badge}"')
    elif bk != kind:
        p.append(f"{at}.badge: {kind} 카드에 {bk} 딱지")
    sources = c.get("sources")
    n_sources = 0
    if not isinstance(sources, list) or len(sources) == 0:
        p.append(f"{at}.sources: 비어 있음(출처 없는 카드는 없다)")
    else:
        n_sources = len(sources)
        for i, s in enumerate(sources):
            p.extend(validate_source(s, f"{at}.sources[{i}]"))
    if c.get("user_state") not in USER_STATES:
        p.append(f"{at}.user_state")
    for k in ("why_fits", "caveats", "rejected"):
        if not isinstance(c.get(k), list):
            p.append(f"{at}.{k}: 배열")
    for i, r in enumerate(c["rejected"] if isinstance(c.get("rejected"), list) else []):
        ra = f"{at}.rejected[{i}]"
        if not isinstance(r, Mapping) or not is_text(r.get("claim")):
            p.append(f"{ra}.claim")
        if not isinstance(r, Mapping) or r.get("reason") not in REJECT_REASONS:
            p.append(f"{ra}.reason: REJECT_REASONS 중 하나")
    if kind == "now":
        slot = c.get("slot")
        if not isinstance(slot, Mapping) or not is_number(slot.get("day")):
            p.append(f"{at}.slot.day: now 카드는 slot 필요")
        if not is_number(c.get("time_cost_min")):
            p.append(f"{at}.time_cost_min")
        valid = c.get("valid")
        if not isinstance(valid, Mapping) or not is_nonempty_str(valid.get("as_of")):
            p.append(f"{at}.valid.as_of")
    if kind == "story" and c.get("narration") is not None and not is_text(c["narration"]):
        p.append(f"{at}.narration: Text 또는 null")
    _validate_extensions(c, at, n_sources, p)
    return p
