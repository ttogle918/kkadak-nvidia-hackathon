from datetime import UTC, date, datetime

import pytest
from kc_catalog_helpers import NOW, REGION, session

from domains.kcontext.catalog.model import EventEntry, Reservation, Schedule
from domains.kcontext.catalog.rules import (
    classify_venue,
    date_range_days,
    event_lifecycle,
    is_operating_day,
    parse_eligibility,
    reservation_status,
)


# ---- 지역: 개최 장소 기준 -------------------------------------------------------------------
def test_region_from_source_gu():
    assert classify_venue(name="○○ 홀", gu="중구", region=REGION).in_target == "yes"
    v = classify_venue(name="○○ 홀", gu="강동구", region=REGION)
    assert v.in_target == "no" and v.district == "강동구" and v.district_basis == "source_gu"


def test_organizer_name_is_not_a_region_evidence():
    # 장소는 모르는데 주최가 "중구"여도 장소 판정에는 쓰지 않는다(주최는 인자로 받지도 않는다)
    assert classify_venue(name="○○ 홀", region=REGION).in_target == "unknown"


def test_region_from_address_needs_the_city():
    assert classify_venue(address="서울특별시 중구 퇴계로 100", region=REGION).in_target == "yes"
    assert classify_venue(address="대구광역시 중구 ○○로 1", region=REGION).in_target == "unknown"
    v = classify_venue(address="서울특별시 마포구 ○○로 1", region=REGION)
    assert v.in_target == "no" and v.district == "마포구"


def test_address_substring_is_not_a_district():
    # "중구" 가 다른 낱말 안에 끼어 있는 경우
    assert classify_venue(address="서울 종로구 ○중구로 3", region=REGION).in_target == "no"


def test_region_from_coordinates_only_with_a_bbox():
    assert classify_venue(lat=37.56, lng=126.99, region=REGION).in_target == "unknown"  # bbox 없음
    import dataclasses

    boxed = dataclasses.replace(REGION, bbox=(37.5, 126.9, 37.6, 127.1))
    assert classify_venue(lat=37.56, lng=126.99, region=boxed).in_target == "yes"
    assert classify_venue(lat=37.7, lng=126.99, region=boxed).in_target == "no"


# ---- 참여조건 --------------------------------------------------------------------------------
def test_resident_restriction_is_detected():
    e = parse_eligibility("중구민")
    assert e.resident_only == "yes" and e.stated_open == "unknown"
    assert e.restrictions[0]["kind"] == "resident"
    assert parse_eligibility("서울시민 대상").resident_only == "yes"
    assert parse_eligibility("중구 주민").resident_only == "yes"


def test_resident_discount_is_not_a_restriction():
    e = parse_eligibility("누구나 (중구민 할인)")
    assert e.resident_only == "unknown" and e.stated_open == "yes"
    assert any(r["kind"] == "perk" for r in e.restrictions)
    assert parse_eligibility("중구민 우대").resident_only == "unknown"


def test_open_to_all_only_when_stated_and_unrestricted():
    assert parse_eligibility("누구나").stated_open == "yes"
    assert parse_eligibility("전체 관람가").stated_open == "yes"
    assert parse_eligibility("").stated_open == "unknown"
    assert parse_eligibility("성인, 청소년").stated_open == "unknown"
    assert parse_eligibility("누구나, 단 중구민만").stated_open == "unknown"


def test_age_conditions():
    e = parse_eligibility("만 19세 이상")
    assert e.age_limit and e.restrictions[0]["kind"] == "age"
    assert parse_eligibility("초등학생").age_limit == "초등학생"


def test_foreigner_status_only_when_stated():
    assert parse_eligibility("누구나").foreigner == "unknown"  # 누구나 ≠ 외국인 가능
    assert parse_eligibility("외국인 참여 가능").foreigner == "allowed"
    assert parse_eligibility("외국인 제외").foreigner == "excluded"
    assert parse_eligibility("내국인만").foreigner == "excluded"
    assert parse_eligibility("외국인 문의").foreigner == "unknown"


# ---- 날짜·운영일·휴무 ------------------------------------------------------------------------
def test_date_range_days():
    assert [d.isoformat() for d in date_range_days("2026-10-15", "2026-10-17")] == [
        "2026-10-15", "2026-10-16", "2026-10-17"]
    assert date_range_days("2026-10-15", None) == [date(2026, 10, 15)]
    assert date_range_days(None, None) == [] and date_range_days("2026-10-17", "2026-10-15") == []


def test_operating_day_respects_range_closures_and_sessions():
    s = Schedule(start_date="2026-10-14", end_date="2026-10-20", weekly_closed_days=(0,),
                 closed_dates=("2026-10-17",))
    assert is_operating_day(s, date(2026, 10, 13))[0] == "no"          # 시작 전
    assert is_operating_day(s, date(2026, 10, 21))[0] == "no"          # 종료 후
    assert is_operating_day(s, date(2026, 10, 19)) == ("no", "정기 휴무 요일")  # 월요일
    assert is_operating_day(s, date(2026, 10, 17))[0] == "no"          # 임시 휴무
    assert is_operating_day(s, date(2026, 10, 16))[0] == "unknown"     # 기간 안이지만 회차 모름
    with_sessions = Schedule(start_date="2026-10-14", end_date="2026-10-20",
                             sessions=(session("2026-10-16"),))
    assert is_operating_day(with_sessions, date(2026, 10, 16))[0] == "yes"
    assert is_operating_day(with_sessions, date(2026, 10, 15))[0] == "no"
    assert is_operating_day(Schedule(), date(2026, 10, 16))[0] == "unknown"


def test_holiday_exception_rule_is_not_decided_without_a_calendar():
    s = Schedule(start_date="2026-10-01", end_date="2026-10-31", weekly_closed_days=(0,),
                 holiday_rule="월요일이 공휴일이면 정상 운영")
    state, why = is_operating_day(s, date(2026, 10, 5))
    assert state == "unknown" and "공휴일" in why


# ---- 상태 ------------------------------------------------------------------------------------
def entry(**sched) -> EventEntry:
    return EventEntry(id="ev:x", title="○○", schedule=Schedule(**sched))


@pytest.mark.parametrize("start,end,expected", [
    ("2026-10-01", "2026-10-06", "ended"),
    ("2026-10-07", "2026-10-07", "ongoing"),
    ("2026-10-01", "2026-10-31", "ongoing"),
    ("2026-10-08", "2026-10-09", "scheduled"),
    (None, None, "unknown"),
])
def test_lifecycle_from_dates(start, end, expected):
    assert event_lifecycle(entry(start_date=start, end_date=end), NOW) == expected


def test_lifecycle_uses_asia_seoul_day_boundary():
    # UTC 로는 10-06 15:30 이지만 서울은 10-07 00:30
    utc = datetime(2026, 10, 6, 15, 30, tzinfo=UTC)
    assert event_lifecycle(entry(start_date="2026-10-07", end_date="2026-10-07"), utc) == "ongoing"
    naive = datetime(2026, 10, 7, 0, 30)  # noqa: DTZ001 - 시간대 없는 값은 서울로 본다
    assert event_lifecycle(entry(start_date="2026-10-07", end_date="2026-10-07"), naive) == "ongoing"


def test_cancelled_is_kept_over_dates():
    e = EventEntry(id="ev:x", title="○○", schedule=Schedule(start_date="2026-10-01", end_date="2026-10-02"),
                   lifecycle="cancelled")
    assert event_lifecycle(e, NOW) == "cancelled"


def test_sessions_extend_the_lifecycle():
    e = EventEntry(id="ev:x", title="○○", schedule=Schedule(
        start_date="2026-10-01", end_date="2026-10-02", sessions=(session("2026-10-20"),)))
    assert event_lifecycle(e, NOW) == "ongoing"


def test_reservation_status_rules():
    assert reservation_status(Reservation(required="no"), NOW) == "not_required"
    assert reservation_status(Reservation(required="unknown"), NOW) == "unknown"
    assert reservation_status(Reservation(required="yes"), NOW) == "unknown"  # 열려 있다고 추정하지 않음
    assert reservation_status(Reservation(required="yes", status="open"), NOW) == "open"
    assert reservation_status(Reservation(required="yes", status="full"), NOW) == "full"
    assert reservation_status(Reservation(required="yes", deadline="2026-10-06"), NOW) == "closed"
    assert reservation_status(Reservation(required="yes", status="open", deadline="2026-10-07"), NOW) == "open"
    assert reservation_status(Reservation(required="yes", status="open", deadline="2026-10-07T11:00"),
                              NOW) == "closed"
    assert reservation_status(Reservation(required="yes", deadline="어제"), NOW) == "unknown"


# ---- 2차 검토(reviewer) 재발 방지 ----------------------------------------------------------
@pytest.mark.parametrize("text", [
    "외국인 참여 가능 여부는 문의",
    "외국인등록증 소지자 가능",
    "외국인 가능 여부 확인",
    "외국인 가능시 문의",
])
def test_foreigner_phrases_that_are_not_a_yes_stay_unknown(text):
    assert parse_eligibility(text).foreigner == "unknown"


@pytest.mark.parametrize("text", ["외국인 참여 가능", "외국인 관광객 환영", "외국인도 참가 가능"])
def test_clear_foreigner_welcome_is_allowed(text):
    assert parse_eligibility(text).foreigner == "allowed"


@pytest.mark.parametrize("text", ["일반시민", "모든시민", "전체 시민 대상", "내외국인 구민"])
def test_generic_citizen_words_are_not_a_residency_condition(text):
    assert parse_eligibility(text).resident_only == "unknown"


@pytest.mark.parametrize("text", ["서울 거주자", "서울시 거주자 누구나", "관내 주민", "중구민만", "중구민 한정"])
def test_residency_conditions_and_exclusive_phrases_are_restrictions(text):
    e = parse_eligibility(text)
    assert e.resident_only == "yes" and e.stated_open == "unknown"


@pytest.mark.parametrize("text", ["중구민 무료", "중구민 할인", "누구나 (중구민 우대)"])
def test_resident_perks_are_not_restrictions(text):
    e = parse_eligibility(text)
    assert e.resident_only == "unknown" and any(r["kind"] == "perk" for r in e.restrictions)


def test_membership_and_infant_age_conditions_block_open_to_all():
    e = parse_eligibility("회원 누구나")
    assert e.stated_open == "unknown" and any(r["kind"] == "other" for r in e.restrictions)
    a = parse_eligibility("36개월 이상 누구나")
    assert a.stated_open == "unknown" and a.age_limit


def test_address_must_start_with_the_city_and_use_the_first_district():
    assert classify_venue(address="부산 중구 ○○로 1 서울빌딩", region=REGION).in_target == "unknown"
    assert classify_venue(address="대구광역시 중구 서울로 1", region=REGION).in_target == "unknown"
    v = classify_venue(address="서울특별시 종로구 ○○로 1 중구빌딩", region=REGION)
    assert v.in_target == "no" and v.district == "종로구"
    assert classify_venue(address="서울 중구 ○○로 1", region=REGION).in_target == "yes"
    assert classify_venue(address="대한민국 서울특별시 중구 ○○로 1", region=REGION).in_target == "yes"


def test_source_district_that_disagrees_with_the_address_is_not_trusted():
    v = classify_venue(gu="중구", address="서울특별시 종로구 ○○로 1", region=REGION)
    assert v.in_target == "unknown"
    assert classify_venue(gu="중구", address="서울특별시 중구 ○○로 1", region=REGION).in_target == "yes"
    assert classify_venue(gu="중구", address="부산 사하구 ○○로 1", region=REGION).in_target == "yes"  # 서울 주소가 아니면 비교하지 않는다


def test_start_date_alone_never_means_ended():
    e = EventEntry(id="ev:x", title="○○", schedule=Schedule(start_date="2026-10-01"))
    assert event_lifecycle(e, NOW) == "unknown"
    today = EventEntry(id="ev:x", title="○○", schedule=Schedule(start_date="2026-10-07"))
    assert event_lifecycle(today, NOW) == "ongoing"
    future = EventEntry(id="ev:x", title="○○", schedule=Schedule(start_date="2026-10-20"))
    assert event_lifecycle(future, NOW) == "scheduled"
