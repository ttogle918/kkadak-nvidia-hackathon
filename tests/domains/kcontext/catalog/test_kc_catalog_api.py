import dataclasses
import json
import subprocess
import sys
from pathlib import Path

import pytest
from kc_catalog_helpers import NOW, obs, session

from domains.kcontext.catalog.api import ApiError, handle
from domains.kcontext.catalog.model import Reservation
from domains.kcontext.catalog.routes import TableRouteProvider
from domains.kcontext.catalog.rules import parse_eligibility
from domains.kcontext.catalog.store import CatalogStore
from domains.kcontext.catalog.updater import run_source

REPO = Path(__file__).resolve().parents[4]
A, V, B = (37.5650, 126.9900), (37.5700, 126.9950), (37.5750, 127.0000)
TABLE = {(A, V): 10, (V, B): 12, (A, B): 15}
TRIP = {"from": "2026-10-16", "to": "2026-10-16"}


def seeded(tmp_path):
    st = CatalogStore(tmp_path / "cat")
    o = obs("s:1", title="○○ 저녁 공연", lat=V[0], lng=V[1], sessions=(session("2026-10-16", "19:00", "20:30"),),
            eligibility=parse_eligibility("누구나 외국인 참여 가능"), reservation=Reservation(required="no"),
            external_ids=("k1",))
    run_source(st, "seoul_openapi", lambda: [o], now=NOW)
    return st


def itin():
    return [{"id": "낮", "title": "낮", "date": "2026-10-16", "start": "14:00", "end": "17:00", "lat": A[0], "lng": A[1]},
            {"id": "밤", "title": "밤", "date": "2026-10-16", "start": "22:00", "end": "23:00", "lat": B[0], "lng": B[1]}]


def call(op, args=None, st=None, **kw):
    return handle(op, args or {}, store=st, now=NOW, **kw)


def test_search_returns_events_coverage_and_suggestions(tmp_path):
    st = seeded(tmp_path)
    r = call("search", {"trip": TRIP, "itinerary": itin(), "max_extra_minutes": 30}, st,
             provider=TableRouteProvider(TABLE))
    assert [e["title"] for e in r["events"]] == ["○○ 저녁 공연"]
    assert r["coverage"]["complete"] is False
    assert any(s["id"] == "seoul_openapi" and s["last_success_at"] for s in r["coverage"]["sources"])
    (s,) = r["suggestions"]
    assert s["extra_minutes"] == 7 and s["status"] == "fit" and s["after_item_id"] == "낮"
    assert r["catalog_empty"] is False


def test_search_without_a_provider_asks_to_check_travel(tmp_path):
    r = call("search", {"trip": TRIP, "itinerary": itin()}, seeded(tmp_path))
    (s,) = r["suggestions"]
    assert s["extra_minutes"] is None and s["status"] == "check_needed"


def test_empty_catalog_is_reported_not_faked(tmp_path):
    r = call("search", {"trip": TRIP}, CatalogStore(tmp_path / "none"))
    assert r["events"] == [] and r["catalog_empty"] is True


def test_detail_includes_history_stories_and_coverage(tmp_path):
    st = seeded(tmp_path)
    eid = st.load_entries()[0].id
    r = call("detail", {"entry_id": eid}, st)
    assert r["id"] == eid and r["history"] and r["history"][0]["field"] == "__new__"
    assert r["stories"] == [] and r["coverage"]["complete"] if "complete" in r["coverage"] else True
    with pytest.raises(ApiError) as ei:
        call("detail", {"entry_id": "ev:none"}, st)
    assert ei.value.code == "not_found"


def test_itinerary_add_and_remove_roundtrip(tmp_path):
    st = seeded(tmp_path)
    eid = st.load_entries()[0].id
    args = {"entry_id": eid, "date": "2026-10-16", "start_time": "19:00", "itinerary": itin()}
    out = call("itinerary_add", args, st, provider=TableRouteProvider(TABLE))
    added = [i for i in out["itinerary"] if i["id"].startswith("evt:")]
    assert len(added) == 1 and len(out["itinerary"]) == 3 and out["suggestion"]["extra_minutes"] == 7
    back = call("itinerary_remove", {"itinerary": out["itinerary"], "item_id": added[0]["id"]}, st)
    assert [i["id"] for i in back["itinerary"]] == ["낮", "밤"]
    with pytest.raises(ApiError) as ei:
        call("itinerary_add", {**args, "start_time": "20:00"}, st)
    assert ei.value.code == "not_found"


def test_itinerary_add_refuses_a_clash_unless_forced(tmp_path):
    st = seeded(tmp_path)
    eid = st.load_entries()[0].id
    clash = [{"id": "식사", "title": "식사", "date": "2026-10-16", "start": "18:30", "end": "19:30",
              "lat": A[0], "lng": A[1]}]
    args = {"entry_id": eid, "date": "2026-10-16", "start_time": "19:00", "itinerary": clash}
    with pytest.raises(ApiError) as ei:
        call("itinerary_add", args, st)
    assert ei.value.code == "conflict" and "겹침" in str(ei.value)
    assert len(call("itinerary_add", {**args, "force": True}, st)["itinerary"]) == 2


def test_saved_changes_show_only_what_changed_after_the_saved_time(tmp_path):
    st = seeded(tmp_path)
    eid = st.load_entries()[0].id
    o2 = dataclasses.replace(
        obs("s:1", title="○○ 저녁 공연", lat=V[0], lng=V[1], external_ids=("k1",),
            sessions=(session("2026-10-17", "20:00", "21:30"),), start="2026-10-17", end="2026-10-17",
            eligibility=parse_eligibility("누구나 외국인 참여 가능"), reservation=Reservation(required="no")))
    later = NOW.replace(hour=15)
    run_source(st, "seoul_openapi", lambda: [o2], now=later)
    r = call("saved_changes", {"ids": [eid, "ev:other"], "since": "2026-10-07T13:00"}, st)
    (s,) = r["saved"]
    assert s["entry_id"] == eid and s["has_major"] is True
    assert {c["field"] for c in s["changes"]} >= {"start_date", "sessions"}
    assert call("saved_changes", {"ids": [eid], "since": "2026-10-07T16:00"}, st)["saved"] == []


def test_report_flow_via_api_needs_a_human_to_decide(tmp_path):
    st = CatalogStore(tmp_path / "cat")
    body = {"kind": "new_event", "official_link": "https://www.example.invalid/n/1", "reason": "공식 공지로 확인했습니다",
            "fields": {"title": "○○ 제보 행사", "start_date": "2026-10-16", "venue_address": "서울특별시 중구 ○○로 1"}}
    rec = call("report_submit", body, st)["report"]
    assert rec["status"] == "pending"
    with pytest.raises(ApiError) as ei:
        call("admin_report_decide", {"report_id": rec["id"], "decision": "approve"}, st)
    assert ei.value.code == "forbidden"
    with pytest.raises(ApiError):
        call("admin_report_decide", {"report_id": rec["id"], "decision": "approve"}, st, actor="agent:bot")
    out = call("admin_report_decide", {"report_id": rec["id"], "decision": "approve"}, st, actor="human:demo")
    assert out["report"]["status"] == "accepted"
    with pytest.raises(ApiError) as ei2:
        call("report_submit", {**body, "official_link": "x"}, st)
    assert ei2.value.code == "bad_request"


def test_admin_ops_need_a_human_actor(tmp_path):
    st = seeded(tmp_path)
    for op in ("admin_review_queue", "admin_reports", "admin_sources", "admin_refresh", "admin_link_check"):
        with pytest.raises(ApiError) as ei:
            call(op, {}, st)
        assert ei.value.code == "forbidden"
    q = call("admin_review_queue", {}, st, actor="human:demo")
    assert {"new_or_changed", "conflicts", "collection_errors", "manual_links"} <= set(q)
    assert call("admin_sources", {}, st, actor="human:demo")["runs"]["seoul_openapi"]["last_success_at"]


def test_link_check_and_refresh_ops(tmp_path):
    st = seeded(tmp_path)
    r = call("admin_link_check", {"source_id": "caci", "note": "확인함"}, st, actor="human:demo")
    assert r["link_check"]["checked_by"] == "human:demo"
    assert st.load_link_checks()["caci"]["note"] == "확인함"
    with pytest.raises(ApiError) as ei:
        call("admin_link_check", {"source_id": "nope"}, st, actor="human:demo")
    assert ei.value.code == "not_found"
    with pytest.raises(ApiError) as ei2:
        call("admin_refresh", {"source_id": "caci"}, st, actor="human:demo")
    assert ei2.value.code == "not_implemented"
    out = call("admin_refresh", {"source_id": "seoul_openapi"}, st, actor="human:demo", env={})
    assert out["run"]["ok"] is False and "SEOUL_OPENAPI_KEY" in out["run"]["error"]
    assert len(st.load_entries()) == 1  # 실패해도 기존 데이터 유지


def test_unknown_op(tmp_path):
    with pytest.raises(ApiError) as ei:
        call("nope", {}, CatalogStore(tmp_path))
    assert ei.value.code == "bad_request"


def run_cli(payload, env_dir):
    import os

    return subprocess.run([sys.executable, "-m", "domains.kcontext.catalog.api"], input=payload, text=True,
                          capture_output=True, check=False, cwd=REPO, env={**os.environ, "KC_CATALOG_DIR": str(env_dir),
                                                              "PYTHONPATH": str(REPO)})


def test_cli_entry_point_speaks_json(tmp_path):
    seeded(tmp_path)
    p = run_cli(json.dumps({"op": "search", "args": {"trip": TRIP}}), tmp_path / "cat")
    assert p.returncode == 0 and json.loads(p.stdout)["events"][0]["title"] == "○○ 저녁 공연"
    p = run_cli(json.dumps({"op": "admin_reports", "args": {}}), tmp_path / "cat")
    assert json.loads(p.stdout)["error"]["code"] == "forbidden"
    p = run_cli("not json", tmp_path / "cat")
    assert p.returncode == 0 and json.loads(p.stdout)["error"]["code"] == "bad_request"
    p = run_cli(json.dumps({"op": "search", "args": {"trip": {"from": 1}}}), tmp_path / "cat")
    assert json.loads(p.stdout)["problems"]
