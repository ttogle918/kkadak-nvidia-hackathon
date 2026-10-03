import inspect
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

import core.hitl
from core.hitl import (
    DraftNotFound,
    DraftState,
    DraftValidationError,
    DraftWriter,
    SelfApprovalError,
    TransitionError,
    init_db,
)
from core.hitl.review import ReviewDesk, Reviewer, _connect_reviewer

ROOT = Path(__file__).resolve().parents[3]
ALICE = Reviewer(id="alice", auth_source="test")


@pytest.fixture
def db(tmp_path):
    p = tmp_path / "hitl.db"
    init_db(p)
    return p


@pytest.fixture
def w(db):
    return DraftWriter(db, actor="agent:1")


@pytest.fixture
def desk(db):
    return ReviewDesk(db)


def test_approve_transitions_and_records_reviewer(w, desk):
    d = w.create("note", {})
    r = desk.approve(d.id, reviewer=ALICE)
    assert r.state is DraftState.APPROVED
    assert r.decided_by == "alice" and r.decided_at
    assert w.get(d.id) == r


def test_reject_requires_reason(w, desk):
    d = w.create("note", {})
    for reason in ("", "   ", None):
        with pytest.raises(DraftValidationError):
            desk.reject(d.id, reviewer=ALICE, reason=reason)
    r = desk.reject(d.id, reviewer=ALICE, reason="no")
    assert r.state is DraftState.REJECTED and r.reason == "no"


def test_double_approve_raises_transition_error(w, desk):
    d = w.create("note", {})
    desk.approve(d.id, reviewer=ALICE)
    with pytest.raises(TransitionError) as ei:
        desk.approve(d.id, reviewer=ALICE)
    assert ei.value.current is DraftState.APPROVED
    assert ei.value.target is DraftState.APPROVED
    assert ei.value.draft_id == d.id


def test_approve_after_reject_raises(w, desk):
    d = w.create("note", {})
    desk.reject(d.id, reviewer=ALICE, reason="x")
    with pytest.raises(TransitionError):
        desk.approve(d.id, reviewer=ALICE)


def test_unknown_id_raises_not_found(desk):
    with pytest.raises(DraftNotFound):
        desk.approve("nope", reviewer=ALICE)


def test_self_approval_forbidden(w, desk):
    d = w.create("note", {})
    with pytest.raises(SelfApprovalError):
        desk.approve(d.id, reviewer=Reviewer(id="agent:1", auth_source="test"))
    assert w.get(d.id).state is DraftState.DRAFT


def test_reviewer_must_be_reviewer_instance(w, desk):
    d = w.create("note", {})
    with pytest.raises(TypeError):
        desk.approve(d.id, reviewer="alice")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        desk.reject(d.id, reviewer={"id": "a"}, reason="x")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kw",
    [
        {"id": "", "auth_source": "t"},
        {"id": "  ", "auth_source": "t"},
        {"id": 123, "auth_source": "t"},
        {"id": "a", "auth_source": ""},
    ],
)
def test_reviewer_fields_validated(kw):
    with pytest.raises(ValueError):
        Reviewer(**kw)


def test_approve_signature_identity_only_via_reviewer():
    names = {"self", "draft_id", "reviewer", "reason"}
    assert set(inspect.signature(ReviewDesk.approve).parameters) == names
    assert set(inspect.signature(ReviewDesk.reject).parameters) == names


def test_desk_missing_db_raises(tmp_path):
    from core.hitl import DbNotFoundError

    with pytest.raises(DbNotFoundError):
        ReviewDesk(tmp_path / "none.db")
    assert not (tmp_path / "none.db").exists()


def test_reviewer_conn_updates_allowed_columns_only(w, db):
    w.create("note", {})
    c = _connect_reviewer(db)
    with pytest.raises(sqlite3.DatabaseError):
        c.execute("UPDATE drafts SET payload='{}'")
    with pytest.raises(sqlite3.DatabaseError):
        c.execute("DELETE FROM drafts")
    with pytest.raises(sqlite3.DatabaseError):
        c.execute(
            "INSERT INTO drafts(id,kind,payload,state,created_by,created_at)"
            " VALUES ('x','k','{}','draft','a','t')"
        )


def test_core_hitl_all_is_exact():
    assert set(core.hitl.__all__) == {
        "Draft", "DraftState", "DraftWriter", "init_db", "connect", "HitlError", "DraftNotFound",
        "TransitionError", "SelfApprovalError", "DraftValidationError", "SchemaMissingError",
        "DbNotFoundError",
    }


def test_core_hitl_does_not_export_review():
    # 같은 프로세스에서 review 를 import 하면 서브모듈 속성이 붙으므로 새 프로세스에서 확인한다
    code = (
        "import core.hitl; n=set(dir(core.hitl)); "
        "print([x for x in ('approve','reject','ReviewDesk','Reviewer','_connect_reviewer',"
        "'review','_open_existing','_agent_authorizer') if x in n])"
    )
    r = _run(code)
    assert r.returncode == 0 and r.stdout.strip() == "[]"


def _run(code, **env):
    e = dict(os.environ)
    e.update(env)
    return subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=e, capture_output=True, text=True, check=False
    )


def test_import_core_hitl_does_not_load_review():
    r = _run("import sys, core.hitl; print('core.hitl.review' in sys.modules)")
    assert r.returncode == 0 and r.stdout.strip() == "False"


def test_review_import_blocked_in_agent_process():
    r = _run("import core.hitl.review", APP_PROCESS_ROLE="agent")
    assert r.returncode != 0 and "ImportError" in r.stderr
