"""사용자 입력(여행 날짜·위치·관심사)에 맞는 행사 목록과 지도 점. 날짜·시간은 Asia/Seoul 기준으로 코드가 계산한다.

원칙
- 대상 지역에서 열리는 것으로 **확인된** 행사만 목록에 올린다. 장소 미확인은 관리자 검토 목록으로 간다.
- 취소·종료된 행사는 목록에서 빼고 ``excluded`` 에 이유와 함께 남긴다(휴무일뿐인 경우 포함).
- 참여조건이 확인되지 않은 행사를 참여 가능으로 확정하지 않는다: ``participation.status`` 는
  ``restricted``(제한 이유 표시) · ``stated_open``(출처가 "누구나"라고 적음) · ``unverified``(확인 필요) 셋뿐이다.
- 전체 행사 수를 입증할 수 없으므로 응답에 ``coverage`` 로 수집 출처와 마지막 확인 시각을 싣고,
  ``complete=False`` 로 "모든 행사"가 아님을 밝힌다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta

from domains.kcontext.contract.text import is_date

from .model import EventEntry
from .rules import date_range_days, event_lifecycle, is_operating_day, norm_text, to_kst

__all__ = ["participation", "search_events", "summarize_entry"]

STALE_HOURS = 72
_AVAIL_ORDER = {"session_match": 0, "date_range_unconfirmed": 1, "postponed": 2}


def participation(e: EventEntry) -> dict:
    """참여 가능 여부 표시. 확인되지 않은 것을 가능으로 확정하지 않는다.

    거주·외국인·대상(회원 등) 제한이 있으면 ``restricted``. 연령 조건만 있으면 제한으로 단정하지 않고(관광객이
    해당될 수 있다) ``unverified`` 에 조건을 보여 준다.
    """
    el = e.eligibility
    hard = [r for r in el.restrictions if r.get("kind") in ("resident", "foreigner", "other")]
    ages = [r for r in el.restrictions if r.get("kind") == "age"]
    if el.foreigner == "excluded" or el.resident_only == "yes" or hard:
        reasons = [r["reason"] for r in hard] or ["참여 제한이 있다"]
        return {"status": "restricted", "reasons": reasons, "foreigner": el.foreigner,
                "needs_check": False}
    if ages:
        return {"status": "unverified", "reasons": [r["reason"] for r in ages] + ["해당되는지 확인 필요"],
                "foreigner": el.foreigner, "needs_check": True}
    if el.stated_open == "yes":
        return {"status": "stated_open", "reasons": ["출처가 누구나 참여할 수 있다고 적음"],
                "foreigner": el.foreigner, "needs_check": el.foreigner == "unknown"}
    return {"status": "unverified", "reasons": ["참여조건이 확인되지 않음 — 원문 확인 필요"],
            "foreigner": el.foreigner, "needs_check": True}


def _links(e: EventEntry) -> list[dict]:
    seen: dict[str, dict] = {}
    for ev in e.evidence:
        if ev.url:
            seen.setdefault(ev.url, {"url": ev.url, "source_name": ev.source_name, "kind": ev.kind,
                                     "quote": ev.quote, "published_at": ev.published_at,
                                     "ai_extracted": ev.ai_extracted, "location": ev.location})
    return list(seen.values())


def summarize_entry(e: EventEntry, now: datetime) -> dict:
    """화면·API 용 요약. 알 수 없는 값은 null·"unknown" 그대로 둔다(문구는 화면이 '확인 필요'로 바꾼다)."""
    return {
        "id": e.id, "title": e.title, "title_en": e.title_en, "description": e.description,
        "event_type": e.event_type, "organizer": e.organizer, "operator": e.operator,
        "venue": {"name": e.venue.name, "address": e.venue.address, "lat": e.venue.lat,
                  "lng": e.venue.lng, "district": e.venue.district, "in_target": e.venue.in_target},
        "schedule": {
            "start_date": e.schedule.start_date, "end_date": e.schedule.end_date,
            "sessions": [{"date": s.date, "start_time": s.start_time, "end_time": s.end_time,
                          "venue_name": s.venue_name, "in_target": s.in_target, "note": s.note}
                         for s in e.schedule.sessions],
            "weekly_closed_days": list(e.schedule.weekly_closed_days),
            "closed_dates": list(e.schedule.closed_dates), "holiday_rule": e.schedule.holiday_rule,
            "entry_cutoff": e.schedule.entry_cutoff, "hours_text": e.schedule.hours_text,
            "timezone": e.schedule.timezone,
        },
        "price": {"kind": e.price.kind, "text": e.price.text},
        "reservation": {"required": e.reservation.required, "link": e.reservation.link,
                        "deadline": e.reservation.deadline, "status": event_reservation(e, now),
                        "note": e.reservation.note},
        "eligibility": {"audience": e.eligibility.audience, "age_limit": e.eligibility.age_limit,
                        "resident_only": e.eligibility.resident_only,
                        "foreigner": e.eligibility.foreigner,
                        "restrictions": [dict(r) for r in e.eligibility.restrictions]},
        "participation": participation(e),
        "language": {"languages": list(e.language.languages),
                     "english_guidance": e.language.english_guidance,
                     "english_subtitles": e.language.english_subtitles,
                     "site_english_page": e.language.site_english_page},
        "lifecycle": event_lifecycle(e, now), "verification": e.verification,
        "needs_check": list(e.needs_check), "conflicts": [dict(c) for c in e.conflicts],
        "independent_sources": e.independent_sources, "links": _links(e),
        "published_at": e.published_at, "modified_at": e.modified_at, "collected_at": e.collected_at,
        "last_verified_at": e.last_verified_at, "demo": e.demo,
        # 출처가 마지막으로 확인된 지 STALE_HOURS 가 지났다 = 목록에서 빠졌거나 수집이 멈췄을 수 있다(취소는 아니다)
        "stale": bool(e.last_verified_at) and e.last_verified_at < (to_kst(now) - timedelta(hours=STALE_HOURS)
                                                                    ).strftime("%Y-%m-%dT%H:%M"),
    }


def event_reservation(e: EventEntry, now: datetime) -> str:
    from .rules import reservation_status

    return reservation_status(e.reservation, now)


def _matching_dates(e: EventEntry, trip_days: list[date]) -> list[dict]:
    out = []
    event_days = set(date_range_days(e.schedule.start_date, e.schedule.end_date))
    event_days |= {date.fromisoformat(s.date) for s in e.schedule.sessions}
    for d in trip_days:
        if event_days and d not in event_days:
            continue
        state, why = is_operating_day(e.schedule, d)
        if state == "no":
            out.append({"date": d.isoformat(), "state": "no", "reason": why, "sessions": []})
            continue
        sess = [{"start_time": s.start_time, "end_time": s.end_time, "venue_name": s.venue_name,
                 "in_target": s.in_target} for s in e.schedule.sessions if s.date == d.isoformat()
                and s.in_target != "no"]
        out.append({"date": d.isoformat(), "state": state, "reason": why, "sessions": sess})
    return out


def _interest_hits(e: EventEntry, interests: Sequence[str]) -> list[str]:
    hay = norm_text(f"{e.title} {e.title_en} {e.event_type} {e.description}").casefold()
    return [t for t in interests if t.strip() and t.strip().casefold() in hay]


def search_events(
    entries: Sequence[EventEntry], request: Mapping, *, now: datetime,
    coverage: Mapping | None = None,
) -> dict:
    """요청: ``trip{from,to}`` · ``interests[]`` · ``origin{name,lat,lng}`` · ``require_interest`` · ``include_demo``."""
    now = to_kst(now)
    trip = request.get("trip") or {}
    problems: list[str] = []
    trip_days: list[date] = []
    if is_date(trip.get("from")) and is_date(trip.get("to")) and trip["from"] <= trip["to"]:
        trip_days = date_range_days(trip["from"], trip["to"])
    else:
        problems.append("trip.from·trip.to 는 YYYY-MM-DD 이고 from <= to 여야 한다")
    interests = [str(x) for x in (request.get("interests") or []) if isinstance(x, str)]
    include_demo = bool(request.get("include_demo"))
    results: list[dict] = []
    excluded: list[dict] = []
    for e in entries:
        if e.demo and not include_demo:
            continue
        s = summarize_entry(e, now)

        def drop(reason: str, entry: EventEntry = e) -> None:
            excluded.append({"id": entry.id, "title": entry.title, "reason": reason})

        if e.venue.in_target != "yes":
            drop("대상 지역에서 열리는지 확인되지 않음" if e.venue.in_target == "unknown"
                 else "대상 지역 밖에서 열림")
            continue
        if s["lifecycle"] == "cancelled":
            drop("취소됨")
            continue
        if s["lifecycle"] == "ended":
            drop("종료됨")
            continue
        if not trip_days:
            drop("여행 날짜가 올바르지 않음")
            continue
        dates = _matching_dates(e, trip_days)
        if not dates:
            drop("여행 날짜에 열리지 않음")
            continue
        if all(d["state"] == "no" for d in dates):
            drop("여행 날짜가 휴무일(" + ", ".join(sorted({d["reason"] for d in dates})) + ")")
            continue
        hits = _interest_hits(e, interests)
        if interests and request.get("require_interest") and not hits:
            drop("관심사와 맞지 않음")
            continue
        if s["lifecycle"] == "postponed":
            avail = "postponed"
        elif any(d["state"] == "yes" for d in dates):
            avail = "session_match"
        else:
            avail = "date_range_unconfirmed"
        s.update({"availability": avail, "matching_dates": dates, "interest_match": hits})
        results.append(s)
    results.sort(key=lambda r: (_AVAIL_ORDER[r["availability"]], -len(r["interest_match"]),
                                r["schedule"]["start_date"] or "9999", r["id"]))
    origin = request.get("origin") if isinstance(request.get("origin"), Mapping) else None
    points = [{"id": r["id"], "title": r["title"], "lat": r["venue"]["lat"], "lng": r["venue"]["lng"],
               "availability": r["availability"], "participation": r["participation"]["status"]}
              for r in results if r["venue"]["lat"] is not None]
    cov = dict(coverage or {})
    cov.update({"complete": False,
                "note": "수집한 출처에서 확인된 행사만 보여 준다 — 지역의 모든 행사가 아니다"})
    return {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M"), "timezone": "Asia/Seoul",
        "events": results, "excluded": excluded, "problems": problems, "coverage": cov,
        "map": {"origin": dict(origin) if origin else None, "points": points,
                "unlocated": [r["id"] for r in results if r["venue"]["lat"] is None]},
        "counts": {"events": len(results), "excluded": len(excluded)},
    }
