import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.settings import Settings
from core.hitl import DraftWriter, init_db


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("APP_PROCESS_ROLE", raising=False)
    s = Settings(
        hitl_db=tmp_path / "hitl.db",
        audit_dir=tmp_path / "audit",
        output_dir=tmp_path / "output",
        reviewer_id="human:test",
    )
    init_db(s.hitl_db)
    w = DraftWriter(s.hitl_db, actor="agent:test-run")
    return TestClient(create_app(s)), w, s


def _draft(w, host="blog.example.com"):
    return w.create("source_request", {"host": host})


def test_list_empty_and_pending_entry(env):
    c, w, _ = env
    assert c.get("/api/audit").json() == []
    d = _draft(w)
    (e,) = c.get("/api/audit").json()
    assert e["id"] == f"draft:{d.id}" and e["kind"] == "pend" and e["origin"] == "hitl"
    assert e["text"]["ko"] == "blog.example.com · 허용 목록에 없음"
    assert e["decided_by"] is None


def test_approve_uses_server_identity(env):
    c, w, _ = env
    d = _draft(w)
    r = c.post(f"/api/audit/draft:{d.id}/decision", json={"decision": "approve"})
    assert r.status_code == 200
    assert r.json()["kind"] == "approved" and r.json()["decided_by"] == "human:test"
    assert w.get(d.id).decided_by == "human:test"


def test_reject_default_reason(env):
    c, w, _ = env
    d = _draft(w)
    r = c.post(f"/api/audit/draft:{d.id}/decision", json={"decision": "reject"})
    assert r.json()["kind"] == "rejected"
    assert w.get(d.id).reason == "화면에서 거절"


@pytest.mark.parametrize("key", ["reviewer", "decided_by", "reviewer_id", "requested_by"])
def test_identity_key_in_body_is_422(env, key):
    c, w, _ = env
    d = _draft(w)
    r = c.post(f"/api/audit/draft:{d.id}/decision", json={"decision": "approve", key: "human:x"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
    assert "human:x" not in r.text
    assert w.get(d.id).state.value == "draft"


def test_bad_decision_422(env):
    c, w, _ = env
    d = _draft(w)
    assert c.post(f"/api/audit/draft:{d.id}/decision", json={"decision": "x"}).status_code == 422


def test_double_decision_409(env):
    c, w, _ = env
    d = _draft(w)
    url = f"/api/audit/draft:{d.id}/decision"
    assert c.post(url, json={"decision": "approve"}).status_code == 200
    r = c.post(url, json={"decision": "approve"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "already_decided"


def test_non_draft_id_409(env):
    c, _, _ = env
    r = c.post("/api/audit/audit:run1:3/decision", json={"decision": "approve"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "not_decidable"


def test_unknown_draft_404(env):
    c, _, _ = env
    r = c.post("/api/audit/draft:nope/decision", json={"decision": "approve"})
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


def test_self_approval_403(tmp_path):
    s = Settings(tmp_path / "h.db", tmp_path / "a", tmp_path / "o", reviewer_id="human:same")
    init_db(s.hitl_db)
    d = DraftWriter(s.hitl_db, actor="human:same").create("source_request", {"host": "h.test"})
    c = TestClient(create_app(s))
    r = c.post(f"/api/audit/draft:{d.id}/decision", json={"decision": "approve"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "self_approval"


@pytest.mark.parametrize("rid", ["", "  ", "agent:x"])
def test_settings_reject_bad_reviewer(tmp_path, rid):
    with pytest.raises(ValueError):
        Settings(tmp_path / "h", tmp_path / "a", tmp_path / "o", reviewer_id=rid)


def test_settings_from_env_rejects_agent_reviewer():
    with pytest.raises(ValueError):
        Settings.from_env({"KC_REVIEWER_ID": "agent:bot"})


def test_settings_from_env_defaults():
    s = Settings.from_env({})
    assert s.reviewer_id == "human:demo" and s.cors_origins == ("http://localhost:8766",)
    assert s.hitl_db.name == "hitl.db"
    assert Settings.from_env({"KC_CORS_ORIGINS": "http://a, http://b"}).cors_origins == (
        "http://a",
        "http://b",
    )


def test_other_kind_not_listed(env):
    c, w, _ = env
    w.create("something_else", {"x": 1})
    assert c.get("/api/audit").json() == []


def test_unknown_route_error_shape(env):
    c, _, _ = env
    r = c.get("/api/nope")
    assert r.status_code == 404 and set(r.json()["error"]) == {"code", "message"}


# ---- 비신뢰 audit JSONL (D10): 깨진 줄·ts 혼재에도 200 ----
def _line(seq, ts, host="a.example"):
    import json

    from core.audit import SCHEMA

    return json.dumps(
        {
            "seq": seq, "ts": ts, "run_id": "r1", "actor": "agent:x", "phase": "observe",
            "kind": "net", "name": "net", "call_id": None,
            "data": {
                "host": host, "port": 443, "decision": "denied", "binary": None,
                "method": None, "path": None, "raw": None,
            },
            "source": "core.audit", "schema": SCHEMA,
        },
        ensure_ascii=False,
    )


def test_audit_bad_ts_mixed_naive_aware_and_empty(env):
    c, _, s = env
    s.audit_dir.mkdir()
    lines = [
        _line(1, "2026-10-07T01:00:00+00:00", "ok1.example"),
        _line(2, "2026-10-07T02:00:00", "naive.example"),  # naive
        _line(3, "2026-10-07T11:30:00+09:00", "kst.example"),  # aware 비-UTC
        _line(4, "not-a-time"),
        _line(5, ""),
        "{깨진 json",
        _line(6, "9999-12-31T23:59:59-23:00"),  # 범위 초과 가능
    ]
    (s.audit_dir / "r1.jsonl").write_text("\n".join(lines)+ "\n")
    (s.audit_dir / "r2.jsonl").write_bytes(b"\xff\xfe\x00bad")
    r = c.get("/api/audit")
    assert r.status_code == 200
    hosts = [e["text"]["ko"].split(":")[0] for e in r.json()]
    assert {"ok1.example", "naive.example", "kst.example"} <= set(hosts)
    assert "not-a-time" not in r.text and "r2" not in r.text and "Traceback" not in r.text
    assert int(r.headers["X-Audit-Skipped"]) >= 4
    ats = [e["at"] for e in r.json()]
    assert len(ats) >= 3
