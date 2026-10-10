import threading

import pytest
from fastapi.testclient import TestClient

from backend import catalog_runner
from backend.app import MAX_BODY_BYTES, create_app
from backend.settings import Settings

ORIGIN = "http://localhost:8766"


def _app(tmp_path, **o):
    s = Settings(hitl_db=tmp_path / "h.db", audit_dir=tmp_path / "a", output_dir=tmp_path / "o",
                 reviewer_id="human:t", catalog_dir=tmp_path / "c", **o)
    return create_app(s)


@pytest.fixture
def pub(tmp_path):
    return TestClient(_app(tmp_path, public_mode=True))


@pytest.fixture
def local(tmp_path):
    return TestClient(_app(tmp_path))


def test_meta_modes(pub, local):
    assert pub.get("/api/meta").json() == {"schema": "kc-meta/v1", "public": True,
                                            "decisions": "closed", "reports": "closed"}
    assert local.get("/api/meta").json() == {"schema": "kc-meta/v1", "public": False,
                                              "decisions": "open", "reports": "open"}


def test_session_issue(pub):
    r = pub.post("/api/session")
    assert r.status_code == 201
    j = r.json()
    assert len(j["session"]) == 43 and j["ttl_s"] == 7200


def test_docs_closed_public_open_local(pub, local):
    for p in ("/docs", "/redoc", "/openapi.json"):
        assert pub.get(p).status_code == 404
    assert local.get("/docs").status_code == 200
    assert local.get("/openapi.json").status_code == 200


def test_429_cors_via_global_rule(tmp_path, monkeypatch):
    from backend import limits
    monkeypatch.setitem(limits.RULES, "read", (limits.Rule("g", 2, 60, "global"),))
    c = TestClient(_app(tmp_path, public_mode=True))
    rs = [c.get("/api/meta", headers={"Origin": ORIGIN}) for _ in range(3)]
    assert [r.status_code for r in rs] == [200, 200, 429]
    r = rs[2]
    assert r.headers["access-control-allow-origin"] == ORIGIN
    assert int(r.headers["retry-after"]) >= 1
    assert r.json()["error"]["code"] == "rate_limited"
    assert "retry-after" in r.headers["access-control-expose-headers"].lower()


def test_ip_limit_off_without_hops(tmp_path, monkeypatch):
    from backend import limits
    monkeypatch.setitem(limits.RULES, "read", (limits.Rule("ip", 1, 60, "ip"),))
    c = TestClient(_app(tmp_path, public_mode=True))
    assert all(c.get("/api/meta", headers={"x-forwarded-for": "1.1.1.1"}).status_code == 200
               for _ in range(5))
    c2 = TestClient(_app(tmp_path, public_mode=True, trusted_proxy_hops=1))
    h = {"x-forwarded-for": "1.1.1.1"}
    assert c2.get("/api/meta", headers=h).status_code == 200
    assert c2.get("/api/meta", headers=h).status_code == 429


def test_413_has_cors(pub, local):
    for c in (pub, local):
        r = c.post("/api/messages", content=b"x", headers={
            "Origin": ORIGIN, "Content-Length": str(MAX_BODY_BYTES + 1)})
        assert r.status_code == 413
        assert r.headers["access-control-allow-origin"] == ORIGIN


def test_preflight_allows_session_header(pub):
    r = pub.options("/api/messages", headers={
        "Origin": ORIGIN, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "X-KC-Session, Content-Type"})
    assert r.status_code == 200
    assert "x-kc-session" in r.headers["access-control-allow-headers"].lower()


def test_gzip_for_large_responses(local):
    r = local.get("/openapi.json", headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200 and len(r.content) > 0
    assert r.headers.get("content-encoding") == "gzip"
    plain = local.get("/openapi.json", headers={"Accept-Encoding": "identity"})  # Accept-Encoding 없으면 압축하지 않는다
    assert "content-encoding" not in plain.headers


def test_local_mode_has_no_rate_limit(tmp_path, monkeypatch):
    from backend import limits
    monkeypatch.setitem(limits.RULES, "read", (limits.Rule("g", 1, 60, "global"),))
    c = TestClient(_app(tmp_path))
    assert all(c.get("/api/meta").status_code == 200 for _ in range(5))


def test_catalog_busy_over_two(monkeypatch, tmp_path):
    started = threading.Semaphore(0)
    release = threading.Event()

    def fake_run(*a, **k):
        started.release()
        release.wait(5)
        return type("P", (), {"returncode": 0, "stdout": "{}", "stderr": ""})()

    monkeypatch.setattr(catalog_runner.subprocess, "run", fake_run)
    catalog_runner.configure_concurrency(2)
    ts = [threading.Thread(target=catalog_runner.run_catalog, args=(tmp_path, "x", {})) for _ in range(2)]
    for t in ts:
        t.start()
    for _ in range(2):
        assert started.acquire(timeout=5)
    with pytest.raises(catalog_runner.CatalogBusy):
        catalog_runner.run_catalog(tmp_path, "x", {})
    release.set()
    for t in ts:
        t.join()
    assert catalog_runner.run_catalog(tmp_path, "x", {}) == {}  # 슬롯 반납 확인
    catalog_runner.configure_concurrency(2)


def test_catalog_busy_is_runner_error_and_range():
    assert issubclass(catalog_runner.CatalogBusy, catalog_runner.CatalogRunnerError)
    with pytest.raises(ValueError):
        catalog_runner.configure_concurrency(0)
