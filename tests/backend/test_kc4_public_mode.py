from fastapi.testclient import TestClient

from backend import catalog_runner
from backend.app import create_app
from backend.settings import Settings

TOKEN = "s3cret-token-0123456789"


def _client(tmp_path, **o):
    s = Settings(hitl_db=tmp_path / "h.db", audit_dir=tmp_path / "a", output_dir=tmp_path / "o",
                 reviewer_id="human:t", catalog_dir=tmp_path / "c", admin_token=TOKEN, **o)
    return TestClient(create_app(s))


def _sess(c):
    return c.post("/api/session").json()["session"]


def test_public_audit_without_session_is_empty(tmp_path):
    c = _client(tmp_path, public_mode=True)  # 계약(§5.1): 세션 없음 GET /api/audit -> 200 []
    r = c.get("/api/audit")
    assert r.status_code == 200 and r.json() == []


def test_public_audit_only_own_session(tmp_path):
    c = _client(tmp_path, public_mode=True)
    a, b = _sess(c), _sess(c)
    sa = c.app.state.sessions.get(a)
    sa.logs.append({"id": "x1", "title": "mine"})
    ra = c.get("/api/audit", headers={"X-KC-Session": a})
    rb = c.get("/api/audit", headers={"X-KC-Session": b})
    assert ra.status_code == 200 and ra.json() == [{"id": "x1", "title": "mine"}]
    assert rb.json() == []


def test_public_audit_ignores_stores(tmp_path):
    c = _client(tmp_path, public_mode=True)
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "r.jsonl").write_text("garbage\n")
    t = _sess(c)
    r = c.get("/api/audit", headers={"X-KC-Session": t})
    assert r.json() == [] and "X-Audit-Skipped" not in r.headers


def test_public_closed_endpoints(tmp_path):
    c = _client(tmp_path, public_mode=True)
    h = {"X-KC-Session": _sess(c), "X-Admin-Token": TOKEN}
    calls = [
        c.post("/api/audit/draft:abc/decision", json={"decision": "approve"}, headers=h),
        c.get("/api/admin/review", headers=h),
        c.get("/api/admin/sources", headers=h),
        c.post("/api/admin/refresh/x", json={}, headers=h),
        c.post("/api/reports", json={"official_link": "https://a.kr", "reason": "r"}, headers=h),
    ]
    for r in calls:
        assert r.status_code == 403 and r.json()["error"]["code"] == "disabled_in_public"


def test_local_audit_unchanged(tmp_path):
    c = _client(tmp_path)
    assert c.get("/api/audit").json() == []


def test_local_decision_still_open(tmp_path):
    c = _client(tmp_path)
    r = c.post("/api/audit/draft:nope/decision", json={"decision": "approve"})
    assert r.status_code == 404


def test_local_admin_lockout(tmp_path, monkeypatch):
    monkeypatch.setattr(catalog_runner, "run_catalog", lambda *a, **k: {"ok": 1})
    from backend.routers import events
    monkeypatch.setattr(events, "run_catalog", lambda *a, **k: {"ok": 1})
    c = _client(tmp_path)
    for _ in range(5):
        r = c.get("/api/admin/sources", headers={"X-Admin-Token": "bad"})
        assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden"
    r = c.get("/api/admin/sources", headers={"X-Admin-Token": TOKEN})
    assert r.status_code == 403 and r.json()["error"]["code"] == "admin_blocked"


def test_local_admin_success_resets_fails(tmp_path, monkeypatch):
    from backend.routers import events
    monkeypatch.setattr(events, "run_catalog", lambda *a, **k: {"ok": 1})
    c = _client(tmp_path)
    for _ in range(4):
        c.get("/api/admin/sources", headers={"X-Admin-Token": "bad"})
    assert c.get("/api/admin/sources", headers={"X-Admin-Token": TOKEN}).status_code == 200
    for _ in range(4):
        c.get("/api/admin/sources", headers={"X-Admin-Token": "bad"})
    assert c.get("/api/admin/sources", headers={"X-Admin-Token": TOKEN}).status_code == 200


def test_catalog_busy_is_429(tmp_path, monkeypatch):
    from backend.routers import events

    def boom(*a, **k):
        raise catalog_runner.CatalogBusy("x")

    monkeypatch.setattr(events, "run_catalog", boom)
    c = _client(tmp_path, public_mode=True)
    r = c.get("/api/events/coverage", headers={"X-KC-Session": _sess(c)})
    assert r.status_code == 429 and r.json()["error"]["code"] == "busy"
    assert r.headers["Retry-After"]
