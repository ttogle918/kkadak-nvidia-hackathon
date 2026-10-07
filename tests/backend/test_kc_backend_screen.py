import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.settings import REPO_ROOT, Settings

FIX = REPO_ROOT / "backend" / "fixtures" / "screen"


def _client(tmp_path, fixture_dir=None):
    s = Settings(
        hitl_db=tmp_path / "h.db", audit_dir=tmp_path / "a", output_dir=tmp_path / "o",
        reviewer_id="human:t", **({"screen_fixture_dir": fixture_dir} if fixture_dir else {}),
    )
    return TestClient(create_app(s))


@pytest.fixture
def c(tmp_path):
    return _client(tmp_path)


def test_cards_list_and_detail(c):
    r = c.get("/api/cards")
    assert r.status_code == 200
    cards = r.json()
    assert len(cards) == 6
    one = c.get(f"/api/cards/{cards[0]['id']}")
    assert one.status_code == 200 and one.json() == cards[0]


def test_cards_have_sources_and_no_identity_fields(c):
    for card in c.get("/api/cards").json():
        assert card["sources"]
        assert not {"user", "user_id", "reviewer", "approved_by", "requester"} & set(card)


def test_sources(c):
    r = c.get("/api/sources")
    assert r.status_code == 200
    assert [s["id"] for s in r.json()][:2] == ["doc_01", "doc_02"]
    assert all(s["tier"] in "SABCD" for s in r.json())


def test_rationale(c):
    cards = c.get("/api/cards").json()
    for card in cards:
        r = c.get(f"/api/cards/{card['id']}/rationale")
        assert r.status_code == 200
        assert r.json()["card_id"] == card["id"]


def test_unknown_id_404(c):
    for path in ("/api/cards/nope", "/api/cards/nope/rationale"):
        r = c.get(path)
        assert r.status_code == 404
        assert r.json() == {"error": {"code": "not_found", "message": "찾을 수 없다"}}


@pytest.mark.parametrize("bad", ["a" * 65, "a.b", "a%20b", "..%2f..%2fetc", "a;b", "한글"])
def test_bad_id_422_without_echo(c, bad):
    for suffix in ("", "/rationale"):
        r = c.get(f"/api/cards/{bad}{suffix}")
        assert r.status_code in (404, 422)
        assert bad not in r.text
    if "%2f" not in bad:
        assert c.get(f"/api/cards/{bad}").status_code == 422


def test_read_only(c):
    for path in ("/api/cards", "/api/cards/card_old_1", "/api/sources", "/api/cards/card_old_1/rationale"):
        for m in ("post", "put", "patch", "delete"):
            assert getattr(c, m)(path).status_code in (404, 405)


def test_broken_fixture_gives_fixed_500_without_path(tmp_path):
    d = tmp_path / "secret_dir_name"
    d.mkdir()
    (d / "cards.json").write_text("{not json", encoding="utf-8")
    cl = _client(tmp_path, d)
    for path in ("/api/cards", "/api/sources", "/api/cards/card_old_1", "/api/cards/card_old_1/rationale"):
        r = cl.get(path)
        assert r.status_code == 500
        assert r.json() == {"error": {"code": "internal_error", "message": "처리 중 오류가 발생했다"}}
        assert "secret_dir_name" not in r.text and "json" not in r.text.lower()


def test_fixture_dir_is_configurable(tmp_path):
    d = tmp_path / "fx"
    shutil.copytree(FIX, d)
    cards = json.loads((d / "cards.json").read_text(encoding="utf-8"))[:1]
    (d / "cards.json").write_text(json.dumps(cards), encoding="utf-8")
    assert len(_client(tmp_path, d).get("/api/cards").json()) == 1
    env = Settings.from_env({"KC_SCREEN_FIXTURE_DIR": str(d)})
    assert env.screen_fixture_dir == Path(d)
