from datetime import UTC, datetime

from fastapi.testclient import TestClient

from backend.app import create_app
from backend.security_log import build_entries, entries_from_events
from backend.settings import Settings
from core.audit import AuditLog, JsonlSink, MemorySink
from core.hitl import DraftWriter, init_db


def _clock():
    return datetime(2026, 1, 1, 0, 30, 5, tzinfo=UTC)


def _events():
    sink = MemorySink()
    log = AuditLog(sink, run_id="r1", actor="agent:t", clock=_clock)
    cid = log.call("kc_search", {})
    log.result(cid, "ok")
    cid = log.call("fetch", {})
    log.error(cid, type("InjectionBlocked", (Exception,), {})("blocked text"))
    cid = log.call("fetch", {})
    log.error(cid, ValueError("ordinary"))
    log.observe_net("a.test", 443, decision="denied")
    log.observe_net("b.test", 443, decision="allowed")
    log.observe_net("c.test", 443)
    log.call("other", {})
    return sink.events


def test_event_mapping():
    got = entries_from_events(_events(), run_id="r1")
    kinds = [(g["kind"], g["text"]["ko"]) for g in got]
    assert ("ok", "kc_search 실행") in kinds
    assert ("deny", "blocked text") in kinds
    assert ("deny", "a.test:443 차단") in kinds
    assert ("ok", "b.test:443 허용") in kinds
    assert len(got) == 4
    assert all(g["time"] == "09:30:05" and g["origin"] == "audit" for g in got)
    assert got[0]["id"].startswith("audit:r1:")


def test_build_sorted_and_policy_text(tmp_path):
    db = tmp_path / "h.db"
    init_db(db)
    w = DraftWriter(db, actor="agent:t")
    d = w.create("policy_proposal", {"summary": {"network": 2, "files": [1, 2, 3]}})
    out = build_entries([d], {"r1": _events()})
    assert [o["at"] for o in out] == sorted(o["at"] for o in out)
    pol = next(o for o in out if o["origin"] == "hitl")
    assert pol["text"]["ko"] == "정책 초안 · 네트워크 2 · 파일 3"
    assert pol["kind"] == "pend"


def test_unknown_payload_fallback(tmp_path):
    db = tmp_path / "h.db"
    init_db(db)
    d = DraftWriter(db, actor="agent:t").create("source_request", {"weird": 1})
    (e,) = build_entries([d], {})
    assert e["text"]["en"] == "source_request request"


def test_api_reads_audit_dir_and_skips_broken(tmp_path):
    s = Settings(tmp_path / "h.db", tmp_path / "audit", tmp_path / "o", reviewer_id="human:t")
    (tmp_path / "audit").mkdir()
    log = AuditLog(JsonlSink(tmp_path / "audit" / "run9.jsonl"), run_id="run9", actor="agent:t")
    log.observe_net("x.test", 443, decision="denied")
    (tmp_path / "audit" / "bad.jsonl").write_text("not json\n", encoding="utf-8")
    r = TestClient(create_app(s)).get("/api/audit")
    assert r.status_code == 200
    assert r.headers["X-Audit-Skipped"] == "1"
    (e,) = r.json()
    assert e["id"] == "audit:run9:1" and e["kind"] == "deny"
    assert "/" not in e["text"]["ko"].replace("차단", "")


def test_missing_audit_dir_is_empty(tmp_path):
    s = Settings(tmp_path / "h.db", tmp_path / "nodir", tmp_path / "o", reviewer_id="human:t")
    assert TestClient(create_app(s)).get("/api/audit").json() == []


def test_build_entries_mixed_naive_aware_sorts():
    from backend.security_log import build_entries_counted
    from core.audit import AuditEvent

    def ev(seq, ts):
        return AuditEvent(
            seq=seq, ts=ts, run_id="r", actor="a", phase="observe", kind="net", name="n",
            call_id=None, data={"host": "h", "port": 1, "decision": "denied"},
        )

    evs = [ev(1, "2026-10-07T02:00:00"), ev(2, "2026-10-07T01:00:00+00:00"), ev(3, "bad"), ev(4, "")]
    out, skipped = build_entries_counted([], {"r": evs})
    assert skipped == 2
    assert [e["id"] for e in out] == ["audit:r:2", "audit:r:1"]
