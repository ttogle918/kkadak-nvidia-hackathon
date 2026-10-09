from datetime import date

from domains.kcontext.schedule import understand

TRIP = {"trip_from": "2026-10-15", "trip_to": "2026-10-16"}
KO = "10/15 10시에 ○○궁, 2시부터 5시까지 ○○동, 숙소는 ○○역"


def codes(r):
    return [p["code"] for p in r["problems"]]


def ko_reply():
    return {"anchors": [
        {"type": "visit", "name": "○○궁", "date": "10-15", "from": "10:00", "to": None,
         "quote": "10/15 10시에 ○○궁"},
        {"type": "visit", "name": "○○동", "date": "10-15", "from": "14:00", "to": "17:00",
         "quote": "10/15 10시에 ○○궁, 2시부터 5시까지 ○○동"},
        {"type": "hotel", "name": "○○역", "quote": "숙소는 ○○역"},
    ]}


def test_korean_example(fake):
    reply = ko_reply()
    reply["anchors"][0]["quote"] = "10/15 10시에 ○○궁, 2시부터 5시까지 ○○동"
    reply["anchors"][0]["to"] = "11:00"
    r = understand(KO, complete=fake(reply), **TRIP)
    a = r["anchors"]
    assert a[0]["to"] is None and "TIME_NOT_IN_QUOTE" in codes(r)
    assert (a[1]["from"], a[1]["to"], a[1]["day"]) == ("2026-10-15T14:00", "2026-10-15T17:00", 1)
    assert a[1]["lat"] is None and a[1]["lng"] is None
    assert a[2]["type"] == "hotel" and a[2]["name"] == "○○역" and a[2]["from"] is None
    assert "day" not in a[2]
    assert "AMPM_ASSUMED" in codes(r)  # 2시·5시 를 오후로 본 것은 알린다
    # 10/15 : 일정 없는 시간 = 14:00 전, 17:00 후. 10시 일정은 끝 시각 없음 → 그날 계산 안 함
    days = {s["day"] for s in r["free_slots"]}
    assert days == {2}  # 둘째 날은 일정이 없어 통째로 비어 있음
    assert "DAY_UNTIMED" in codes(r)


def test_english_example(fake):
    text = "Oct 15: Palace visit 10am-12:30pm. Then Market 2pm to 5pm. Hotel check-in 3pm."
    reply = {"anchors": [
        {"type": "visit", "name": "Palace", "date": "10-15", "from": "10:00", "to": "12:30",
         "quote": "Oct 15: Palace visit 10am-12:30pm"},
        {"type": "visit", "name": "Market", "date": "10-15", "from": "14:00", "to": "17:00",
         "quote": "Then Market 2pm to 5pm"},
        {"type": "hotel", "name": "Hotel", "date": "10-15", "from": "15:00",
         "quote": "Hotel check-in 3pm"},
    ]}
    r = understand(text, complete=fake(reply), **TRIP)
    a = r["anchors"]
    assert a[0]["from"] == "2026-10-15T10:00" and a[0]["to"] == "2026-10-15T12:30"
    # 두 번째 quote 에는 날짜가 없지만 바로 앞 날짜 표기(Oct 15)가 문맥으로 확인된다
    assert a[1]["from"] == "2026-10-15T14:00" and a[1]["to"] == "2026-10-15T17:00"
    assert a[2]["from"] == "2026-10-15T15:00" and a[2]["to"] is None
    d1 = [s for s in r["free_slots"] if s["day"] == 1]
    # 08:00-10:00, 12:30-14:00, 17:00-23:00 (체크인 15:00~16:00 는 17:00 전이라 영향 없음)
    assert [(s["from"][11:], s["to"][11:]) for s in d1] == [
        ("08:00", "10:00"), ("12:30", "14:00"), ("17:00", "23:00")]
    assert [s["inferred"] for s in d1] == [True, False, True]
    assert d1[0]["assumption"]["ko"] and d1[0]["assumption"]["en"]
    assert d1[1]["assumption"] is None and d1[1]["near"] == "Palace"
    assert d1[2]["near"] == "Market"


def test_free_slots_from_llm_are_ignored(fake):
    reply = ko_reply()
    reply["free_slots"] = [{"day": 1, "from": "2026-10-15T00:00", "to": "2026-10-15T01:00"}]
    reply["anchors"] = reply["anchors"][1:2]
    r = understand(KO, complete=fake(reply), **TRIP)
    assert all(s["from"] != "2026-10-15T00:00" for s in r["free_slots"])
    d1 = [(s["from"][11:], s["to"][11:]) for s in r["free_slots"] if s["day"] == 1]
    assert d1 == [("08:00", "14:00"), ("17:00", "23:00")]


def test_hotel_checkin_checkout_blocked_from_free_time(fake):
    text = "10/15 숙소 ○○호텔 체크인 15시, 10/16 체크아웃 11시"
    reply = {"anchors": [{"type": "hotel", "name": "○○호텔", "date": "10-15", "to_date": "10-16",
                          "from": "15:00", "to": "11:00", "quote": text}]}
    r = understand(text, complete=fake(reply), **TRIP)
    h = r["anchors"][0]
    assert (h["from"], h["to"]) == ("2026-10-15T15:00", "2026-10-16T11:00")
    d1 = [(s["from"][11:], s["to"][11:]) for s in r["free_slots"] if s["day"] == 1]
    d2 = [(s["from"][11:], s["to"][11:]) for s in r["free_slots"] if s["day"] == 2]
    assert d1 == [("08:00", "15:00"), ("16:00", "23:00")]
    assert d2 == [("08:00", "10:00"), ("11:00", "23:00")]


def test_overlap_reported(fake):
    text = "10/15 ○○ 10:00-12:00, △△ 11:00-13:00"
    reply = {"anchors": [
        {"name": "○○", "date": "10-15", "from": "10:00", "to": "12:00", "quote": "10/15 ○○ 10:00-12:00"},
        {"name": "△△", "date": "10-15", "from": "11:00", "to": "13:00",
         "quote": "10/15 ○○ 10:00-12:00, △△ 11:00-13:00"},
    ]}
    r = understand(text, complete=fake(reply), **TRIP)
    assert "OVERLAP" in codes(r)
    d1 = [(s["from"][11:], s["to"][11:]) for s in r["free_slots"] if s["day"] == 1]
    assert d1 == [("08:00", "10:00"), ("13:00", "23:00")]


def test_day_without_plans_is_all_free_and_inferred(fake):
    text = "10/15 ○○ 10:00-11:00"
    reply = {"anchors": [{"name": "○○", "date": "10-15", "from": "10:00", "to": "11:00",
                          "quote": text}]}
    r = understand(text, complete=fake(reply), **TRIP)
    d2 = [s for s in r["free_slots"] if s["day"] == 2]
    assert len(d2) == 1 and d2[0]["inferred"] is True and d2[0]["near"] is None
    assert (d2[0]["from"], d2[0]["to"]) == ("2026-10-16T08:00", "2026-10-16T23:00")


def test_midnight_crossing(fake):
    text = "10/15 ○○ 야간 23:00~01:00, 10/16 △△ 00:30-02:00"
    reply = {"anchors": [
        {"name": "○○", "date": "10-15", "from": "23:00", "to": "01:00", "quote": "10/15 ○○ 야간 23:00~01:00"},
    ]}
    r = understand(text, complete=fake(reply), **TRIP)
    a = r["anchors"][0]
    assert (a["from"], a["to"]) == ("2026-10-15T23:00", "2026-10-16T01:00")
    assert "LONG_SPAN" not in codes(r)
    d1 = [(s["from"][11:], s["to"][11:]) for s in r["free_slots"] if s["day"] == 1]
    assert d1 == [("08:00", "23:00")]
    d2 = [(s["from"][11:], s["to"][11:]) for s in r["free_slots"] if s["day"] == 2]
    assert d2 == [("08:00", "23:00")]


def _noyear(fake, text, md, today):
    reply = {"anchors": [{"name": "○○", "date": md, "from": "10:00", "to": "11:00", "quote": text}]}
    return understand(text, complete=fake(reply), today=today)


def test_no_trip_assumes_nearest_upcoming_date(fake):
    # D22 ②: trip 없으면 오늘(포함) 이후 가장 가까운 그 월·일 + YEAR_ASSUMED
    text = "10/15 ○○ 10:00-11:00"
    r = _noyear(fake, text, "10-15", date(2026, 10, 10))
    a = r["anchors"][0]
    assert a["from"] == "2026-10-15T10:00" and a["day"] is None
    ya = [p for p in r["problems"] if p["code"] == "YEAR_ASSUMED"]
    assert ya and "2026-10-15" in ya[0]["message"] and "YEAR_UNKNOWN" not in codes(r)
    # 오늘 날짜 포함
    assert _noyear(fake, text, "10-15", date(2026, 10, 15))["anchors"][0]["from"] == "2026-10-15T10:00"
    # 이미 지났으면 내년(거슬러 가지 않는다)
    assert _noyear(fake, text, "10-15", date(2026, 10, 16))["anchors"][0]["from"] == "2027-10-15T10:00"


def test_no_trip_feb29_goes_to_next_existing_year(fake):
    text = "2/29 ○○ 10:00-11:00"
    r = _noyear(fake, text, "02-29", date(2026, 10, 10))
    assert r["anchors"][0]["from"] == "2028-02-29T10:00"


def test_trip_and_explicit_year_unchanged_by_today(fake):
    text = "10/15 ○○ 10:00-11:00"
    reply = {"anchors": [{"name": "○○", "date": "10-15", "from": "10:00", "to": "11:00", "quote": text}]}
    r = understand(text, complete=fake(reply), trip_from="2025-10-14", trip_to="2025-10-16", today=date(2026, 10, 10))
    assert r["anchors"][0]["from"] == "2025-10-15T10:00" and "YEAR_ASSUMED" not in codes(r)
    t2 = "2025-10-15 ○○ 10:00-11:00"
    r = understand(t2, complete=fake({"anchors": [{"name": "○○", "date": "2025-10-15", "from": "10:00",
                                                    "to": "11:00", "quote": t2}]}), today=date(2026, 10, 10))
    assert r["anchors"][0]["from"] == "2025-10-15T10:00" and "YEAR_ASSUMED" not in codes(r)


def test_explicit_year_without_trip(fake):
    text = "2026-10-15 ○○ 10:00-11:00"
    reply = {"anchors": [{"name": "○○", "date": "2026-10-15", "from": "10:00", "to": "11:00", "quote": text}]}
    r = understand(text, complete=fake(reply))
    assert r["anchors"][0]["from"] == "2026-10-15T10:00"
    assert r["anchors"][0]["day"] is None
    assert [(s["from"][11:], s["to"][11:]) for s in r["free_slots"]] == [("08:00", "10:00"), ("11:00", "23:00")]


def test_date_out_of_trip(fake):
    text = "11/20 ○○ 10:00-11:00"
    reply = {"anchors": [{"name": "○○", "date": "11-20", "from": "10:00", "to": "11:00", "quote": text}]}
    r = understand(text, complete=fake(reply), **TRIP)
    a = r["anchors"][0]
    assert a["from"] is None and "DATE_OUT_OF_TRIP" in codes(r)


def test_trip_invalid_is_ignored_with_problem(fake):
    r = understand("○○", complete=fake({"anchors": []}), trip_from="2026-10-18", trip_to="2026-10-15")
    assert "TRIP_INVALID" in codes(r)
