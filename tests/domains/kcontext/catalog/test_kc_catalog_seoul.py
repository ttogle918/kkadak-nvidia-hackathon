import json

import httpx
import pytest
from kc_catalog_helpers import NOW, REGION

from domains.kcontext.catalog.merge import build_entries
from domains.kcontext.catalog.seoul import (
    SeoulApiError,
    fetch_rows,
    observation_from_row,
    observations_from_rows,
)

KEY = "k" * 32  # 실행 시 조립한 합성 키


def row(**over):
    base = {
        "CODENAME": "콘서트", "GUNAME": "중구", "TITLE": "○○ 가을 음악회 (합성)",
        "DATE": "2026-10-16~2026-10-16", "PLACE": "○○ 홀", "ORG_NAME": "기타", "USE_TRGT": "성인, 청소년",
        "USE_FEE": "R석 77,000원", "INQUIRY": "02-000-0000", "PLAYER": "○○", "PROGRAM": "합성 프로그램",
        "ETC_DESC": "", "ORG_LINK": "https://tickets.example.invalid/1", "MAIN_IMG": "", "RGSTDATE": "2026-09-20",
        "TICKET": "시민", "STRTDATE": "2026-10-16 00:00:00.0", "END_DATE": "2026-10-16 00:00:00.0",
        "THEMECODE": "기타", "LOT": "126.99", "LAT": "37.56", "IS_FREE": "유료",
        "HMPG_ADDR": "https://culture.seoul.go.kr/culture/culture/cultureEvent/view.do?cultcode=158770&menuNo=1",
        "PRO_TIME": "19:30",
    }
    base.update(over)
    return base


def test_row_maps_the_documented_fields():
    o = observation_from_row(row(), region=REGION, collected_at="2026-10-07")
    assert o.obs_id == "seoul:158770" and o.external_ids == ("seoul_cult:158770",)
    assert o.title == "○○ 가을 음악회 (합성)" and o.event_type == "콘서트"
    assert o.venue.in_target == "yes" and o.venue.district_basis == "source_gu"
    assert (o.venue.lat, o.venue.lng) == (37.56, 126.99)  # LAT=위도, LOT=경도
    assert o.schedule.start_date == o.schedule.end_date == "2026-10-16"
    assert o.schedule.sessions[0].start_time == "19:30" and o.schedule.sessions[0].in_target == "yes"
    assert o.price.kind == "paid" and o.price.text == "R석 77,000원"
    assert o.evidence.kind == "official_api" and o.evidence.origin == "culture.seoul.go.kr#158770"
    assert o.evidence.url.startswith("https://culture.seoul.go.kr/")
    assert o.evidence.quote == "○○ 가을 음악회 (합성) / 2026-10-16~2026-10-16 / ○○ 홀"
    assert o.published_at == "2026-09-20"


def test_unknowns_stay_unknown():
    o = observation_from_row(row(IS_FREE="", USE_TRGT="", ORG_LINK="", PRO_TIME="", ORG_NAME=""),
                             region=REGION, collected_at="2026-10-07")
    assert o.price.kind == "unknown" and o.reservation.required == "unknown" and o.reservation.link == ""
    assert o.eligibility.stated_open == "unknown" and o.schedule.sessions == ()
    assert o.language.english_guidance == "unknown" and o.organizer == ""


def test_link_is_not_treated_as_a_reservation_requirement():
    o = observation_from_row(row(), region=REGION, collected_at="2026-10-07")
    assert o.reservation.required == "unknown" and "확인 필요" in o.reservation.note
    assert o.reservation.link.startswith("https://tickets.example.invalid")


def test_free_is_only_what_the_source_says():
    assert observation_from_row(row(IS_FREE="무료"), region=REGION, collected_at="2026-10-07").price.kind == "free"
    assert observation_from_row(row(IS_FREE="?"), region=REGION, collected_at="2026-10-07").price.kind == "unknown"


def test_range_and_non_time_pro_time():
    o = observation_from_row(row(DATE="2026-10-15~2026-10-18", STRTDATE="2026-10-15 00:00:00.0",
                                 END_DATE="2026-10-18 00:00:00.0", PRO_TIME="화~금 20:00, 토 15:00"),
                             region=REGION, collected_at="2026-10-07")
    assert o.schedule.sessions == () and o.schedule.hours_text == "화~금 20:00, 토 15:00"
    assert (o.schedule.start_date, o.schedule.end_date) == ("2026-10-15", "2026-10-18")


def test_dates_fall_back_to_the_date_field_and_bad_values_are_dropped():
    o = observation_from_row(row(STRTDATE="", END_DATE="", DATE="2026-10-15~2026-10-17"), region=REGION,
                             collected_at="2026-10-07")
    assert (o.schedule.start_date, o.schedule.end_date) == ("2026-10-15", "2026-10-17")
    o = observation_from_row(row(STRTDATE="2026-10-18 00:00:00.0", END_DATE="2026-10-15 00:00:00.0"),
                             region=REGION, collected_at="2026-10-07")
    assert o.schedule.end_date is None
    o = observation_from_row(row(LAT="x", LOT="127"), region=REGION, collected_at="2026-10-07")
    assert o.venue.lat is None and o.venue.lng is None


def test_missing_title_gives_nothing_and_missing_code_gets_a_stable_id():
    assert observation_from_row(row(TITLE=" "), region=REGION, collected_at="2026-10-07") is None
    a = observation_from_row(row(HMPG_ADDR=""), region=REGION, collected_at="2026-10-07")
    b = observation_from_row(row(HMPG_ADDR=""), region=REGION, collected_at="2026-10-08")
    assert a.obs_id == b.obs_id and a.obs_id.startswith("seoul:") and a.external_ids == ()


def test_only_events_held_in_the_target_region_are_kept():
    rows = [row(), row(GUNAME="강동구", TITLE="○○ 다른 구 공연", HMPG_ADDR="x?cultcode=2"),
            row(GUNAME="", TITLE="○○ 구 미상", HMPG_ADDR="x?cultcode=3")]
    obs = observations_from_rows(rows, region=REGION, collected_at="2026-10-07")
    assert [o.title for o in obs] == ["○○ 가을 음악회 (합성)", "○○ 구 미상"]
    assert obs[1].venue.in_target == "unknown"


def test_organizer_naming_the_region_does_not_make_it_in_region():
    r = row(GUNAME="강동구", ORG_NAME="중구청", HMPG_ADDR="x?cultcode=9")
    assert observations_from_rows([r], region=REGION, collected_at="2026-10-07") == []


def test_end_to_end_entry_from_a_row():
    (o,) = observations_from_rows([row()], region=REGION, collected_at="2026-10-07")
    (e,) = build_entries([o], now=NOW)
    assert e.verification == "verified" and e.lifecycle == "scheduled"
    assert e.eligibility.audience == "성인, 청소년"


def pages(rows, total=None, code="INFO-000"):
    def handler(req: httpx.Request) -> httpx.Response:
        parts = req.url.path.strip("/").split("/")
        a, b = int(parts[-2]), int(parts[-1])
        chunk = rows[a - 1: b]
        if not chunk:
            return httpx.Response(200, json={"RESULT": {"CODE": "INFO-200", "MESSAGE": "없음"}})
        return httpx.Response(200, json={"culturalEventInfo": {
            "list_total_count": total or len(rows), "RESULT": {"CODE": code, "MESSAGE": "ok"}, "row": chunk}})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_pages_until_total():
    rows, total = fetch_rows(KEY, client=pages([row(TITLE=f"○○ {i}") for i in range(5)]), page_size=2)
    assert len(rows) == 5 and total == 5


def test_fetch_requires_a_key():
    with pytest.raises(SeoulApiError, match="SEOUL_OPENAPI_KEY"):
        fetch_rows("", client=pages([]))


def test_fetch_error_messages_never_contain_the_key_or_url():
    def boom(req):
        raise httpx.ConnectError(f"cannot reach {req.url}")

    with pytest.raises(SeoulApiError) as ei:
        fetch_rows(KEY, client=httpx.Client(transport=httpx.MockTransport(boom)))
    assert KEY not in str(ei.value) and "openapi.seoul.go.kr" not in str(ei.value)

    def bad(req):
        return httpx.Response(500, text=f"error for {req.url}")

    with pytest.raises(SeoulApiError) as ei:
        fetch_rows(KEY, client=httpx.Client(transport=httpx.MockTransport(bad)))
    assert KEY not in str(ei.value) and "500" in str(ei.value)


def test_fetch_error_codes():
    def err(req):
        return httpx.Response(200, json={"RESULT": {"CODE": "ERROR-300", "MESSAGE": "x"}})

    with pytest.raises(SeoulApiError, match="ERROR-300"):
        fetch_rows(KEY, client=httpx.Client(transport=httpx.MockTransport(err)))
    with pytest.raises(SeoulApiError, match="ERROR-500"):
        fetch_rows(KEY, client=pages([row()], code="ERROR-500"))
    rows, _ = fetch_rows(KEY, client=pages([]))  # INFO-200 = 끝
    assert rows == []


def test_fetch_rejects_bad_shapes():
    def bad(req):
        return httpx.Response(200, json={"culturalEventInfo": {"RESULT": {"CODE": "INFO-000"}, "row": "oops"}})

    with pytest.raises(SeoulApiError):
        fetch_rows(KEY, client=httpx.Client(transport=httpx.MockTransport(bad)))

    def notjson(req):
        return httpx.Response(200, text="<html>")

    with pytest.raises(SeoulApiError):
        fetch_rows(KEY, client=httpx.Client(transport=httpx.MockTransport(notjson)))


def test_request_url_follows_the_documented_pattern():
    seen = []

    def handler(req):
        seen.append(str(req.url))
        return httpx.Response(200, json={"RESULT": {"CODE": "INFO-200"}})

    fetch_rows(KEY, client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert seen == [f"http://openapi.seoul.go.kr:8088/{KEY}/json/culturalEventInfo/1/1000/"]
    assert json.dumps(seen)  # 문자열
