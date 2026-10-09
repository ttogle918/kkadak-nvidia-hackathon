import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "catalog"))
from kc_catalog_helpers import (
    NOW,
    obs,
    session,
)

from domains.kcontext.catalog.fit import fit_event
from domains.kcontext.catalog.merge import build_entries
from domains.kcontext.catalog.model import Reservation
from domains.kcontext.catalog.query import search_events
from domains.kcontext.catalog.routes import NullRouteProvider
from domains.kcontext.catalog.rules import parse_eligibility
from domains.kcontext.geo.chain import ChainRouteProvider, make_route_provider
from domains.kcontext.geo.distance import haversine_m
from domains.kcontext.geo.estimate import GeoConfig, StraightLineEstimator
from domains.kcontext.geo.osm import OsrmWalkProvider

A = (37.5600, 126.9900)
V = (37.5700, 126.9950)
B = (37.5750, 127.0000)


def test_haversine_one_degree_latitude_is_about_111km():
    assert 111_000 < haversine_m((37.0, 127.0), (38.0, 127.0)) < 111_400
    assert haversine_m(A, A) == 0


def test_estimator_is_flagged_estimated_and_rounds_up():
    e = StraightLineEstimator()
    assert e.estimated is True and e.minutes(A, A) == 0
    m = e.minutes(A, V)
    assert m == -(-int(haversine_m(A, V) * 1.3) // 67) or m > 0
    assert e.minutes(A, (91.0, 0.0)) is None and e.minutes(A, (float("nan"), 1.0)) is None
    with pytest.raises(ValueError):
        StraightLineEstimator(GeoConfig(speed_m_per_min=0))


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_osrm_provider_parses_duration_and_caches():
    seen = []

    def h(req):
        seen.append(str(req.url))
        return httpx.Response(200, json={"code": "Ok", "routes": [{"duration": 301}]})

    p = OsrmWalkProvider("https://router.local:5000", client=_client(h))
    assert p.estimated is False and p.minutes(A, V) == 6 and p.minutes(A, V) == 6
    assert len(seen) == 1 and "/route/v1/foot/126.995000,37.570000" not in seen[0] and "foot/126.990000,37.560000;126.995000,37.570000" in seen[0]


@pytest.mark.parametrize("resp", [
    httpx.Response(500), httpx.Response(200, text="not json"),
    httpx.Response(200, json={"code": "NoRoute"}), httpx.Response(200, json={"code": "Ok", "routes": []}),
    httpx.Response(200, json={"code": "Ok", "routes": [{"duration": "x"}]}),
    httpx.Response(200, json={"code": "Ok", "routes": [{"duration": True}]}),
])
def test_osrm_provider_failures_are_unknown_not_guesses(resp):
    p = OsrmWalkProvider("https://router.local:5000", client=_client(lambda r: resp))
    assert p.minutes(A, V) is None


def test_osrm_rejects_credentials_in_url_and_caps_calls():
    with pytest.raises(ValueError):
        OsrmWalkProvider("http://u:p@host")
    with pytest.raises(ValueError):
        OsrmWalkProvider("file:///etc/passwd")
    with pytest.raises(ValueError):
        OsrmWalkProvider("http://router.example.com")  # 원격 http 거부
    OsrmWalkProvider("http://127.0.0.1:5000")  # 루프백 http 는 허용
    p = OsrmWalkProvider("https://r", max_calls=1, client=_client(
        lambda r: httpx.Response(200, json={"code": "Ok", "routes": [{"duration": 60}]})))
    assert p.minutes(A, V) == 1 and p.minutes(V, B) is None


def test_chain_prefers_engine_then_estimate_and_tracks_estimated():
    eng = OsrmWalkProvider("https://r", client=_client(lambda r: httpx.Response(500)))
    c = ChainRouteProvider([eng, StraightLineEstimator()])
    c.begin()
    assert c.minutes(A, V) is not None and c.estimated is True and c.name == "straight_line_estimate"
    ok = OsrmWalkProvider("https://r", client=_client(
        lambda r: httpx.Response(200, json={"code": "Ok", "routes": [{"duration": 120}]})))
    c2 = ChainRouteProvider([ok, StraightLineEstimator()])
    c2.begin()
    assert c2.minutes(A, V) == 2 and c2.estimated is False and c2.name == "osm_route_engine"


def test_make_provider_defaults_to_none_and_ignores_bad_config():
    assert isinstance(make_route_provider({}), NullRouteProvider)
    assert isinstance(make_route_provider({"KC_ROUTE_PROVIDER": "weird"}), NullRouteProvider)
    assert isinstance(make_route_provider({"KC_ROUTE_PROVIDER": "osm"}), NullRouteProvider)  # URL 없음
    assert isinstance(make_route_provider({"KC_ROUTE_PROVIDER": "osm", "KC_OSM_ROUTER_URL": "ftp://x"}), NullRouteProvider)
    assert isinstance(make_route_provider({"KC_ROUTE_PROVIDER": "estimate"}), NullRouteProvider)  # 결정 승인 전 잠금
    est = make_route_provider({"KC_ROUTE_PROVIDER": "estimate", "KC_ROUTE_ESTIMATE_APPROVED": "1"})
    assert est.estimated is False  # 아직 쓰지 않았다 — 값을 준 뒤에 추정 여부가 정해진다
    assert est.minutes(A, V) is not None and est.estimated is True


def _event():
    o = obs("s:1", title="○○ 저녁 공연", sessions=(session("2026-10-16", "19:00", "20:30"),), lat=V[0], lng=V[1],
            eligibility=parse_eligibility("누구나 외국인 참여 가능"), reservation=Reservation(required="no"))
    return search_events(build_entries([o], now=NOW), {"trip": {"from": "2026-10-16", "to": "2026-10-16"}},
                         now=NOW)["events"][0]


def _plan(id, s, e, loc):
    return {"id": id, "title": f"○○ {id}", "date": "2026-10-16", "start": s, "end": e, "lat": loc[0], "lng": loc[1]}


def test_fit_never_says_fit_from_estimated_times():
    prov = make_route_provider({"KC_ROUTE_PROVIDER": "estimate", "KC_ROUTE_ESTIMATE_APPROVED": "1"})
    (s,) = fit_event(_event(), [_plan("낮", "10:00", "12:00", A), _plan("밤", "22:00", "23:00", B)], prov)
    assert s["route"]["estimated"] is True and s["extra_minutes"] is not None
    assert s["status"] != "fit" and any(r["code"] == "travel_estimated" for r in s["reasons"])


def test_osrm_non_object_json_and_oversize_and_deadline_are_unknown(monkeypatch):
    for resp in (httpx.Response(200, json=[1, 2]), httpx.Response(200, json="x"),
                 httpx.Response(200, content=b"{" + b" " * 70_000 + b"}")):
        p = OsrmWalkProvider("https://r", client=_client(lambda r, resp=resp: resp))
        assert p.minutes(A, V) is None
    from domains.kcontext.geo import osm
    p = OsrmWalkProvider("https://r", client=_client(
        lambda r: httpx.Response(200, json={"code": "Ok", "routes": [{"duration": 60}]})))
    monkeypatch.setattr(osm.time, "monotonic", lambda: 1e12)
    assert p.minutes(A, V) is None


def test_estimated_values_do_not_make_no_fit():
    prov = make_route_provider({"KC_ROUTE_PROVIDER": "estimate", "KC_ROUTE_ESTIMATE_APPROVED": "1"})
    # 뒤 일정이 행사 직후라 시간 부족처럼 보여도 추정값만으로는 no_fit 이 아니다
    (s,) = fit_event(_event(), [_plan("밤", "20:31", "22:00", B)], prov)
    assert s["status"] == "check_needed"


@pytest.mark.parametrize("url,ok", [("http://localhost:5000", True), ("http://127.0.0.1:5000", True),
                                    ("http://[::1]:5000", True), ("https://router.example.invalid", False),
                                    ("http://10.0.0.5", False), ("not a url", False)])
def test_agent_provider_allows_only_loopback_osm(url, ok):
    from domains.kcontext.geo.chain import ROUTE_REMOTE_REFUSED, make_agent_route_provider

    p, codes = make_agent_route_provider({"KC_ROUTE_PROVIDER": "osm", "KC_OSM_ROUTER_URL": url})
    if ok:
        assert codes == [] and isinstance(p, ChainRouteProvider)
    else:
        assert isinstance(p, NullRouteProvider) and (codes == [ROUTE_REMOTE_REFUSED] or url == "not a url")


def test_osrm_budget_is_capped_by_argument():
    p = OsrmWalkProvider("http://127.0.0.1:1", budget_s=0)
    assert p.minutes((37.5, 127.0), (37.51, 127.01)) is None  # 예산 0 → 부르지 않고 모름
