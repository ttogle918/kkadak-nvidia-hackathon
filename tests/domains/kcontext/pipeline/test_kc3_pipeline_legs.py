"""이동 구간 생산(legs.py) — 가짜 공급자·합성 앵커. D16(직선은 시간이 아니다)·D18(숙소 제외)."""

from domains.kcontext.catalog.routes import NullRouteProvider, TableRouteProvider
from domains.kcontext.geo.chain import ChainRouteProvider, make_route_provider
from domains.kcontext.geo.estimate import StraightLineEstimator
from domains.kcontext.pipeline.legs import MAX_LEGS, build_routes

A = (37.5000, 127.0000)
B = (37.5100, 127.0100)
C = (37.5200, 127.0300)


def v(name, hm, ll, day=1, d="2026-10-15"):
    a = {"type": "visit", "name": name, "day": day, "from": f"{d}T{hm}" if hm else None, "to": None,
         "lat": ll[0] if ll else None, "lng": ll[1] if ll else None}  # fmt: skip
    return a


def test_null_provider_gives_straight_but_no_minutes():
    r = build_routes([v("a", "10:00", A), v("b", "12:00", B)], provider=NullRouteProvider())
    assert len(r) == 1 and r[0]["id"] == "day1" and r[0]["day"] == 1 and r[0]["date"] == "2026-10-15"
    leg = r[0]["legs"][0]
    assert leg["walk_min"] is None and leg["provider"] == "none" and leg["estimated"] is False
    assert isinstance(leg["straight_m"], int) and 1000 < leg["straight_m"] < 1700
    assert leg["from"] == "a" and leg["to"] == "b" and leg["from_ll"] == list(A) and leg["to_ll"] == list(B)


def test_table_provider_minutes_and_name():
    p = TableRouteProvider({(A, B): 14}, name="tbl")
    leg = build_routes([v("a", "10:00", A), v("b", "12:00", B)], provider=p)[0]["legs"][0]
    assert leg["walk_min"] == 14 and leg["provider"] == "tbl" and leg["estimated"] is False


def test_estimate_provider_marked_estimated():
    p = ChainRouteProvider([StraightLineEstimator()])
    leg = build_routes([v("a", "10:00", A), v("b", "12:00", B)], provider=p)[0]["legs"][0]
    assert isinstance(leg["walk_min"], int) and leg["estimated"] is True
    assert leg["provider"] == "straight_line_estimate"


def test_chain_provider_state_reset_per_leg():
    p = ChainRouteProvider([TableRouteProvider({(A, B): 5}, name="tbl")])
    legs = build_routes([v("a", "10:00", A), v("b", "11:00", B), v("c", "12:00", C)], provider=p)[0]["legs"]
    assert legs[0]["provider"] == "tbl" and legs[1]["provider"] == "none" and legs[1]["walk_min"] is None


def test_default_env_provider_is_none_and_estimate_needs_approval():
    assert isinstance(make_route_provider({}), NullRouteProvider)
    assert isinstance(make_route_provider({"KC_ROUTE_PROVIDER": "estimate"}), NullRouteProvider)  # 승인 env 없음
    ok = make_route_provider({"KC_ROUTE_PROVIDER": "estimate", "KC_ROUTE_ESTIMATE_APPROVED": "1"})
    assert isinstance(ok, ChainRouteProvider)


def test_sorted_by_time_and_split_by_date():
    anchors = [v("c", "15:00", C), v("a", "09:00", A), v("b", "11:00", B),
               v("x", "10:00", A, day=2, d="2026-10-16"), v("y", "11:00", B, day=2, d="2026-10-16")]  # fmt: skip
    r = build_routes(anchors, provider=NullRouteProvider())
    assert [x["id"] for x in r] == ["day1", "day2"]
    assert [(g["from"], g["to"]) for g in r[0]["legs"]] == [("a", "b"), ("b", "c")]
    assert [(g["from"], g["to"]) for g in r[1]["legs"]] == [("x", "y")]


def test_missing_coords_skipped_and_chain_continues():
    r = build_routes([v("a", "09:00", A), v("b", "11:00", None), v("c", "13:00", C)], provider=NullRouteProvider())[0]
    assert r["legs"] == []
    assert r["skipped"] == [{"from": "a", "to": "b", "reason": "좌표 없음"},
                            {"from": "b", "to": "c", "reason": "좌표 없음"}]  # fmt: skip


def test_visit_without_time_skipped_with_empty_to():
    r = build_routes([v("a", "09:00", A), v("b", "11:00", B), v("z", None, A)], provider=NullRouteProvider(),
                     trip_from="2026-10-15")  # fmt: skip
    assert r[0]["skipped"] == [{"from": "z", "to": "", "reason": "시각 없음"}]
    assert len(r[0]["legs"]) == 1


def test_visit_without_time_and_without_date_is_left_out():
    assert build_routes([v("z", None, A)], provider=NullRouteProvider()) == []


def test_hotel_excluded():
    h = {"type": "hotel", "name": "h", "from": "2026-10-15T15:00", "to": None, "lat": 37.0, "lng": 127.0}
    r = build_routes([v("a", "09:00", A), h, v("b", "11:00", B)], provider=NullRouteProvider())
    assert [(g["from"], g["to"]) for g in r[0]["legs"]] == [("a", "b")]


def test_same_place_is_zero():
    leg = build_routes([v("a", "09:00", A), v("a", "13:00", A)], provider=TableRouteProvider({}))[0]["legs"][0]
    assert (leg["straight_m"], leg["walk_min"], leg["provider"], leg["estimated"]) == (0, 0, "same_place", False)


def test_single_visit_day_makes_no_route():
    assert build_routes([v("a", "09:00", A)], provider=NullRouteProvider()) == []


def test_caps_and_unique_ids_without_day():
    many = [v(f"p{i}", f"{8 + i // 2:02d}:{(i % 2) * 30:02d}", A if i % 2 else B) for i in range(30)]
    assert len(build_routes(many, provider=NullRouteProvider())[0]["legs"]) == MAX_LEGS
    days = [v(f"p{d}{i}", f"1{i}:00", A, day=None, d=f"2026-10-{10 + d}") for d in range(9) for i in range(2)]
    r = build_routes(days, provider=NullRouteProvider())
    assert len(r) == 7 and len({x["id"] for x in r}) == 7


def test_provider_exception_means_unknown():
    class Boom:
        name, mode, estimated = "boom", "walk", False

        def minutes(self, a, b):
            raise RuntimeError("x")

    leg = build_routes([v("a", "09:00", A), v("b", "11:00", B)], provider=Boom())[0]["legs"][0]
    assert leg["walk_min"] is None and leg["provider"] == "none"
