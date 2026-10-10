import dataclasses
from datetime import UTC, datetime, timedelta

from kc_catalog_helpers import NOW, obs, session

from domains.kcontext.catalog.merge import build_entries
from domains.kcontext.catalog.model import Reservation
from domains.kcontext.catalog.query import search_events
from domains.kcontext.catalog.rules import parse_eligibility

TRIP = {"from": "2026-10-15", "to": "2026-10-18"}


def entries(*o):
    return build_entries(list(o), now=NOW)


def search(*o, trip=TRIP, now=NOW, **req):
    return search_events(entries(*o), {"trip": trip, **req}, now=now)


def ids(r):
    return [e["title"] for e in r["events"]]


def why(r):
    return {x["title"]: x["reason"] for x in r["excluded"]}


# ---- 중구 포함 여부: 개최 장소 기준 ----------------------------------------------------------
def test_venues_outside_the_target_region_are_excluded_with_a_reason():
    r = search(obs("s:1", title="○○ 안쪽"), obs("s:2", title="○○ 바깥", in_target="no", venue_name="△△"))
    assert ids(r) == ["○○ 안쪽"] and why(r)["○○ 바깥"] == "대상 지역 밖에서 열림"


def test_unknown_venue_region_is_not_listed_but_is_explained():
    r = search(obs("s:1", title="○○ 미확인", in_target="unknown"))
    assert r["events"] == [] and "확인되지 않음" in why(r)["○○ 미확인"]


def test_organizer_name_does_not_include_an_event():
    r = search(obs("s:1", title="○○ 주최만", in_target="no", organizer="중구청"))
    assert r["events"] == []  # 주최 기관 이름에 지역이 있어도 장소가 밖이면 제외


def test_multi_venue_event_keeps_only_sessions_in_the_target_region():
    o = obs("s:1", sessions=(session("2026-10-16", venue="○○ 홀", in_target="yes"),
                             session("2026-10-17", venue="△△ 극장", in_target="no")))
    r = search(o)
    days = {d["date"]: d for d in r["events"][0]["matching_dates"]}
    assert len(days["2026-10-16"]["sessions"]) == 1
    assert days["2026-10-17"]["sessions"] == []  # 중구 밖 회차는 회차로 세지 않는다


# ---- 날짜·회차·휴무 ---------------------------------------------------------------------------
def test_session_match_vs_range_only():
    r = search(obs("s:1", title="○○ 회차 확인", sessions=(session("2026-10-16"),)),
               obs("s:2", title="○○ 기간만", venue_name="△△ 극장", start="2026-10-14", end="2026-10-20"))
    by = {e["title"]: e for e in r["events"]}
    assert by["○○ 회차 확인"]["availability"] == "session_match"
    assert by["○○ 기간만"]["availability"] == "date_range_unconfirmed"
    assert ids(r)[0] == "○○ 회차 확인"  # 회차가 확인된 것이 먼저


def test_events_outside_trip_dates_are_excluded():
    r = search(obs("s:1", title="○○ 전", start="2026-10-01", end="2026-10-10"),
               obs("s:2", title="○○ 후", venue_name="△△", start="2026-10-25", end="2026-10-26"))
    assert r["events"] == []
    assert set(why(r).values()) <= {"여행 날짜에 열리지 않음", "종료됨"}


def test_closed_days_are_respected():
    import dataclasses

    base = obs("s:1", title="○○ 상설", start="2026-10-01", end="2026-10-31")
    closed = dataclasses.replace(base, schedule=dataclasses.replace(
        base.schedule, weekly_closed_days=(0,), closed_dates=("2026-10-16",)))
    r = search(closed, trip={"from": "2026-10-15", "to": "2026-10-19"})
    states = {d["date"]: d["state"] for d in r["events"][0]["matching_dates"]}
    assert states["2026-10-16"] == "no" and states["2026-10-19"] == "no"  # 임시 휴무·월요일
    assert states["2026-10-15"] == "unknown" and states["2026-10-17"] == "unknown"


def test_trip_only_on_closed_days_is_excluded_with_the_reason():
    import dataclasses

    base = obs("s:1", title="○○ 상설", start="2026-10-01", end="2026-10-31")
    closed = dataclasses.replace(base, schedule=dataclasses.replace(base.schedule, weekly_closed_days=(0,)))
    r = search(closed, trip={"from": "2026-10-19", "to": "2026-10-19"})  # 월요일
    assert r["events"] == [] and "휴무" in why(r)["○○ 상설"]


def test_cancelled_and_ended_are_excluded():
    base = obs("s:1", title="○○ 취소", external_ids=("k",), lifecycle="cancelled", kind="official_site")
    r = search(base, obs("s:2", title="○○ 지난 행사", venue_name="△△", start="2026-10-01", end="2026-10-05"),
               trip={"from": "2026-10-01", "to": "2026-10-18"})
    assert r["events"] == [] and why(r)["○○ 취소"] == "취소됨" and why(r)["○○ 지난 행사"] == "종료됨"


def test_postponed_is_listed_but_not_as_available():
    o = obs("s:1", title="○○ 연기", lifecycle="postponed", kind="official_site")
    r = search(o)
    assert r["events"][0]["availability"] == "postponed"


def test_seoul_time_boundary_decides_ended():
    ev_ = obs("s:1", title="○○ 오늘까지", start="2026-10-07", end="2026-10-07")
    utc_late = datetime(2026, 10, 7, 14, 30, tzinfo=UTC)  # 서울 23:30
    assert ids(search(ev_, trip={"from": "2026-10-07", "to": "2026-10-08"}, now=utc_late)) == ["○○ 오늘까지"]
    next_day = utc_late + timedelta(hours=1)  # 서울 10-08 00:30
    assert search(ev_, trip={"from": "2026-10-07", "to": "2026-10-08"}, now=next_day)["events"] == []


def test_bad_trip_is_reported_not_crashed():
    r = search(obs("s:1"), trip={"from": "2026-10-19", "to": "2026-10-15"})
    assert r["events"] == [] and r["problems"]
    assert search(obs("s:1"), trip={})["problems"]


# ---- 참여조건 ---------------------------------------------------------------------------------
def test_participation_is_never_assumed_open():
    r = search(obs("s:1", title="○○ 미확인"),
               obs("s:2", title="○○ 누구나", venue_name="△△", eligibility=parse_eligibility("누구나")),
               obs("s:3", title="○○ 주민 전용", venue_name="□□", eligibility=parse_eligibility("중구민")),
               obs("s:4", title="○○ 외국인 제외", venue_name="▽▽", eligibility=parse_eligibility("외국인 제외")))
    st = {e["title"]: e["participation"] for e in r["events"]}
    assert st["○○ 미확인"]["status"] == "unverified" and st["○○ 미확인"]["needs_check"] is True
    assert st["○○ 누구나"]["status"] == "stated_open" and st["○○ 누구나"]["foreigner"] == "unknown"
    assert st["○○ 주민 전용"]["status"] == "restricted" and "거주" in st["○○ 주민 전용"]["reasons"][0]
    assert st["○○ 외국인 제외"]["status"] == "restricted"


def test_restricted_events_are_still_listed_with_the_reason():
    r = search(obs("s:1", eligibility=parse_eligibility("중구민")))
    assert r["events"][0]["participation"]["reasons"]


# ---- 데모·범위·지도·관심사 --------------------------------------------------------------------
def test_demo_events_are_hidden_unless_requested():
    d = obs("d:1", title="○○ 데모", demo=True)
    assert search(d)["events"] == []
    shown = search(d, include_demo=True)["events"]
    assert shown[0]["demo"] is True


def test_response_never_claims_to_be_complete_and_lists_coverage():
    r = search_events(entries(obs("s:1")), {"trip": TRIP}, now=NOW,
                      coverage={"sources": [{"id": "seoul_openapi", "last_success_at": "2026-10-07T12:00"}]})
    assert r["coverage"]["complete"] is False and "모든 행사가 아니다" in r["coverage"]["note"]
    assert r["coverage"]["sources"][0]["last_success_at"] == "2026-10-07T12:00"
    assert r["timezone"] == "Asia/Seoul"


def test_map_points_and_unlocated():
    r = search(obs("s:1", title="○○ 좌표 있음", lat=37.56, lng=126.99),
               obs("s:2", title="○○ 좌표 없음", venue_name="△△"),
               origin={"name": "○○ 호텔", "lat": 37.55, "lng": 126.98})
    assert [p["title"] for p in r["map"]["points"]] == ["○○ 좌표 있음"]
    assert r["map"]["unlocated"] and r["map"]["origin"]["name"] == "○○ 호텔"


def test_interests_rank_and_optionally_filter():
    a = obs("s:1", title="○○ 전통 공연")
    b = obs("s:2", title="○○ 사진 전시", venue_name="△△")
    r = search(a, b, interests=["전시"])
    assert ids(r)[0] == "○○ 사진 전시" and r["events"][0]["interest_match"] == ["전시"]
    r = search(a, b, interests=["전시"], require_interest=True)
    assert ids(r) == ["○○ 사진 전시"] and why(r)["○○ 전통 공연"] == "관심사와 맞지 않음"


def test_summary_keeps_unknowns_and_links_to_sources():
    o = dataclasses.replace(obs("s:1"), reservation=Reservation(link="https://example.invalid/r"))
    e = search(o)["events"][0]
    assert e["price"]["kind"] == "unknown" and e["reservation"]["required"] == "unknown"
    assert e["language"]["english_guidance"] == "unknown" and e["language"]["languages"] == []
    assert e["links"][0]["url"] == "https://example.invalid/x" and e["links"][0]["quote"]
    assert e["last_verified_at"] == "2026-10-07T12:00" and "price" in e["needs_check"]


def test_old_last_verified_time_is_flagged_as_stale_not_cancelled():
    (e,) = entries(obs("s:1"))
    fresh = search_events([e], {"trip": TRIP}, now=NOW)["events"][0]
    assert fresh["stale"] is False
    old = dataclasses.replace(e, last_verified_at="2026-10-01T12:00")
    shown = search_events([old], {"trip": TRIP}, now=NOW)["events"][0]
    assert shown["stale"] is True and shown["lifecycle"] != "cancelled"


def test_age_only_conditions_are_shown_but_do_not_decide_eligibility():
    from domains.kcontext.catalog.rules import parse_eligibility

    r = search(obs("s:1", eligibility=parse_eligibility("만 7세 이상")))
    p = r["events"][0]["participation"]
    assert p["status"] == "unverified" and any("연령 조건" in x for x in p["reasons"])
    r = search(obs("s:2", eligibility=parse_eligibility("회원 누구나")))
    assert r["events"][0]["participation"]["status"] == "restricted"


# ---- D23: 종료일·회차 없이 1년 넘게 지난 행사 -----------------------------------------------------
STALE = "종료일 정보가 없고 시작한 지 1년이 넘음"


def test_d23_open_ended_boundary_365_kept_366_excluded():
    r = search(obs("s:1", title="○○ 365일", start="2025-10-15", end=None),
               obs("s:2", title="○○ 366일", start="2025-10-14", end=None, venue_name="△△"))
    assert ids(r) == ["○○ 365일"] and why(r) == {"○○ 366일": STALE}


def test_d23_end_date_or_sessions_or_missing_start_are_not_excluded():
    r = search(obs("s:1", title="○○ 종료일", start="2021-01-01", end="2026-12-31"),
               obs("s:2", title="○○ 회차", start="2021-01-01", end=None, venue_name="△△",
                   sessions=(session("2026-10-16"),)),
               obs("s:3", title="○○ 시작일없음", start=None, end=None, venue_name="□□"))
    assert STALE not in why(r).values()
    assert {"○○ 종료일", "○○ 회차"} <= set(ids(r))
