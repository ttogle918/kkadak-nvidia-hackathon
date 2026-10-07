"""경로(AGENT_CONTEXT 3.3 출력 — 경로 + 보충 4) 검증기. 문구 형식은 schema.js 와 같다.

경로에는 ``space`` 가 없어서 ``segments[].coords`` 의 좌표 범위는 검사하지 않는다(목업 좌표계
``[x, y]`` 와 구분할 수 없다). 형식(숫자 2개짜리 배열, 2점 이상)만 본다.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping

from .card import is_coord
from .text import is_nonempty_str, is_number, is_text

ROUTE_BADGES = ("가장 빠름", "이야기 가장 많음", "추천")

__all__ = ["ROUTE_BADGES", "validate_route"]


def validate_route(r: Mapping, card_ids: Collection[str] | None = None) -> list[str]:
    at = f"route[{r.get('id') if isinstance(r, Mapping) else None}]"
    if not isinstance(r, Mapping):
        return [f"{at}: 객체가 아님"]
    p: list[str] = []
    if not is_nonempty_str(r.get("id")):
        p.append(f"{at}.id")
    if not is_text(r.get("theme")):
        p.append(f"{at}.theme")
    for k in ("walk_min", "delta_min", "story_count"):
        if not is_number(r.get(k)):
            p.append(f"{at}.{k}: 숫자")
    if is_number(r.get("delta_min")) and r["delta_min"] < 0:
        p.append(f"{at}.delta_min: 0 이상")
    badges = r.get("badges")
    if not isinstance(badges, list):
        p.append(f"{at}.badges: 배열")
    else:
        for b in badges:
            if b not in ROUTE_BADGES:
                p.append(f"{at}.badges: 알 수 없는 딱지 {b!r}")
    if "estimated" in r and not isinstance(r["estimated"], bool):
        p.append(f"{at}.estimated: boolean")
    segs = r.get("segments")
    if not isinstance(segs, list) or len(segs) == 0:
        p.append(f"{at}.segments: 비어 있음")
        return p
    for i, s in enumerate(segs):
        sa = f"{at}.segments[{i}]"
        if not isinstance(s, Mapping):
            p.append(f"{sa}: 객체가 아님")
            continue
        if not is_text(s.get("name")):
            p.append(f"{sa}.name")
        cid = s.get("card_id")
        if cid is not None and not isinstance(cid, str):
            p.append(f"{sa}.card_id: string|null")
        if card_ids is not None and cid and cid not in card_ids:
            p.append(f"{sa}.card_id: 없는 카드 {cid}")
        if not isinstance(s.get("weak"), bool):
            p.append(f"{sa}.weak: boolean")
        co = s.get("coords")
        if co is not None and (
            not isinstance(co, (list, tuple)) or len(co) < 2 or not all(is_coord(c) for c in co)
        ):
            p.append(f"{sa}.coords: [[a,b],…] 2점 이상")
        lxy = s.get("label_xy")
        if lxy is not None and not is_coord(lxy):
            p.append(f"{sa}.label_xy: [x,y] 또는 null")
        for k in ("length_m", "walk_min"):
            if s.get(k) is not None and not is_number(s[k]):
                p.append(f"{sa}.{k}: 숫자")
    with_card = sum(1 for s in segs if isinstance(s, Mapping) and s.get("card_id"))
    sc = r.get("story_count")
    if is_number(sc) and with_card != sc:
        p.append(f"{at}.story_count({sc}) != 카드 있는 구간 수({with_card})")
    return p
