import copy

from kc_catalog_helpers import NOW, obs, session

from domains.kcontext.catalog.fit import (
    FitConfig,
    add_to_itinerary,
    fit_event,
    remove_from_itinerary,
    validate_itinerary,
)
from domains.kcontext.catalog.merge import build_entries
from domains.kcontext.catalog.model import Reservation
from domains.kcontext.catalog.query import search_events
from domains.kcontext.catalog.routes import NullRouteProvider, TableRouteProvider
from domains.kcontext.catalog.rules import parse_eligibility

HOTEL = (37.5600, 126.9800)
A = (37.5650, 126.9900)       # 앞 일정 장소
V = (37.5700, 126.9950)       # 행사장
B = (37.5750, 127.0000)       # 뒤 일정 장소
TABLE = {(A, V): 10, (V, B): 12, (A, B): 15, (HOTEL, V): 20}


def event(*, sessions=None, lat=V[0], lng=V[1], **kw):
    o = obs("s:1", title="○○ 저녁 공연", sessions=sessions if sessions is not None else (
        session("2026-10-16", "19:00", "20:30"),), lat=lat, lng=lng, **kw)
    r = search_events(build_entries([o], now=NOW), {"trip": {"from": "2026-10-16", "to": "2026-10-16"}}, now=NOW)
    return r["events"][0]


def plan(id, start, end, loc, date="2026-10-16"):
    return {"id": id, "title": f"○○ {id}", "date": date, "start": start, "end": end,
            "lat": loc[0], "lng": loc[1]}


def fit(ev, itin, provider=None, **kw):
    return fit_event(ev, itin, provider or TableRouteProvider(TABLE), **kw)


def by_status(sug):
    return [s["status"] for s in sug]


# ---- 추가 이동시간 공식 -----------------------------------------------------------------------
def test_extra_travel_is_prev_to_event_plus_event_to_next_minus_prev_to_next():
    ev = event(eligibility=parse_eligibility("누구나 외국인 참여 가능"),
               reservation=Reservation(required="no"))
    (s,) = fit(ev, [plan("낮", "14:00", "17:00", A), plan("밤", "22:00", "23:00", B)])
    assert s["extra_minutes"] == 10 + 12 - 15 == 7 and s["extra_basis"] == "formula"
    assert s["after_item_id"] == "낮" and s["before_item_id"] == "밤"
    assert s["route"]["legs"] == {"prev_to_event": 10, "event_to_next": 12, "prev_to_next": 15}
    assert s["extra_status"] == "known" and s["status"] in ("fit", "check_needed")


def test_missing_route_makes_it_check_needed_not_a_guess():
    ev = event()
    (s,) = fit(ev, [plan("낮", "14:00", "17:00", A), plan("밤", "22:00", "23:00", B)],
               TableRouteProvider({(A, V): 10}))  # 나머지 구간을 모른다
    assert s["extra_minutes"] is None and s["extra_status"] == "needs_check"
    assert any(r["code"] == "travel_unknown" for r in s["reasons"]) and s["status"] == "check_needed"
    (n,) = fit(ev, [plan("낮", "14:00", "17:00", A)], NullRouteProvider())
    assert n["extra_minutes"] is None and n["route"]["provider"] == "none"


def test_straight_line_distance_is_never_used():
    ev = event()
    (s,) = fit(ev, [plan("낮", "14:00", "17:00", A), plan("밤", "22:00", "23:00", B)], NullRouteProvider())
    assert s["extra_minutes"] is None and all(v is None for v in s["route"]["legs"].values())


def test_extra_above_the_users_limit_is_not_a_fit():
    table = {(A, V): 30, (V, B): 30, (A, B): 10}  # 추가 50분
    (s,) = fit(event(), [plan("낮", "14:00", "17:00", A), plan("밤", "22:00", "23:00", B)],
               TableRouteProvider(table), cfg=FitConfig(max_extra_minutes=30))
    assert s["extra_minutes"] == 50 and s["status"] == "no_fit"
    assert any(r["code"] == "too_far" for r in s["reasons"])
    (ok,) = fit(event(), [plan("낮", "14:00", "17:00", A), plan("밤", "22:00", "23:00", B)],
                TableRouteProvider(table), cfg=FitConfig(max_extra_minutes=60))
    assert not any(r["code"] == "too_far" for r in ok["reasons"])


def test_formula_is_floored_at_zero():
    (s,) = fit(event(), [plan("낮", "14:00", "17:00", A), plan("밤", "22:00", "23:00", B)],
               TableRouteProvider({(A, V): 5, (V, B): 5, (A, B): 30}))
    assert s["extra_minutes"] == 0


def test_estimated_provider_values_are_flagged():
    prov = TableRouteProvider(TABLE, estimated=True, name="추정 공급자")
    (s,) = fit(event(), [plan("낮", "14:00", "17:00", A), plan("밤", "22:00", "23:00", B)], prov)
    assert s["route"]["estimated"] is True and s["route"]["provider"] == "추정 공급자"


# ---- 시간 겹침·여유 ---------------------------------------------------------------------------
def test_overlap_with_existing_plan_is_no_fit():
    (s,) = fit(event(), [plan("저녁식사", "18:30", "19:30", A)])
    assert s["status"] == "no_fit" and s["reasons"][0]["code"] == "overlaps"


def test_not_enough_time_to_travel_from_the_previous_plan():
    (s,) = fit(event(), [plan("낮", "17:00", "18:55", A)])  # 5분 여유, 이동 10분
    assert s["status"] == "no_fit" and any(r["code"] == "not_enough_time_before" for r in s["reasons"])


def test_not_enough_time_to_reach_the_next_plan():
    (s,) = fit(event(), [plan("낮", "14:00", "17:00", A), plan("밤", "20:35", "22:00", B)])  # 5분, 이동 12분
    assert s["status"] == "no_fit" and any(r["code"] == "not_enough_time_after" for r in s["reasons"])


def test_free_slots_limit_the_window():
    ev = event()
    slots = [{"date": "2026-10-16", "from": "18:00", "to": "20:00"}]
    (s,) = fit(ev, [plan("낮", "10:00", "12:00", A)], free_slots=slots)
    assert s["status"] == "no_fit" and s["reasons"][0]["code"] == "outside_free_slot"
    ok = fit(ev, [plan("낮", "10:00", "12:00", A)], free_slots=[{"date": "2026-10-16", "from": "18:00", "to": "21:00"}])
    assert not any(r["code"] == "outside_free_slot" for r in ok[0]["reasons"])


def test_unknown_session_end_needs_a_duration_from_the_user():
    ev = event(sessions=(session("2026-10-16", "19:00", None),))
    (s,) = fit(ev, [plan("낮", "10:00", "12:00", A)])
    assert s["status"] == "check_needed" and any(r["code"] == "duration_unknown" for r in s["reasons"])
    (t,) = fit(ev, [plan("낮", "10:00", "12:00", A)], cfg=FitConfig(assumed_duration_min=90))
    assert t["session"]["assumed_end"] is True and not any(r["code"] == "duration_unknown" for r in t["reasons"])


def test_events_without_confirmed_sessions_give_no_suggestions():
    o = obs("s:1", title="○○ 기간만", start="2026-10-14", end="2026-10-20", lat=V[0], lng=V[1])
    r = search_events(build_entries([o], now=NOW), {"trip": {"from": "2026-10-16", "to": "2026-10-16"}}, now=NOW)
    assert fit(r["events"][0], [plan("낮", "10:00", "12:00", A)]) == []


# ---- 출발 위치·한쪽 일정 ----------------------------------------------------------------------
def test_origin_is_used_only_when_there_is_no_previous_plan():
    (s,) = fit(event(), [], origin={"lat": HOTEL[0], "lng": HOTEL[1]})
    assert s["extra_basis"] == "origin_leg" and s["extra_minutes"] == 20 and s["route"]["from"] == "origin"
    (n,) = fit(event(), [])
    assert n["extra_basis"] == "none" and n["extra_minutes"] is None
    assert any(r["code"] == "no_reference" for r in n["reasons"])


def test_only_a_previous_plan_counts_the_leg_only():
    (s,) = fit(event(), [plan("낮", "14:00", "17:00", A)])
    assert s["extra_basis"] == "one_side_leg" and s["extra_minutes"] == 10


# ---- 예약·참여·검증 ---------------------------------------------------------------------------
def test_reservation_closed_and_participation_restricted_are_not_fits():
    closed = event(reservation=Reservation(required="yes", deadline="2026-10-06"))
    (s,) = fit(closed, [plan("낮", "10:00", "12:00", A)])
    assert s["status"] == "no_fit" and any(r["code"] == "reservation_unavailable" for r in s["reasons"])
    restricted = event(eligibility=parse_eligibility("중구민"))
    (t,) = fit(restricted, [plan("낮", "10:00", "12:00", A)])
    assert t["status"] == "no_fit" and any(r["code"] == "not_eligible" for r in t["reasons"])


def test_fit_requires_verified_known_conditions():
    full = event(eligibility=parse_eligibility("누구나 외국인 참여 가능"), reservation=Reservation(required="no"))
    (s,) = fit(full, [plan("낮", "14:00", "17:00", A), plan("밤", "22:00", "23:00", B)])
    assert s["status"] == "fit"
    unknown_res = event(eligibility=parse_eligibility("누구나"))
    (t,) = fit(unknown_res, [plan("낮", "14:00", "17:00", A), plan("밤", "22:00", "23:00", B)])
    assert t["status"] == "check_needed"
    assert {r["code"] for r in t["reasons"]} >= {"reservation_unknown"}


def test_reservation_required_is_surfaced_with_link():
    ev = event(eligibility=parse_eligibility("누구나"),
               reservation=Reservation(required="yes", link="https://example.invalid/r", status="open"))
    (s,) = fit(ev, [plan("낮", "14:00", "17:00", A), plan("밤", "22:00", "23:00", B)])
    assert any(r["code"] == "reservation_required" for r in s["reasons"])
    assert s["reservation"]["link"] == "https://example.invalid/r"


# ---- 일정 추가·취소 ---------------------------------------------------------------------------
def test_add_and_cancel_keep_the_existing_itinerary():
    ev = event(eligibility=parse_eligibility("누구나"), reservation=Reservation(required="no"))
    itin = [plan("낮", "14:00", "17:00", A), plan("밤", "22:00", "23:00", B)]
    snapshot = copy.deepcopy(itin)
    (s,) = fit(ev, itin)
    added = add_to_itinerary(itin, s, ev)
    assert itin == snapshot and [i["id"] for i in added][1].startswith("evt:") and len(added) == 3
    assert [i["id"] for i in added] == ["낮", added[1]["id"], "밤"]
    assert add_to_itinerary(added, s, ev) == added  # 같은 제안은 한 번만
    back = remove_from_itinerary(added, added[1]["id"])
    assert [i["id"] for i in back] == ["낮", "밤"]
    assert remove_from_itinerary(added, "낮") == added  # 기존 일정은 이 경로로 지우지 않는다


def test_end_time_is_flagged_when_assumed_on_add():
    ev = event(sessions=(session("2026-10-16", "19:00", None),))
    (s,) = fit(ev, [plan("낮", "10:00", "12:00", A)], cfg=FitConfig(assumed_duration_min=90))
    item = add_to_itinerary([plan("낮", "10:00", "12:00", A)], s, ev)[1]
    assert item["end_assumed"] is True and item["start"] == "19:00" and item["end"] > "19:00"


def test_invalid_itinerary_items_are_dropped_with_reasons():
    good, problems = validate_itinerary([plan("낮", "10:00", "12:00", A), {"id": "x"}, "문자열",
                                         plan("거꾸로", "12:00", "10:00", A)])
    assert [g["id"] for g in good] == ["낮"] and len(problems) == 3
