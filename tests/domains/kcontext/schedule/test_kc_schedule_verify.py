from domains.kcontext.schedule import understand

TRIP = {"trip_from": "2026-10-15", "trip_to": "2026-10-16"}


def codes(r):
    return [p["code"] for p in r["problems"]]


def one(fake, text, cand):
    return understand(text, complete=fake({"anchors": [cand]}), **TRIP)


def test_quote_not_in_text_drops_candidate(fake):
    r = one(fake, "10/15 ○○ 10시", {"name": "○○", "quote": "10/15 △△ 10시"})
    assert r["anchors"] == [] and "QUOTE_NOT_FOUND" in codes(r) and "NO_ANCHOR_VERIFIED" in codes(r)


def test_quote_match_ignores_whitespace_and_width(fake):
    r = one(fake, "10/15   ○○\n 10:00-11:00", {"name": "○○", "date": "10-15", "from": "10:00",
                                              "to": "11:00", "quote": "10/15 ○○ 10:00-11:00"})
    assert r["anchors"][0]["source_quote"] == "10/15 ○○ 10:00-11:00"
    r = one(fake, "Ｏ○ 10/15 10:00-11:00", {"name": "O○", "quote": "O○ 10/15"})
    assert len(r["anchors"]) == 1  # 전각 영문은 NFKC 로 같아진다


def test_quote_missing_or_too_long(fake):
    assert "QUOTE_MISSING" in codes(one(fake, "○○", {"name": "○○"}))
    long = "가" * 250
    r = one(fake, long, {"name": "가", "quote": long})
    assert "QUOTE_TOO_LONG" in codes(r) and r["anchors"] == []


def test_name_not_in_quote_is_null(fake):
    r = one(fake, "10/15 ○○ 10시", {"name": "△△", "date": "10-15", "quote": "10/15 ○○ 10시"})
    assert r["anchors"][0]["name"] is None and "NAME_NOT_IN_QUOTE" in codes(r)


def test_time_not_in_quote_is_null(fake):
    r = one(fake, "10/15 ○○ 10시에", {"name": "○○", "date": "10-15", "from": "09:00", "to": "11:00",
                                       "quote": "10/15 ○○ 10시에"})
    a = r["anchors"][0]
    assert a["from"] is None and a["to"] is None
    assert codes(r).count("TIME_NOT_IN_QUOTE") == 2


def test_time_with_meridiem_is_exact(fake):
    text = "10/15 ○○ 오후 2시부터 오후 5시"
    r = one(fake, text, {"name": "○○", "date": "10-15", "from": "14:00", "to": "17:00", "quote": text})
    assert r["anchors"][0]["from"] == "2026-10-15T14:00"
    assert "AMPM_ASSUMED" not in codes(r)
    r = one(fake, text, {"name": "○○", "date": "10-15", "from": "02:00", "to": "17:00", "quote": text})
    assert r["anchors"][0]["from"] is None  # 오후 2시 는 02:00 이 아니다


def test_date_not_in_quote_or_context_is_null(fake):
    r = one(fake, "10/15 □□ 10:00 / ○○ 10:00-11:00",
            {"name": "○○", "date": "10-16", "from": "10:00", "to": "11:00", "quote": "○○ 10:00-11:00"})
    assert r["anchors"][0]["from"] is None and "DATE_NOT_IN_QUOTE" in codes(r)


def test_context_date_is_nearest_preceding_only(fake):
    text = "10/15 □□ 10:00-11:00\n10/16 ○○ 10:00-11:00 \n△△ 13:00-14:00"
    r = one(fake, text, {"name": "△△", "date": "10-16", "from": "13:00", "to": "14:00",
                         "quote": "△△ 13:00-14:00"})
    assert r["anchors"][0]["from"] == "2026-10-16T13:00"
    r = one(fake, text, {"name": "△△", "date": "10-15", "from": "13:00", "to": "14:00",
                         "quote": "△△ 13:00-14:00"})
    assert r["anchors"][0]["from"] is None


def test_quote_repeated_disables_context(fake):
    text = "10/15 ○○ 10:00-11:00\n10/16 ○○ 10:00-11:00"
    r = one(fake, text, {"name": "○○", "date": "10-16", "from": "10:00", "to": "11:00",
                         "quote": "○○ 10:00-11:00"})
    assert r["anchors"][0]["from"] is None


def test_year_in_text_and_out_of_trip_year(fake):
    text = "2025/10/15 ○○ 10:00-11:00"
    r = one(fake, text, {"name": "○○", "date": "2025-10-15", "from": "10:00", "to": "11:00", "quote": text})
    assert r["anchors"][0]["from"] is None and "DATE_OUT_OF_TRIP" in codes(r)


def test_invalid_calendar_date(fake):
    text = "2/30 ○○ 10:00"
    r = one(fake, text, {"name": "○○", "date": "02-30", "quote": text})
    assert "DATE_INVALID" in codes(r) or "DATE_OUT_OF_TRIP" in codes(r)


def test_hotel_type_needs_hotel_word(fake):
    r = one(fake, "10/15 ○○ 10:00", {"type": "hotel", "name": "○○", "quote": "10/15 ○○ 10:00"})
    assert r["anchors"][0]["type"] == "visit" and "TYPE_DOWNGRADED" in codes(r)


def test_bad_field_types_do_not_raise(fake):
    cand = {"name": 5, "date": ["x"], "from": 10, "to": {"a": 1}, "type": 3, "quote": "○○"}
    r = one(fake, "○○", cand)
    assert len(r["anchors"]) == 1 and r["anchors"][0]["name"] is None
    assert {"BAD_FIELD_TYPE", "TIME_FORMAT"} <= set(codes(r))


def test_duration_words_are_not_times(fake):
    text = "○○ 3시간 관람"
    r = one(fake, text, {"name": "○○", "from": "03:00", "quote": text})
    assert "TIME_NOT_IN_QUOTE" in codes(r)


def test_coordinates_never_filled(fake):
    r = one(fake, "○○", {"name": "○○", "quote": "○○", "lat": 37.5, "lng": 127.0})
    assert r["anchors"][0]["lat"] is None and r["anchors"][0]["lng"] is None
