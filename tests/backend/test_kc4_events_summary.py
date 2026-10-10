"""T437 — 공개 행사 검색 응답의 excluded 요약(D30 ③)."""
import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.routers import events as ev
from backend.settings import Settings

TRIP = {"from": "2026-10-16", "to": "2026-10-16"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    s = Settings(hitl_db=tmp_path / "h.db", audit_dir=tmp_path / "a", output_dir=tmp_path / "o",
                 catalog_dir=tmp_path / "cat", reviewer_id="human:demo")
    calls = []

    def fake(_dir, op, args, actor=None):
        calls.append(op)
        excl = [{"title": f"t{i}", "reason": "기간 밖" if i % 3 else "구 밖"} for i in range(100)]
        return {"events": [{"id": "e1"}], "excluded": excl, "problems": [], "op": op}

    monkeypatch.setattr(ev, "run_catalog", fake)
    c = TestClient(create_app(s))
    c.calls = calls
    return c


def test_search_is_summarized(client):
    d = client.post("/api/events/search", json={"trip": TRIP}).json()
    assert len(d["excluded"]) == 20 and d["excluded"][0]["title"] == "t0"
    assert d["excluded_total"] == 100
    assert d["excluded_by_reason"] == {"기간 밖": 66, "구 밖": 34}
    assert d["problems"] == [] and d["events"] == [{"id": "e1"}]


def test_small_list_keeps_all_and_no_internal_problem(client, monkeypatch):
    monkeypatch.setattr(ev, "run_catalog", lambda *a, **k: {"events": [], "excluded": [{"title": "a", "reason": "r"}], "problems": []})
    d = client.post("/api/events/search", json={"trip": TRIP}).json()
    assert d["excluded_total"] == 1 and len(d["excluded"]) == 1 and d["problems"] == []


def test_other_ops_unchanged(client):
    d = client.post("/api/events/cards", json={"trip": TRIP}).json()
    assert len(d["excluded"]) == 100 and "excluded_total" not in d
    d = client.get("/api/events/abc").json()
    assert d["op"] == "detail" and "excluded_total" not in d
