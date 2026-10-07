import dataclasses
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from kc_catalog_helpers import NOW, obs, session

from domains.kcontext.catalog.api import handle
from domains.kcontext.catalog.cards import build_now_cards, tier_of
from domains.kcontext.catalog.fit import fit_event
from domains.kcontext.catalog.merge import build_entries
from domains.kcontext.catalog.model import Reservation
from domains.kcontext.catalog.query import search_events
from domains.kcontext.catalog.routes import NullRouteProvider, TableRouteProvider
from domains.kcontext.catalog.rules import parse_eligibility
from domains.kcontext.catalog.store import CatalogStore
from domains.kcontext.catalog.updater import run_source

REPO = Path(__file__).resolve().parents[4]
NODE = shutil.which("node")
TRIP = {"from": "2026-10-15", "to": "2026-10-18"}
A, V, B = (37.5650, 126.9900), (37.5700, 126.9950), (37.5750, 127.0000)
OPEN = parse_eligibility("누구나 외국인 참여 가능")


def good(**kw):
    kw.setdefault("lat", V[0])
    kw.setdefault("lng", V[1])
    kw.setdefault("eligibility", OPEN)
    kw.setdefault("reservation", Reservation(required="no"))
    kw.setdefault("sessions", (session("2026-10-16", "19:00", "20:30"),))
    return obs(**kw)


def run(*observations, itinerary=None, provider=None, **extra):
    entries = build_entries(list(observations), now=NOW)
    req = {"trip": TRIP, **extra}
    if itinerary is not None:
        req["itinerary"] = itinerary
    res = search_events(entries, req, now=NOW)
    if itinerary is not None:
        sug = []
        for e in res["events"]:
            sug.extend(fit_event(e, itinerary, provider or NullRouteProvider()))
        res["suggestions"] = sug
    return build_now_cards(res, req), res


def by_id(out):
    return {c["entry_id"]: c for c in out["cards"]}


def validate_with_node(out):
    p = subprocess.run([NODE, str(REPO / "frontend/k-context/tests/_validate_cards.mjs")],
                       input=json.dumps({"cards": out["cards"], "rationale": out["rationale"]}), text=True,
                       capture_output=True, check=False)
    assert p.returncode == 0, p.stderr[-400:]
    return json.loads(p.stdout)


# ---- 화면 계약(validateCard) -------------------------------------------------------------------
@pytest.mark.skipif(NODE is None, reason="node 가 없어 schema.js 로 검증할 수 없다")
def test_cards_pass_the_frontends_validateCard_and_rationale_shape():
    out, _ = run(good(), good(obs_id="s:2", title="△△ 전시", venue_name="□□ 관", lat=37.58, lng=127.01,
                              sessions=()),
                 itinerary=[{"id": "낮", "title": "낮", "date": "2026-10-16", "start": "14:00", "end": "17:00",
                             "lat": A[0], "lng": A[1]}],
                 provider=TableRouteProvider({(A, V): 10, (V, B): 12, (A, B): 15}))
    assert out["cards"]
    assert validate_with_node(out) == {"count": len(out["cards"]), "problems": []}


@pytest.mark.skipif(NODE is None, reason="node 가 없어 schema.js 로 검증할 수 없다")
def test_cards_with_conflicts_unknown_travel_and_unverified_sources_also_validate():
    a = good(external_ids=("k",), origin="o1", start="2026-10-16", end="2026-10-16")
    b = good(obs_id="s:2", external_ids=("k",), origin="o2", start="2026-10-17", end="2026-10-17")
    web = good(obs_id="w:1", title="○○ 검색 수집", venue_name="◇◇ 홀", kind="sns", source_id="web",
               lat=37.59, lng=127.02)
    out, _ = run(a, b, web, itinerary=[])
    assert len(out["cards"]) == 2 and validate_with_node(out)["problems"] == []


def test_card_ids_are_stable_and_json_serializable():
    out, _ = run(good())
    again, _ = run(good())
    assert [c["id"] for c in out["cards"]] == [c["id"] for c in again["cards"]]
    assert out["cards"][0]["id"].startswith("card_now_") and json.dumps(out)


# ---- 딱지: 확인됨은 검증·회차·최신·일정 제안이 모두 맞을 때만 -------------------------------------
def test_badge_is_confirmed_only_when_everything_is_known():
    out, _ = run(good())
    assert out["cards"][0]["badge"] == "확인됨"


def test_unconfirmed_session_or_unofficial_source_never_gets_the_confirmed_badge():
    out, _ = run(good(sessions=()), good(obs_id="s:2", title="△△ 공연", venue_name="□□", kind="sns",
                                         source_id="web", lat=37.58, lng=127.01))
    assert {c["badge"] for c in out["cards"]} == {"확인 필요"}


def test_conflicting_sources_get_the_hold_badge_and_list_the_rejected_values():
    a = good(external_ids=("k",), origin="o1", start="2026-10-16", end="2026-10-16", price_kind="free")
    b = good(obs_id="s:2", external_ids=("k",), origin="o2", start="2026-10-17", end="2026-10-17", price_kind="paid")
    out, _ = run(a, b)
    (card,) = out["cards"]
    assert card["badge"] == "보류"
    assert any("시작일" in r["claim"]["ko"] and "확정하지 않음" in r["reason"]["ko"] for r in card["rejected"])
    assert "conflict" in out["rationale"][card["id"]]["items"]


def test_stale_events_are_not_confirmed():
    entries = build_entries([good()], now=NOW)
    entries = [dataclasses.replace(entries[0], last_verified_at="2026-10-01T12:00")]
    res = search_events(entries, {"trip": TRIP}, now=NOW)
    (card,) = build_now_cards(res, {"trip": TRIP})["cards"]
    assert card["badge"] == "확인 필요" and any("오래됨" in c["text"]["ko"] for c in card["checks"])


# ---- 이동시간 모름은 숫자로 속이지 않는다 -------------------------------------------------------
def test_unknown_travel_is_flagged_and_can_be_null_when_the_contract_allows():
    itin = [{"id": "낮", "title": "낮", "date": "2026-10-16", "start": "14:00", "end": "17:00", "lat": A[0], "lng": A[1]}]
    out, res = run(good(), itinerary=itin)
    (c,) = out["cards"]
    assert c["time_cost_unknown"] is True and c["time_cost_min"] == 0 and c["badge"] == "확인 필요"
    assert any("이동시간 확인 필요" in x["text"]["ko"] for x in c["checks"])
    assert "이동시간 확인 필요" in out["rationale"][c["id"]]["chips"][-1]["label"]["ko"]
    nul = build_now_cards(res, {"trip": TRIP, "itinerary": itin}, null_unknown_time_cost=True)["cards"][0]
    assert nul["time_cost_min"] is None and nul["time_cost_unknown"] is True


def test_known_travel_fills_time_cost_and_the_between_labels():
    itin = [{"id": "낮", "title": "점심", "date": "2026-10-16", "start": "14:00", "end": "17:00", "lat": A[0], "lng": A[1]},
            {"id": "밤", "title": "호텔", "date": "2026-10-16", "start": "22:00", "end": "23:00", "lat": B[0], "lng": B[1]}]
    out, _ = run(good(), itinerary=itin, provider=TableRouteProvider({(A, V): 10, (V, B): 12, (A, B): 15}))
    (c,) = out["cards"]
    assert c["time_cost_min"] == 7 and c["time_cost_unknown"] is False and c["badge"] == "확인됨"
    assert [x["ko"] for x in c["slot"]["between"]] == ["점심", "호텔"] and c["slot"]["at"] == "19:00"
    assert c["slot"]["day"] == 2  # 여행 시작일(10/15) 기준 둘째 날


def test_event_already_in_the_itinerary_is_a_card_with_user_state_added_and_does_not_clash_with_itself():
    out, _ = run(good(), itinerary=[])
    eid = out["cards"][0]["entry_id"]
    itin = [{"id": f"evt:{eid}:2026-10-16:19:00", "title": "○○ 가을 음악회", "date": "2026-10-16", "start": "19:00",
             "end": "20:30", "lat": V[0], "lng": V[1], "source": "catalog", "entry_id": eid}]
    again, _ = run(good(), itinerary=itin)
    (card,) = again["cards"]
    assert card["user_state"] == "added" and again["skipped"] == []
    assert out["cards"][0]["user_state"] == "proposed"


# ---- 카드로 만들지 않는 것과 깔때기 -------------------------------------------------------------
def test_restricted_postponed_uncoordinated_and_non_fitting_events_are_not_cards():
    restricted = good(obs_id="s:2", title="△△ 주민 전용", venue_name="□□", lat=37.58, lng=127.01,
                      eligibility=parse_eligibility("서울 거주자"))
    nocoord = good(obs_id="s:3", title="◇◇ 좌표 없음", venue_name="◇◇", lat=None, lng=None)
    postponed = good(obs_id="s:4", title="☆☆ 연기", venue_name="☆☆ 극장", lat=37.60, lng=127.03, lifecycle="postponed",
                     kind="official_site")
    out, _ = run(good(), restricted, nocoord, postponed)
    assert [c["title"]["ko"] for c in out["cards"]] == ["○○ 가을 음악회"]
    assert {s["reason"] for s in out["skipped"]} == {"참여 제한", "좌표 없음", "연기됨"}
    assert out["funnel"]["candidates"] == 4 and out["funnel"]["adopted"] == 1
    assert out["funnel"]["reasons"] == {"참여 제한": 1, "좌표 없음": 1, "연기됨": 1}


def test_clashing_sessions_are_dropped_with_a_reason_and_search_exclusions_are_counted():
    clash = [{"id": "식사", "title": "식사", "date": "2026-10-16", "start": "18:30", "end": "19:30", "lat": A[0], "lng": A[1]}]
    other = good(obs_id="s:2", title="△△ 바깥", venue_name="□□", in_target="no")
    out, _ = run(good(), other, itinerary=clash)
    assert out["cards"] == [] and out["funnel"]["reasons"]["일정에 맞지 않음"] == 1
    assert out["funnel"]["reasons"]["대상 지역 밖에서 열림"] == 1 and out["funnel"]["candidates"] == 2


def test_demo_events_are_not_cards_unless_requested():
    entries = build_entries([good(demo=True)], now=NOW)
    res = search_events(entries, {"trip": TRIP, "include_demo": True}, now=NOW)
    assert build_now_cards(res, {"trip": TRIP})["cards"] == []
    (c,) = build_now_cards(res, {"trip": TRIP}, include_demo=True)["cards"]
    assert c["demo"] is True


# ---- 출처 표시 ---------------------------------------------------------------------------------
def test_source_tiers_and_unverified_flags_for_search_collected_events():
    assert [tier_of(k) for k in ("official_site", "official_api", "press", "sns", "ai_extracted", "report", "demo", "x")] == [
        "A", "B", "B", "C", "C", "D", "D", "D"]
    out, _ = run(good(kind="sns", source_id="web_search"))
    (c,) = out["cards"]
    assert c["sources"][0]["tier"] == "C" and c["sources"][0]["unverified"] is True
    assert c["caveats"][0]["ko"] == "검색 수집 · 미확인"
    assert c["sources"][0]["locator"].endswith("수집") and c["sources"][0]["collected_at"] == "2026-10-07"
    ok, _ = run(good())
    assert ok["cards"][0]["sources"][0]["unverified"] is False and not any("검색 수집" in x["ko"] for x in ok["cards"][0]["caveats"])


def test_unknown_facts_are_shown_as_needs_checking_not_as_yes():
    out, _ = run(good(eligibility=None, reservation=None, sessions=()))
    (c,) = out["cards"]
    texts = [x["ko"] for x in c["caveats"]]
    assert {"요금 확인 필요", "예약 확인 필요", "참여조건 확인 필요"} <= set(texts)
    assert not any("누구나" in w["ko"] for w in c["why_fits"])


def test_why_fits_lists_date_interest_and_stated_openness_only():
    out, _ = run(good(title="○○ 전통 공연"), interests=["공연"])
    (c,) = out["cards"]
    ko = [w["ko"] for w in c["why_fits"]]
    assert any("여행 날짜(2026-10-16)에 열림" in x for x in ko) and any("관심사와 일치: 공연" in x for x in ko)
    assert any("누구나" in x for x in ko)


# ---- API 진입점 --------------------------------------------------------------------------------
def test_cards_op_through_the_api_entry(tmp_path):
    st = CatalogStore(tmp_path / "cat")
    run_source(st, "seoul_openapi", lambda: [good()], now=NOW)
    out = handle("cards", {"trip": TRIP}, store=st, now=NOW)
    assert len(out["cards"]) == 1 and out["coverage"]["complete"] is False and out["problems"] == []
    assert out["rationale"][out["cards"][0]["id"]]["chips"][0]["key"] == "funnel"
    empty = handle("cards", {"trip": TRIP}, store=CatalogStore(tmp_path / "none"), now=NOW)
    assert empty["cards"] == [] and empty["funnel"] == {"candidates": 0, "adopted": 0, "reasons": {}}


def test_committed_fixture_is_current():
    """프론트 계약 테스트가 쓰는 fixture 가 이 코드의 출력과 같다(다르면 gen_cards_fixture.py 를 다시 돌린다)."""
    from gen_cards_fixture import OUT, build

    assert json.loads(OUT.read_text(encoding="utf-8")) == json.loads(json.dumps(build(), ensure_ascii=False))


def test_cards_endpoint_through_the_http_api(tmp_path):
    from fastapi.testclient import TestClient

    from backend.app import create_app
    from backend.settings import Settings

    run_source(CatalogStore(tmp_path / "cat"), "seoul_openapi", lambda: [good()], now=NOW)
    s = Settings(hitl_db=tmp_path / "h.db", audit_dir=tmp_path / "a", output_dir=tmp_path / "o",
                 reviewer_id="human:demo", catalog_dir=tmp_path / "cat")
    r = TestClient(create_app(s)).post("/api/events/cards", json={"trip": TRIP})
    assert r.status_code == 200
    d = r.json()
    assert [c["kind"] for c in d["cards"]] == ["now"] and d["funnel"]["adopted"] == 1 and d["rationale"]
    assert TestClient(create_app(s)).post("/api/events/cards", json={"trip": {"from": "내일", "to": "x"}}).status_code == 422
