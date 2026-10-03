"""쓰기 경계 (SCOPE 5 · D2): 에이전트 경로는 draft 생성 외에는 쓸 수 없다.

reviewer 연결(`_connect_reviewer`)과 authorizer 없는 우회 연결은 테스트에서 사람 쪽 코드로
취급한다(비공개 함수 사용은 의도된 예외).
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from core import hitl
from core.hitl import DraftState, DraftWriter, connect, init_db
from core.hitl.review import ReviewDesk, Reviewer, _connect_reviewer

# 락 오류("database is locked")를 거부로 오인하지 않도록, 거부 사유는 이 문구 중 하나여야 한다.
_DENY_MARKERS = (
    "not authorized",
    "insert must be a fresh plain draft",
    "illegal update",
    "terminal rows cannot be deleted",
)

_INS = "INSERT INTO drafts(id,kind,payload,state,created_by,created_at) "


def _is_denial(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return "locked" not in msg and any(m in msg for m in _DENY_MARKERS)


def _snapshot(db: Path) -> list[tuple]:
    conn = sqlite3.connect(db)
    try:
        return conn.execute("SELECT * FROM drafts ORDER BY id").fetchall()
    finally:
        conn.close()


def _attempt(conn: sqlite3.Connection, sql: str, params=()) -> sqlite3.DatabaseError | None:
    """문장을 실행하고 예외를 돌려준다. 어떤 경우든 rollback·close 해 락을 남기지 않는다."""
    try:
        conn.execute(sql, params)
        conn.commit()
    except sqlite3.DatabaseError as exc:
        return exc
    finally:
        try:
            conn.rollback()
        finally:
            conn.close()
    return None


def _assert_denied(exc: sqlite3.DatabaseError | None) -> None:
    assert exc is not None, "거부되어야 하는데 성공했다"
    assert _is_denial(exc), f"트리거/authorizer 거부가 아니다: {exc!r}"


def _assert_not_authorized(exc: sqlite3.DatabaseError | None) -> None:
    """authorizer 가 막은 것만 통과시킨다. 트리거 문구(`illegal update` 등)로는 통과하지 않는다."""
    assert exc is not None, "거부되어야 하는데 성공했다"
    assert "not authorized" in str(exc), f"authorizer 거부가 아니다: {exc!r}"


@pytest.fixture
def db(tmp_path: Path) -> Path:
    p = tmp_path / "hitl.db"
    init_db(p)
    return p


@pytest.fixture
def writer(db: Path) -> DraftWriter:
    return DraftWriter(db, actor="agent:test-run")


@pytest.fixture
def desk(db: Path) -> ReviewDesk:
    return ReviewDesk(db)


@pytest.fixture
def human() -> Reviewer:
    return Reviewer(id="human:alice", auth_source="test")


@pytest.fixture
def rows(db, writer, desk, human):
    """승인 1·반려 1·draft 1 인 DB. 각 id 를 돌려준다."""
    a = writer.create("note", {"n": 1})
    b = writer.create("note", {"n": 2})
    c = writer.create("note", {"n": 3})
    desk.approve(a.id, reviewer=human, reason="ok")
    desk.reject(c.id, reviewer=human, reason="no")
    return {"approved": a.id, "draft": b.id, "rejected": c.id}


# 1
def test_agent_can_create_draft(writer):
    d = writer.create("note", {"text": "hello"})
    assert d.state == DraftState.DRAFT
    assert d.created_by == "agent:test-run"
    assert d.decided_by is None


# 2
def test_public_connect_is_agent_only(db, writer):
    with pytest.raises(TypeError):
        connect(db, "reviewer")  # type: ignore[call-arg]
    writer.create("note", {})
    exc = _attempt(connect(db), "UPDATE drafts SET state='approved'")
    _assert_not_authorized(exc)


# 3
def test_agent_conn_update_denied(db, writer):
    writer.create("note", {})
    _assert_not_authorized(_attempt(connect(db), "UPDATE drafts SET state='approved'"))


# 4
def test_agent_conn_delete_denied(db, writer):
    writer.create("note", {})
    _assert_not_authorized(_attempt(connect(db), "DELETE FROM drafts"))


# 5
def test_agent_conn_insert_approved_denied(db):
    exc = _attempt(
        connect(db),
        _INS + "VALUES ('x','note','{}','approved','agent:a','2026-01-01T00:00:00.000+00:00')",
    )
    _assert_denied(exc)
    assert "insert must be a fresh plain draft" in str(exc)


# 6
@pytest.mark.parametrize(
    "sql",
    [
        "CREATE TABLE x(a)",
        "DROP TRIGGER drafts_update_guard",
        "DROP TRIGGER drafts_insert_only_draft",
        "DROP TRIGGER drafts_no_delete_terminal",
        "CREATE TRIGGER t BEFORE INSERT ON drafts BEGIN SELECT 1; END",
        "DROP TABLE drafts",
        "ALTER TABLE drafts ADD COLUMN z TEXT",
        "CREATE INDEX i ON drafts(kind)",
    ],
)
def test_agent_conn_ddl_denied(db, sql):
    before = _snapshot(db)
    _assert_not_authorized(_attempt(connect(db), sql))
    assert _snapshot(db) == before
    connect(db).close()  # 트리거 3종이 남아 있어 여전히 열린다


# 7
def test_agent_conn_attach_denied(db, tmp_path):
    other = tmp_path / "other.db"
    _assert_not_authorized(_attempt(connect(db), f"ATTACH DATABASE '{other}' AS o"))
    assert not other.exists()


# 8
@pytest.mark.parametrize("sql", ["PRAGMA writable_schema=ON", "PRAGMA recursive_triggers=ON"])
def test_agent_conn_pragma_denied(db, sql):
    _assert_not_authorized(_attempt(connect(db), sql))


# W3: VACUUM 은 authorizer 액션 코드 없이 SQLite 가 별도로 거부한다(실측: "authorization denied").
# VACUUM INTO 는 DB 를 복사하는 유출 경로가 될 수 있어 파일이 생기지 않음까지 고정한다.
def test_agent_conn_vacuum_denied(db, writer):
    writer.create("note", {})
    before = _snapshot(db)
    exc = _attempt(connect(db), "VACUUM")
    assert exc is not None and "authorization denied" in str(exc), repr(exc)
    assert _snapshot(db) == before


def test_agent_conn_vacuum_into_denied(db, writer, tmp_path):
    writer.create("note", {})
    copy = tmp_path / "copy.db"
    exc = _attempt(connect(db), f"VACUUM INTO '{copy}'")
    assert exc is not None and "authorization denied" in str(exc), repr(exc)
    assert not copy.exists()


# 9
def test_reviewer_conn_insert_denied(db):
    exc = _attempt(
        _connect_reviewer(db),
        _INS + "VALUES ('x','note','{}','draft','human:a','2026-01-01T00:00:00.000+00:00')",
    )
    _assert_denied(exc)


def test_reviewer_conn_delete_denied(db, writer):
    writer.create("note", {})
    _assert_denied(_attempt(_connect_reviewer(db), "DELETE FROM drafts"))


# 10
def test_reviewer_conn_cannot_update_payload(db, writer):
    writer.create("note", {"a": 1})
    before = _snapshot(db)
    # reviewer authorizer 의 컬럼 화이트리스트가 막는다 (실측 메시지: "not authorized").
    _assert_not_authorized(_attempt(_connect_reviewer(db), "UPDATE drafts SET payload='{}'"))
    assert _snapshot(db) == before


# 11
@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE drafts SET reason='x' WHERE id=?",
        "UPDATE drafts SET decided_by='human:mallory' WHERE id=?",
        "UPDATE drafts SET state='draft' WHERE id=?",
        "UPDATE drafts SET state='rejected', decided_by='human:m', decided_at='t' WHERE id=?",
    ],
)
@pytest.mark.parametrize("which", ["approved", "rejected"])
def test_reviewer_conn_cannot_tamper_terminal_row(db, rows, sql, which):
    before = _snapshot(db)
    exc = _attempt(_connect_reviewer(db), sql, (rows[which],))
    _assert_denied(exc)
    assert "illegal update" in str(exc)  # 트리거가 막는 경로(authorizer 는 허용 컬럼)
    assert _snapshot(db) == before


# 12
def test_reviewer_conn_cannot_edit_draft_without_transition(db, writer):
    d = writer.create("note", {})
    before = _snapshot(db)
    exc = _attempt(_connect_reviewer(db), "UPDATE drafts SET reason='x' WHERE id=?", (d.id,))
    _assert_denied(exc)
    assert "illegal update" in str(exc)
    assert _snapshot(db) == before


# 13
_SELF_APPROVE = (
    "UPDATE drafts SET state='approved', decided_by='human:mallory', "
    "decided_at='2026-01-01T00:00:00.000+00:00'"
)


def test_state_unchanged_after_denied_attempts(db, rows, tmp_path):
    before = _snapshot(db)
    assert len(before) == 3
    attempts = [
        (connect, _INS + "VALUES ('x','note','{}','approved','agent:a','t')", ()),
        (connect, f"ATTACH DATABASE '{tmp_path / 'o.db'}' AS o", ()),
        (connect, "UPDATE drafts SET state='approved'", ()),
        (connect, _SELF_APPROVE, ()),
        (connect, "DELETE FROM drafts", ()),
        (connect, "DROP TRIGGER drafts_update_guard", ()),
        (connect, "PRAGMA writable_schema=ON", ()),
        (_connect_reviewer, _INS + "VALUES ('z','n','{}','draft','h','t')", ()),
        (_connect_reviewer, "DELETE FROM drafts", ()),
        (_connect_reviewer, "UPDATE drafts SET payload='{}'", ()),
        (_connect_reviewer, "UPDATE drafts SET reason='x' WHERE id=?", (rows["approved"],)),
        (_connect_reviewer, "UPDATE drafts SET reason='x' WHERE id=?", (rows["draft"],)),
    ]
    for opener, sql, params in attempts:
        exc = _attempt(opener(db), sql, params)
        _assert_denied(exc)
        if opener is connect and "insert" not in sql.lower():
            _assert_not_authorized(exc)  # agent 연결의 쓰기·DDL 은 authorizer 가 막는다
        assert _snapshot(db) == before, sql
    assert not (tmp_path / "o.db").exists()


# B1: 트리거(`decided_by IS NULL` 등)를 통과하는 "정상 형태" 자기 승인 UPDATE.
# 이 경로를 막는 장치는 agent authorizer 하나뿐이므로 "not authorized" 로 고정한다.
_FORGED_TRANSITIONS = {
    "approve": _SELF_APPROVE + " WHERE id=?",
    "approve_all": _SELF_APPROVE,
    "reject": "UPDATE drafts SET state='rejected', decided_by='human:mallory', "
    "decided_at='2026-01-01T00:00:00.000+00:00' WHERE id=?",
    "or_replace": "UPDATE OR REPLACE drafts SET state='approved', decided_by='human:mallory', "
    "decided_at='2026-01-01T00:00:00.000+00:00' WHERE id=?",
}


def _bind(sql: str, draft_id: str) -> tuple:
    return (draft_id,) if "WHERE id=?" in sql else ()


@pytest.mark.parametrize("name", list(_FORGED_TRANSITIONS))
def test_agent_conn_self_approval_denied_by_authorizer(db, writer, name):
    d = writer.create("note", {"n": 1})
    before = _snapshot(db)
    sql = _FORGED_TRANSITIONS[name]
    _assert_not_authorized(_attempt(connect(db), sql, _bind(sql, d.id)))
    assert _snapshot(db) == before
    assert writer.get(d.id).state == DraftState.DRAFT


def test_agent_conn_decided_by_only_denied_by_authorizer(db, writer):
    d = writer.create("note", {})
    before = _snapshot(db)
    sql = "UPDATE drafts SET decided_by='human:mallory' WHERE id=?"
    _assert_not_authorized(_attempt(connect(db), sql, (d.id,)))
    assert _snapshot(db) == before


# 대조 실험(회귀 고정): authorizer 없는 연결에서는 같은 문장이 성공한다. 즉 트리거만으로는
# 자기 승인을 못 막고 agent authorizer 가 유일한 방어다. 이 테스트가 실패하면(=트리거가 강화되어
# 문장이 막히면) 위 B1 테스트의 전제를 다시 검토해야 한다. 연결은 롤백 후 닫아 DB 를 바꾸지 않는다.
@pytest.mark.parametrize("name", ["approve", "approve_all", "reject", "or_replace"])
def test_control_same_update_succeeds_without_authorizer(db, writer, name):
    d = writer.create("note", {"n": 1})
    before = _snapshot(db)
    sql = _FORGED_TRANSITIONS[name]
    conn = sqlite3.connect(db)
    try:
        cur = conn.execute(sql, _bind(sql, d.id))
        assert cur.rowcount == 1, "authorizer 없는 연결에서는 전이 UPDATE 가 통과해야 한다"
    finally:
        conn.rollback()
        conn.close()
    assert _snapshot(db) == before


# 14
def test_only_review_path_transitions(db, writer, desk, human):
    d = writer.create("note", {})
    assert desk.approve(d.id, reviewer=human).state == DraftState.APPROVED
    for name in hitl.__all__:
        assert "approve" not in name.lower() and "reject" not in name.lower()
    assert not hasattr(hitl, "_connect_reviewer")
    assert not hasattr(hitl, "ReviewDesk") and not hasattr(hitl, "Reviewer")
    for attr in ("approve", "reject"):
        assert not hasattr(DraftWriter, attr)
    # core.hitl 은 review 를 로드하지 않는다 (같은 프로세스에서는 서브모듈 속성이 붙어 서브프로세스로)
    code = (
        "import sys, core.hitl; "
        "assert 'core.hitl.review' not in sys.modules; "
        "assert not hasattr(core.hitl, 'review')"
    )
    root = Path(__file__).resolve().parent.parent
    r = subprocess.run(
        [sys.executable, "-c", code], cwd=root, capture_output=True, text=True, check=False
    )
    assert r.returncode == 0, r.stderr


# --- Stage 1 reviewer 권고 4: id 충돌·위조 경로 ---

_TERM_COLS = "(id,kind,payload,state,created_by,created_at)"


def _update_id_variants(approved_id: str, other_id: str) -> list[tuple[str, tuple]]:
    ins = f"INTO drafts{_TERM_COLS} "
    vals = "VALUES (?,'note','{}','draft','agent:evil','t')"
    return [
        ("UPDATE OR REPLACE drafts SET id=? WHERE id=?", (approved_id, other_id)),
        ("UPDATE OR IGNORE drafts SET id=? WHERE id=?", (approved_id, other_id)),
        ("UPDATE drafts SET id=? WHERE id=?", (approved_id, other_id)),
        (
            "UPDATE OR REPLACE drafts SET id=?, state='approved', decided_by='h', "
            + "decided_at='t' WHERE id=?",
            (approved_id, other_id),
        ),
        ("INSERT OR REPLACE " + ins + vals, (approved_id,)),
        ("INSERT OR IGNORE " + ins + vals, (approved_id,)),
        ("INSERT " + ins + vals + " ON CONFLICT(id) DO UPDATE SET payload='{}'", (approved_id,)),
        (
            "INSERT OR REPLACE INTO drafts SELECT ?, kind, payload, 'draft', created_by, "
            + "created_at, NULL, NULL, NULL FROM drafts WHERE id=?",
            (approved_id, other_id),
        ),
    ]


@pytest.mark.parametrize("conn_kind", ["bypass", "reviewer"])
@pytest.mark.parametrize("variant", range(8))
def test_update_or_replace_cannot_overwrite_terminal_id(db, rows, conn_kind, variant):
    sql, params = _update_id_variants(rows["approved"], rows["draft"])[variant]
    before = _snapshot(db)
    conn = sqlite3.connect(db) if conn_kind == "bypass" else _connect_reviewer(db)
    exc = _attempt(conn, sql, params)
    _assert_denied(exc)
    assert _snapshot(db) == before


_REPLACE_VARIANTS = [
    "INSERT OR REPLACE " + f"INTO drafts{_TERM_COLS} VALUES (:id,'note','{{}}','draft','a','t')",
    "REPLACE " + f"INTO drafts{_TERM_COLS} VALUES (:id,'note','{{}}','draft','a','t')",
    "INSERT OR IGNORE " + f"INTO drafts{_TERM_COLS} VALUES (:id,'note','{{}}','draft','a','t')",
    f"INSERT INTO drafts{_TERM_COLS} VALUES (:id,'note','{{}}','draft','a','t') "
    + "ON CONFLICT(id) DO UPDATE SET payload='{}', state='draft'",
    f"INSERT INTO drafts{_TERM_COLS} VALUES (:id,'note','{{}}','draft','a','t') "
    + "ON CONFLICT(id) DO NOTHING",
    f"INSERT OR REPLACE INTO drafts{_TERM_COLS} "
    + "SELECT id, kind, '{}', 'draft', created_by, created_at FROM drafts WHERE id=:id",
    f"INSERT INTO drafts{_TERM_COLS} "
    + "SELECT id, kind, '{}', 'draft', created_by, created_at FROM drafts WHERE id=:id",
]


@pytest.mark.parametrize("which", ["approved", "rejected"])
@pytest.mark.parametrize("sql", _REPLACE_VARIANTS)
def test_agent_conn_replace_cannot_overwrite_approved(db, rows, sql, which):
    before = _snapshot(db)
    exc = _attempt(connect(db), sql, {"id": rows[which]})
    _assert_denied(exc)
    assert _snapshot(db) == before


_FORGED_VARIANTS = [
    "VALUES (:id,'note','{}','draft','a','t','human:x',NULL,NULL)",
    "VALUES (:id,'note','{}','draft','a','t',NULL,'2026-01-01T00:00:00.000+00:00',NULL)",
    "VALUES (:id,'note','{}','draft','a','t',NULL,NULL,'looks fine')",
    "VALUES (:id,'note','{}','draft','a','t','human:x','2026-01-01T00:00:00.000+00:00','ok')",
    "VALUES (:id,'note','{}','approved','a','t','human:x','2026-01-01T00:00:00.000+00:00','ok')",
    "SELECT :id,'note','{}','draft','a','t','human:x','t','ok'",
]
_FORGED_VERBS = [
    "INSERT INTO",
    "INSERT OR REPLACE INTO",
    "INSERT OR IGNORE INTO",
    "REPLACE INTO",
]


@pytest.mark.parametrize("verb", _FORGED_VERBS)
@pytest.mark.parametrize("tail", _FORGED_VARIANTS)
def test_forged_decision_fields_on_insert_denied(db, rows, verb, tail):
    before = _snapshot(db)
    sql = f"{verb} drafts(id,kind,payload,state,created_by,created_at,decided_by,decided_at,"
    sql += f"reason) {tail}"
    exc = _attempt(connect(db), sql, {"id": "fresh-forged"})
    _assert_denied(exc)
    assert "insert must be a fresh plain draft" in str(exc)
    assert _snapshot(db) == before


def test_forged_decision_fields_upsert_and_insert_select_denied(db, rows):
    before = _snapshot(db)
    cols = "drafts(id,kind,payload,state,created_by,created_at,decided_by)"
    for sql in (
        f"INSERT INTO {cols} VALUES (:id,'n','{{}}','draft','a','t','human:x') "
        + "ON CONFLICT(id) DO UPDATE SET payload='{}'",
        f"INSERT INTO {cols} SELECT :id,'n','{{}}','draft','a','t','human:x' FROM drafts",
    ):
        _assert_denied(_attempt(connect(db), sql, {"id": "fresh-forged"}))
    assert _snapshot(db) == before
