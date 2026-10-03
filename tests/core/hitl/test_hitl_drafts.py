import inspect
import sqlite3

import pytest

from core.hitl import (
    DbNotFoundError,
    DraftState,
    DraftValidationError,
    DraftWriter,
    SchemaMissingError,
    init_db,
)


@pytest.fixture
def db(tmp_path):
    p = tmp_path / "hitl.db"
    init_db(p)
    return p


@pytest.fixture
def w(db):
    return DraftWriter(db, actor="agent:run-1")


def test_create_returns_draft_state(w):
    d = w.create("note", {"a": 1})
    assert d.state is DraftState.DRAFT
    assert d.created_by == "agent:run-1"
    assert d.decided_by is None and d.decided_at is None and d.reason is None
    assert d.payload == {"a": 1}
    assert w.get(d.id) == d


def test_create_signature_has_no_identity_param():
    assert set(inspect.signature(DraftWriter.create).parameters) == {"self", "kind", "payload"}


def test_payload_state_key_does_not_change_state(w):
    d = w.create("note", {"state": "approved", "created_by": "x"})
    assert d.state is DraftState.DRAFT and d.created_by == "agent:run-1"
    assert d.payload["state"] == "approved"


@pytest.mark.parametrize("kind", ["Bad Kind", "", "1abc"])
def test_invalid_kind_rejected(w, kind):
    with pytest.raises(DraftValidationError):
        w.create(kind, {})


def test_unserializable_payload_rejected(w):
    with pytest.raises(DraftValidationError):
        w.create("note", {"x": object()})


def test_oversize_payload_rejected(w):
    with pytest.raises(DraftValidationError):
        w.create("note", {"x": "a" * (256 * 1024)})


@pytest.mark.parametrize("actor", ["", "  ", None])
def test_empty_actor_rejected(db, actor):
    with pytest.raises(ValueError):
        DraftWriter(db, actor=actor)


def test_schema_missing_raises(tmp_path):
    p = tmp_path / "e.db"
    sqlite3.connect(p).close()
    with pytest.raises(SchemaMissingError):
        DraftWriter(p, actor="a")


def test_writer_missing_db_raises(tmp_path):
    p = tmp_path / "none.db"
    with pytest.raises(DbNotFoundError):
        DraftWriter(p, actor="a")
    assert not p.exists()


def test_get_unknown_raises(w):
    from core.hitl import DraftNotFound

    with pytest.raises(DraftNotFound):
        w.get("nope")


def test_list_drafts_filters_and_order(w):
    a = w.create("alpha", {})
    b = w.create("beta", {})
    c = w.create("alpha", {})
    ids = [d.id for d in w.list_drafts()]
    assert set(ids) == {a.id, b.id, c.id}
    keys = [(d.created_at, d.id) for d in w.list_drafts()]
    assert keys == sorted(keys)
    assert {d.id for d in w.list_drafts(kind="alpha")} == {a.id, c.id}
    assert w.list_drafts(state=DraftState.APPROVED) == []
    assert len(w.list_drafts(limit=2)) == 2


@pytest.mark.parametrize("limit", [0, 1001])
def test_list_drafts_limit_bounds(w, limit):
    with pytest.raises(ValueError):
        w.list_drafts(limit=limit)
