"""D21 ① 모호한 시각은 낮 시간 후보로 — 표기가 있는 시각은 손대지 않는다."""

from domains.kcontext.schedule import understand

TRIP = {"trip_from": "2026-10-15", "trip_to": "2026-10-18"}


def one(fake, text, quote, frm, to=None):
    reply = {"anchors": [{"type": "visit", "name": "○○문", "date": "10-16", "from": frm, "to": to, "quote": quote}]}
    return understand(text, complete=fake(reply), **TRIP)


def codes(r):
    return [p["code"] for p in r["problems"]]


def msgs(r):
    return " ".join(p["message"] for p in r["problems"])


def test_ambiguous_one_oclock_becomes_afternoon(fake):
    t = "10/16에 ○○궁 10시, ○○문 1시"
    r = one(fake, t, "10/16에 ○○궁 10시, ○○문 1시", "01:00")
    assert r["anchors"][0]["from"] == "2026-10-16T13:00"
    assert "AMPM_ASSUMED" in codes(r) and "낮 시간 후보로 정함" in msgs(r)


def test_explicit_markers_untouched(fake):
    r = one(fake, "10/16 새벽 1시에 ○○문", "10/16 새벽 1시에 ○○문", "01:00")
    assert r["anchors"][0]["from"] == "2026-10-16T01:00"
    assert "AMPM_ASSUMED" not in codes(r) and "낮 시간" not in msgs(r)
    r = one(fake, "10/16 오후 1시에 ○○문", "10/16 오후 1시에 ○○문", "13:00")
    assert r["anchors"][0]["from"] == "2026-10-16T13:00"
    assert "낮 시간" not in msgs(r)


def test_ten_oclock_unchanged(fake):
    r = one(fake, "10/16 ○○문 10시", "10/16 ○○문 10시", "10:00")
    assert r["anchors"][0]["from"] == "2026-10-16T10:00"
    assert "AMPM_ASSUMED" not in codes(r)


def test_to_not_swapped_when_order_breaks(fake):
    # from 11:00, to 모델 값 01:00(모호) → 13:00 이 from ≤ to 를 지키므로 바뀐다
    t = "10/16 ○○문 11시부터 1시까지"
    r = one(fake, t, t, "11:00", "01:00")
    assert r["anchors"][0]["to"] == "2026-10-16T13:00"
    # from 오후 3시, to 1시(모델 01:00) → 13:00 <= 15:00 이라 바꾸지 않는다(기존 처리: 다음 날로 넘김)
    t = "10/16 ○○문 오후 3시부터 1시까지"
    r = one(fake, t, t, "15:00", "01:00")
    assert r["anchors"][0]["to"] == "2026-10-17T01:00"


def test_range_pair_judged_together(fake):
    # B1: "1시부터 3시까지" 에 모델이 01:00/03:00 → 둘 다 낮 시간으로 13:00~15:00
    t = "10/16 ○○문 1시부터 3시까지"
    r = one(fake, t, t, "01:00", "03:00")
    a = r["anchors"][0]
    assert (a["from"], a["to"]) == ("2026-10-16T13:00", "2026-10-16T15:00")


def test_range_same_time_not_swapped(fake):
    # 같은 값이면 바꾸지 않는다(바꾸면 from == to 로 24시간짜리가 된다)
    t = "10/16 ○○문 1시부터 1시까지"
    r = one(fake, t, t, "01:00", "01:00")
    a = r["anchors"][0]
    assert (a["from"], a["to"]) == ("2026-10-16T01:00", "2026-10-17T01:00")


def test_range_one_side_equal_not_swapped(fake):
    # 한쪽만 후보: from 후보 13:00 이 to(13:00 표기, 모호하지 않음)와 같으면 바꾸지 않는다
    t = "10/16 ○○문 1시부터 오후 1시까지"
    r = one(fake, t, t, "01:00", "13:00")
    a = r["anchors"][0]
    assert a["from"] == "2026-10-16T01:00"
