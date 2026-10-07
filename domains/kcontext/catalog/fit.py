"""기존 일정에 행사를 끼워 넣을 수 있는지 판단한다. 시간·거리 계산은 코드가, 설명 문장은 이 결과를 근거로 만든다.

추가 이동시간 = (앞 일정 → 행사) + (행사 → 뒤 일정) − (앞 일정 → 뒤 일정)
같은 ``RouteProvider``(같은 교통수단)로 세 값을 모두 구한다. 하나라도 얻지 못하면 ``extra_minutes`` 는 None 이고
"이동시간 확인 필요"로 표시한다. 직선거리로 대신하지 않는다.

앞 또는 뒤 일정이 없을 때: 앞이 없으면 출발 위치(숙소)를 앞으로 쓰고(``extra_basis="origin_leg"``),
뒤가 없으면 앞 → 행사 이동만 센다(``"one_side_leg"``). 둘 다 없고 출발 위치도 없으면 계산하지 않는다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from domains.kcontext.contract.text import is_date, is_hhmm

from .routes import LatLng, RouteProvider

__all__ = ["FitConfig", "add_to_itinerary", "fit_event", "remove_from_itinerary", "validate_itinerary"]


@dataclass(frozen=True)
class FitConfig:
    max_extra_minutes: int = 30  # 사용자가 허용한 추가 이동시간
    assumed_duration_min: int | None = None  # 회차 종료 시각을 모를 때 사용자가 정한 소요 시간(없으면 확인 필요)


def _m(hhmm: str) -> int:
    return int(hhmm[:2]) * 60 + int(hhmm[3:5])


def _coord(o: Mapping) -> LatLng | None:
    a, b = o.get("lat"), o.get("lng")
    ok = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (a, b))
    return (float(a), float(b)) if ok else None  # type: ignore[arg-type]


def validate_itinerary(items: Sequence[Mapping]) -> tuple[list[dict], list[str]]:
    """일정 항목 검증. 형식이 틀린 항목은 버리고 이유를 돌려준다."""
    good: list[dict] = []
    problems: list[str] = []
    for i, it in enumerate(items):
        if not isinstance(it, Mapping):
            problems.append(f"itinerary[{i}]: 객체가 아님")
            continue
        if not (isinstance(it.get("id"), str) and it["id"] and is_date(it.get("date"))
                and is_hhmm(it.get("start")) and is_hhmm(it.get("end"))
                and _m(it["start"]) < _m(it["end"])):
            problems.append(f"itinerary[{i}]: id·date·start·end(HH:MM, start<end) 필요")
            continue
        good.append(dict(it))
    return sorted(good, key=lambda x: (x["date"], x["start"])), problems


def _reason(code: str, ko: str, en: str, **kw) -> dict:
    return {"code": code, "ko": ko, "en": en, **kw}


def _leg(provider: RouteProvider, a: LatLng | None, b: LatLng | None) -> int | None:
    return provider.minutes(a, b) if a is not None and b is not None else None


def fit_event(
    event: Mapping, itinerary: Sequence[Mapping], provider: RouteProvider, *, cfg: FitConfig = FitConfig(),  # noqa: B008
    origin: Mapping | None = None, free_slots: Sequence[Mapping] = (),
) -> list[dict]:
    """``search_events`` 가 돌려준 행사 하나 → 회차별 제안. 회차가 확인된 날짜만 다룬다."""
    items, _ = validate_itinerary(itinerary)
    # 이미 일정에 넣은 이 행사 자신은 겹침·앞뒤 일정 계산에서 뺀다(자기 자신과 겹치는 것으로 보지 않게)
    items = [i for i in items if not (i.get("source") == "catalog" and i.get("entry_id") == event["id"])]
    venue = _coord(event["venue"])
    org = _coord(origin) if origin else None
    out: list[dict] = []
    part = event["participation"]
    res_status = event["reservation"]["status"]
    for day in event["matching_dates"]:
        if day["state"] != "yes":
            continue
        for s in day["sessions"]:
            if not is_hhmm(s.get("start_time")):
                continue
            start = _m(s["start_time"])
            if is_hhmm(s.get("end_time")) and _m(s["end_time"]) > start:
                end, dur_known = _m(s["end_time"]), True
            elif cfg.assumed_duration_min:
                end, dur_known = start + cfg.assumed_duration_min, True
            else:
                end, dur_known = start, False
            reasons: list[dict] = []
            status = "fit"
            if not dur_known:
                status = "check_needed"
                reasons.append(_reason("duration_unknown", "소요 시간을 알 수 없어 일정 겹침을 확인하지 못함",
                                       "Duration unknown, so overlap with your plans cannot be checked"))
            same_day = [i for i in items if i["date"] == day["date"]]
            if dur_known:
                clash = [i for i in same_day if _m(i["start"]) < end and start < _m(i["end"])]
            else:  # 끝을 모르면 행사 시작 시각에 이미 진행 중이거나 같은 시각에 시작하는 일정만 겹침으로 본다
                clash = [i for i in same_day if _m(i["start"]) <= start < _m(i["end"])]
            prev = max((i for i in same_day if _m(i["end"]) <= start), key=lambda i: _m(i["end"]),
                       default=None)
            nxt = min((i for i in same_day if _m(i["start"]) >= end and i not in clash),
                      key=lambda i: _m(i["start"]), default=None)
            if clash:
                status = "no_fit"
                reasons.append(_reason("overlaps", f"기존 일정 '{clash[0].get('title', clash[0]['id'])}'과 겹침",
                                       f"Overlaps your plan '{clash[0].get('title', clash[0]['id'])}'",
                                       item_id=clash[0]["id"]))
            slots = [x for x in free_slots if x.get("date") == day["date"]
                     and is_hhmm(x.get("from")) and is_hhmm(x.get("to"))]
            if free_slots and dur_known and not any(_m(x["from"]) <= start and end <= _m(x["to"])
                                                    for x in slots):
                status = "no_fit"
                reasons.append(_reason("outside_free_slot", "비어 있는 시간 밖에 있음",
                                       "Falls outside your free time"))
            # 이동시간 (같은 provider 로 세 값)
            if prev is not None:
                before_c = _coord(prev)
                basis_prev = "item"
            elif org is not None:
                before_c, basis_prev = org, "origin"
            else:
                before_c, basis_prev = None, "none"
            nxt_c = _coord(nxt) if nxt is not None else None
            a = _leg(provider, before_c, venue)
            b = _leg(provider, venue, nxt_c)
            c = _leg(provider, before_c, nxt_c)
            extra: int | None = None
            has_before = prev is not None or basis_prev == "origin"
            if has_before and nxt is not None:
                basis = "formula"  # 앞(앞 일정 또는 출발 위치) → 행사 → 뒤 − 앞 → 뒤
                if None not in (a, b, c):
                    extra = max(a + b - c, 0)  # type: ignore[operator]
            elif has_before:
                basis = "one_side_leg" if prev is not None else "origin_leg"
                extra = a
            else:
                basis = "none"
            need_known = ([a] if has_before else []) + ([b] if nxt is not None else []) + (
                [c] if has_before and nxt is not None else [])
            if None in need_known:
                if status == "fit":
                    status = "check_needed"
                reasons.append(_reason("travel_unknown", "이동시간 확인 필요",
                                       "Travel time needs checking"))
            if basis == "none":
                if status == "fit":
                    status = "check_needed"
                if nxt is not None:
                    reasons.append(_reason("no_before_reference", "앞 일정과 출발 위치가 없어 뒤 일정까지의 이동만 확인함",
                                           "No earlier plan or starting point; only the trip to the next plan was checked"))
                else:
                    reasons.append(_reason("no_reference", "비교할 앞뒤 일정과 출발 위치가 없어 이동시간을 계산하지 않음",
                                           "No neighboring plan or starting point to compute travel from"))
            if status == "fit" and cfg.assumed_duration_min and not (is_hhmm(s.get("end_time")) and _m(s["end_time"]) > start):
                reasons.append(_reason("duration_assumed", f"종료 시각을 모르는 회차 — 사용자가 정한 {cfg.assumed_duration_min}분으로 계산함",
                                       f"The session end is unknown; calculated with your {cfg.assumed_duration_min} min"))
            if a is not None and prev is not None and start - _m(prev["end"]) < a:
                status = "no_fit"
                reasons.append(_reason("not_enough_time_before", "앞 일정에서 이동할 시간이 부족함",
                                       "Not enough time to travel from the previous plan", needed=a))
            if b is not None and nxt is not None and _m(nxt["start"]) - end < b and dur_known:
                status = "no_fit"
                reasons.append(_reason("not_enough_time_after", "뒤 일정까지 이동할 시간이 부족함",
                                       "Not enough time to reach the next plan", needed=b))
            if extra is not None and extra > cfg.max_extra_minutes:
                status = "no_fit"
                reasons.append(_reason("too_far", f"추가 이동시간 {extra}분이 허용({cfg.max_extra_minutes}분)을 넘음",
                                       f"Extra travel {extra} min exceeds your limit ({cfg.max_extra_minutes} min)",
                                       extra=extra))
            # 참여·예약·검증
            if part["status"] == "restricted":
                status = "no_fit"
                reasons.append(_reason("not_eligible", "참여 제한: " + "; ".join(part["reasons"]),
                                       "Participation is restricted"))
            elif part["status"] == "unverified" and status == "fit":
                status = "check_needed"
                reasons.append(_reason("eligibility_unverified", "참여조건 확인 필요", "Eligibility needs checking"))
            if res_status in ("closed", "full"):
                status = "no_fit"
                reasons.append(_reason("reservation_unavailable", "예약이 마감됨", "Reservation is closed"))
            elif event["reservation"]["required"] == "yes" and status == "fit":
                reasons.append(_reason("reservation_required", "예약이 필요함", "Reservation required"))
            elif event["reservation"]["required"] == "unknown" and status == "fit":
                status = "check_needed"
                reasons.append(_reason("reservation_unknown", "예약 필요 여부 확인 필요",
                                       "Whether a reservation is required needs checking"))
            if event["verification"] != "verified" and status == "fit":
                status = "check_needed"
                reasons.append(_reason("not_verified", "정보 검증이 끝나지 않음", "Information is not fully verified"))
            out.append({
                "entry_id": event["id"], "title": event["title"], "date": day["date"],
                "session": {"start_time": s["start_time"], "end_time": s.get("end_time"),
                            "assumed_end": not (is_hhmm(s.get("end_time")) and _m(s["end_time"]) > start),
                            "assumed_minutes": (cfg.assumed_duration_min if not (
                                is_hhmm(s.get("end_time")) and _m(s["end_time"]) > start) else None)},
                "after_item_id": prev["id"] if prev else None,
                "before_item_id": nxt["id"] if nxt else None,
                "extra_minutes": extra, "extra_basis": basis,
                "extra_status": "known" if extra is not None else "needs_check",
                "route": {"provider": provider.name, "mode": provider.mode, "estimated": provider.estimated,
                          "legs": {"prev_to_event": a, "event_to_next": b, "prev_to_next": c},
                          "from": basis_prev},
                "status": status, "reasons": reasons,
                "reservation": event["reservation"], "participation": part,
                "verification": event["verification"], "last_verified_at": event["last_verified_at"],
                "links": event["links"],
            })
    return out


def add_to_itinerary(itinerary: Sequence[Mapping], suggestion: Mapping, event: Mapping) -> list[dict]:
    """제안을 일정에 추가한다. 같은 제안은 두 번 들어가지 않는다. 입력 일정은 바꾸지 않는다."""
    items, _ = validate_itinerary(itinerary)
    s = suggestion["session"]
    item_id = f"evt:{suggestion['entry_id']}:{suggestion['date']}:{s['start_time']}"
    if any(i["id"] == item_id for i in items):
        return items
    start = _m(s["start_time"])
    if is_hhmm(s.get("end_time")) and _m(s["end_time"]) > start:
        end_min = _m(s["end_time"])
    else:  # 끝을 모르면 사용자가 정한 소요 시간, 없으면 60분으로 두고 end_assumed 로 표시한다
        end_min = start + int(s.get("assumed_minutes") or 60)
    end_min = min(end_min, 23 * 60 + 59)
    if end_min <= start:
        raise ValueError("종료 시각을 정할 수 없어 일정에 추가하지 못한다")
    end = f"{end_min // 60:02d}:{end_min % 60:02d}"
    new = {"id": item_id, "title": event["title"], "date": suggestion["date"], "start": s["start_time"],
           "end": end, "lat": event["venue"]["lat"], "lng": event["venue"]["lng"],
           "source": "catalog", "entry_id": suggestion["entry_id"],
           "end_assumed": bool(s.get("assumed_end") or not s.get("end_time"))}
    return sorted([*items, new], key=lambda x: (x["date"], x["start"]))


def remove_from_itinerary(itinerary: Sequence[Mapping], item_id: str) -> list[dict]:
    """추가한 행사를 일정에서 뺀다(원래 일정도 id 로 뺄 수 있지만 catalog 항목만 허용한다)."""
    items, _ = validate_itinerary(itinerary)
    return [i for i in items if not (i["id"] == item_id and i.get("source") == "catalog")]
