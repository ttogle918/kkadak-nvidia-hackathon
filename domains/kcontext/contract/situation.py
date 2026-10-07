"""사용자 상황 입력(AGENT_CONTEXT 3.3 입력 + 보충 6)의 검증기.

사용자가 채팅에 붙여 넣은 일정에서 추출한 값이므로 신뢰하지 않는다 — 형식만 확인하고, 문자열
안의 지시문은 해석하지 않는다.
"""

from __future__ import annotations

import datetime
from collections.abc import Mapping

from .text import is_date, is_nonempty_str, is_number

ANCHOR_TYPES = ("flight", "hotel", "train", "bus", "visit")
LANGUAGES = ("ko", "en")

__all__ = ["ANCHOR_TYPES", "LANGUAGES", "validate_situation"]


def _dt(v: object) -> datetime.datetime | None:
    """``YYYY-MM-DDTHH:MM``(초 허용) 파싱. 실패하면 None. 시간대 표기는 받지 않는다."""
    if not isinstance(v, str):
        return None
    try:
        d = datetime.datetime.fromisoformat(v)
    except ValueError:
        return None
    return d if d.tzinfo is None and "T" in v else None


def _latlng(o: Mapping, at: str, p: list[str], *, required: bool = False) -> None:
    for k, lo, hi in (("lat", -90, 90), ("lng", -180, 180)):
        v = o.get(k)
        if v is None:
            if required:
                p.append(f"{at}.{k}: 숫자 필요")
        elif not is_number(v) or not lo <= v <= hi:
            p.append(f"{at}.{k}: 숫자({lo}..{hi}) 또는 null")


def _place(o: object, at: str, p: list[str]) -> None:
    if not isinstance(o, Mapping):
        p.append(f"{at}: 객체가 아님")
        return
    if not is_nonempty_str(o.get("name")):
        p.append(f"{at}.name: 문자열 필요")
    _latlng(o, at, p, required=True)


def validate_situation(s: Mapping) -> list[str]:
    if not isinstance(s, Mapping):
        return ["situation: 객체가 아님"]
    p: list[str] = []
    trip = s.get("trip")
    if (
        not isinstance(trip, Mapping)
        or not is_date(trip.get("from"))
        or not is_date(trip.get("to"))
    ):
        p.append("situation.trip: {from, to} YYYY-MM-DD")
    elif trip["from"] > trip["to"]:
        p.append("situation.trip: from 이 to 보다 늦음")
    anchors = s.get("anchors")
    if not isinstance(anchors, list):
        p.append("situation.anchors: 배열")
    else:
        for i, a in enumerate(anchors):
            aa = f"situation.anchors[{i}]"
            if not isinstance(a, Mapping):
                p.append(f"{aa}: 객체가 아님")
                continue
            if a.get("type") not in ANCHOR_TYPES:
                p.append(f"{aa}.type: {'|'.join(ANCHOR_TYPES)}")
            if not is_nonempty_str(a.get("name")):
                p.append(f"{aa}.name: 문자열 필요")
            _latlng(a, aa, p)
            for k in ("from", "to", "at"):
                if k in a and a[k] is not None and _dt(a[k]) is None:
                    p.append(f"{aa}.{k}: YYYY-MM-DDTHH:MM")
    slots = s.get("free_slots")
    if not isinstance(slots, list):
        p.append("situation.free_slots: 배열")
    else:
        for i, f in enumerate(slots):
            fa = f"situation.free_slots[{i}]"
            if not isinstance(f, Mapping):
                p.append(f"{fa}: 객체가 아님")
                continue
            a, b = _dt(f.get("from")), _dt(f.get("to"))
            if a is None or b is None:
                p.append(f"{fa}: from·to 는 YYYY-MM-DDTHH:MM")
            elif not a < b:
                p.append(f"{fa}: from 이 to 보다 빨라야 함")
            if "inferred" in f and not isinstance(f["inferred"], bool):
                p.append(f"{fa}.inferred: boolean")
            if f.get("near") is not None and not isinstance(f["near"], str):
                p.append(f"{fa}.near: 문자열 또는 null")
    now = s.get("now")
    if now is not None:
        if not isinstance(now, Mapping):
            p.append("situation.now: 객체가 아님")
        else:
            if _dt(now.get("time")) is None:
                p.append("situation.now.time: YYYY-MM-DDTHH:MM")
            _latlng(now, "situation.now", p)
    party = s.get("party")
    if party is not None:
        if not isinstance(party, Mapping):
            p.append("situation.party: 객체가 아님")
        else:
            size = party.get("size")
            if isinstance(size, bool) or not isinstance(size, int) or size < 1:
                p.append("situation.party.size: 1 이상 정수")
            for k in ("kids", "mobility_limited", "luggage"):
                if k in party and not isinstance(party[k], bool):
                    p.append(f"situation.party.{k}: boolean")
    if s.get("language") not in LANGUAGES:
        p.append("situation.language: ko|en")
    interests = s.get("interests")
    if interests is not None and not (
        isinstance(interests, list) and all(isinstance(x, str) for x in interests)
    ):
        p.append("situation.interests: 문자열 배열")
    if "minimize_changes" in s and not isinstance(s["minimize_changes"], bool):
        p.append("situation.minimize_changes: boolean")
    w = s.get("weather")
    if w is not None:
        if not isinstance(w, Mapping):
            p.append("situation.weather: 객체가 아님")
        else:
            if "rain" in w and not isinstance(w["rain"], bool):
                p.append("situation.weather.rain: boolean")
            if w.get("temp_c") is not None and not is_number(w["temp_c"]):
                p.append("situation.weather.temp_c: 숫자")
    wr = s.get("walk_request")
    if wr is not None:
        if not isinstance(wr, Mapping):
            p.append("situation.walk_request: 객체가 아님")
        else:
            _place(wr.get("from"), "situation.walk_request.from", p)
            _place(wr.get("to"), "situation.walk_request.to", p)
            b = wr.get("budget_min")
            if b is not None and (not is_number(b) or b <= 0):
                p.append("situation.walk_request.budget_min: 양수 또는 null")
    return p
