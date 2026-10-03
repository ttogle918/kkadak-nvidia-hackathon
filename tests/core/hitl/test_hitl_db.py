import inspect
import sqlite3

import pytest

from core.hitl import DbNotFoundError, SchemaMissingError, connect, init_db


@pytest.fixture
def db(tmp_path):
    p = tmp_path / "hitl.db"
    init_db(p)
    return p


def _raw(db, state="draft", decided=False):
    c = sqlite3.connect(db)
    c.execute(
        "INSERT INTO drafts(id,kind,payload,state,created_by,created_at,decided_by,decided_at)"
        " VALUES ('d1','k','{}','draft','a','t0',NULL,NULL)"
    )
    if state != "draft":
        c.execute(
            "UPDATE drafts SET state=?, decided_by='h', decided_at='t1' WHERE id='d1'", (state,)
        )
    c.commit()
    return c


def test_init_db_idempotent(db):
    init_db(db)
    init_db(db)


def test_init_db_missing_parent_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        init_db(tmp_path / "nope" / "x.db")


def test_connect_has_no_role_param(db):
    assert list(inspect.signature(connect).parameters) == ["path"]
    with pytest.raises(TypeError):
        connect(db, "reviewer")  # type: ignore[call-arg]


def test_connect_missing_db_raises_and_creates_nothing(tmp_path):
    p = tmp_path / "none.db"
    with pytest.raises(DbNotFoundError):
        connect(p)
    assert not p.exists()


def test_memory_path_rejected():
    with pytest.raises(ValueError):
        connect(":memory:")
    with pytest.raises(ValueError):
        init_db(":memory:")


def test_connect_schema_missing(tmp_path):
    p = tmp_path / "empty.db"
    sqlite3.connect(p).close()
    with pytest.raises(SchemaMissingError):
        connect(p)


def test_agent_conn_update_denied_smoke(db):
    _raw(db).close()
    with pytest.raises(sqlite3.DatabaseError):
        connect(db).execute("UPDATE drafts SET state='approved'")


def test_agent_conn_delete_and_ddl_denied(db):
    c = connect(db)
    for sql in ("DELETE FROM drafts", "DROP TABLE drafts", "PRAGMA user_version=1",
                "DROP TRIGGER drafts_update_guard"):
        with pytest.raises(sqlite3.DatabaseError):
            c.execute(sql)


def test_insert_non_draft_state_blocked_by_trigger(db):
    c = sqlite3.connect(db)
    with pytest.raises(sqlite3.DatabaseError):
        c.execute(
            "INSERT INTO drafts(id,kind,payload,state,created_by,created_at)"
            " VALUES ('x','k','{}','approved','a','t')"
        )


@pytest.mark.parametrize("col", ["reason", "decided_by", "decided_at", "state"])
def test_terminal_row_any_column_update_blocked(db, col):
    c = _raw(db, "approved")
    val = "draft" if col == "state" else "zzz"
    with pytest.raises(sqlite3.DatabaseError):
        c.execute(f"UPDATE drafts SET {col}=? WHERE id='d1'", (val,))


def test_draft_row_update_without_transition_blocked(db):
    c = _raw(db)
    with pytest.raises(sqlite3.DatabaseError):
        c.execute("UPDATE drafts SET reason='x' WHERE id='d1'")


def test_transition_cannot_change_immutable_columns(db):
    c = _raw(db)
    with pytest.raises(sqlite3.DatabaseError):
        c.execute(
            "UPDATE drafts SET state='approved', decided_by='h', decided_at='t', payload='{\"z\":1}'"
            " WHERE id='d1'"
        )


def test_transition_requires_decider(db):
    c = _raw(db)
    with pytest.raises(sqlite3.DatabaseError):
        c.execute("UPDATE drafts SET state='approved' WHERE id='d1'")


def test_valid_transition_passes_trigger(db):
    c = _raw(db)
    c.execute("UPDATE drafts SET state='approved', decided_by='h', decided_at='t' WHERE id='d1'")


# --- B1/W1: id·rowid 충돌 INSERT 로 기존 행을 덮어쓰는 경로 ------------------------------------

_COLS = "id,kind,payload,state,created_by,created_at,decided_by,decided_at,reason"


def _seed(db, state):
    c = sqlite3.connect(db)
    c.execute(
        "INSERT INTO drafts(id,kind,payload,state,created_by,created_at)"
        " VALUES ('d1','k','{\"x\":1}','draft','agent:a','t0')"
    )
    if state != "draft":
        c.execute(
            "UPDATE drafts SET state=?, decided_by='human:h', decided_at='t1' WHERE id='d1'",
            (state,),
        )
    c.commit()
    c.close()


def _snapshot(db):
    c = sqlite3.connect(db)
    try:
        return c.execute(f"SELECT {_COLS} FROM drafts ORDER BY id").fetchall()
    finally:
        c.close()


_EVIL = "('d1','k','{\"evil\":1}','draft','agent:evil','t9',NULL,NULL,NULL)"
_COLLIDING_SQL = [
    f"INSERT OR REPLACE INTO drafts({_COLS}) VALUES {_EVIL}",
    f"REPLACE INTO drafts({_COLS}) VALUES {_EVIL}",
    f"INSERT OR IGNORE INTO drafts({_COLS}) VALUES {_EVIL}",
    f"INSERT INTO drafts({_COLS}) VALUES {_EVIL}",
    (f"INSERT INTO drafts({_COLS}) VALUES {_EVIL}"
    " ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, state='draft',"
    " decided_by=NULL, decided_at=NULL"),
    f"INSERT INTO drafts({_COLS}) VALUES {_EVIL} ON CONFLICT(id) DO NOTHING",
    (f"INSERT OR REPLACE INTO drafts({_COLS}) SELECT {_COLS} FROM (SELECT 'd1' AS id,'k' AS kind,"
    "'{\"evil\":1}' AS payload,'draft' AS state,'agent:evil' AS created_by,'t9' AS created_at,"
    "NULL AS decided_by,NULL AS decided_at,NULL AS reason)"),
    ("INSERT OR REPLACE INTO drafts(id,kind,payload,state,created_by,created_at)"
    " SELECT 'd1','k','{\"evil\":1}','draft','agent:evil','t9'"),
]


def _try(conn, sql):
    try:
        conn.execute(sql)
        conn.commit()
    except sqlite3.DatabaseError:
        conn.rollback()


@pytest.mark.parametrize("who", ["agent", "bypass"])
@pytest.mark.parametrize("state", ["approved", "rejected", "draft"])
@pytest.mark.parametrize("sql", _COLLIDING_SQL)
def test_id_collision_insert_never_changes_existing_row(db, who, state, sql):
    _seed(db, state)
    before = _snapshot(db)
    conn = connect(db) if who == "agent" else sqlite3.connect(db)
    _try(conn, sql)
    conn.close()
    assert _snapshot(db) == before


@pytest.mark.parametrize("who", ["agent", "bypass"])
@pytest.mark.parametrize("state", ["approved", "draft"])
@pytest.mark.parametrize(
    "stmt",
    [
        ("INSERT OR REPLACE INTO drafts(rowid,id,kind,payload,state,created_by,created_at)"
        " VALUES (1,'other','k','{\"evil\":1}','draft','agent:evil','t9')"),
        ("INSERT INTO drafts(rowid,id,kind,payload,state,created_by,created_at)"
        " VALUES (1,'other','k','{\"evil\":1}','draft','agent:evil','t9')"),
        ("INSERT OR IGNORE INTO drafts(rowid,id,kind,payload,state,created_by,created_at)"
        " VALUES (1,'other','k','{\"evil\":1}','draft','agent:evil','t9')"),
    ],
)
def test_rowid_collision_insert_never_changes_existing_row(db, who, state, stmt):
    _seed(db, state)
    before = _snapshot(db)
    conn = connect(db) if who == "agent" else sqlite3.connect(db)
    _try(conn, stmt)
    conn.close()
    assert _snapshot(db) == before


@pytest.mark.parametrize("state", ["approved", "rejected"])
def test_terminal_row_delete_blocked_on_bypass_conn(db, state):
    _seed(db, state)
    before = _snapshot(db)
    c = sqlite3.connect(db)
    with pytest.raises(sqlite3.DatabaseError):
        c.execute("DELETE FROM drafts WHERE id='d1'")
    c.close()
    assert _snapshot(db) == before


@pytest.mark.parametrize(
    "cols,vals",
    [
        ("decided_by", "'human:h'"),
        ("decided_at", "'t1'"),
        ("reason", "'forged'"),
    ],
)
@pytest.mark.parametrize("who", ["agent", "bypass"])
def test_forged_decision_fields_on_draft_insert_blocked(db, who, cols, vals):
    c = connect(db) if who == "agent" else sqlite3.connect(db)
    with pytest.raises(sqlite3.DatabaseError):
        c.execute(
            f"INSERT INTO drafts(id,kind,payload,state,created_by,created_at,{cols})"
            f" VALUES ('n','k','{{}}','draft','a','t',{vals})"
        )


def test_agent_conn_cannot_create_view_trigger_or_pragma(db):
    c = connect(db)
    for sql in (
        "CREATE VIEW v AS SELECT * FROM drafts",
        "CREATE TEMP TRIGGER t AFTER INSERT ON drafts BEGIN SELECT 1; END",
        "CREATE TRIGGER t2 AFTER INSERT ON drafts BEGIN SELECT 1; END",
        "PRAGMA recursive_triggers=ON",
        "PRAGMA writable_schema=ON",
        "ATTACH DATABASE ':memory:' AS m",
        "CREATE TABLE z(a)",
    ):
        with pytest.raises(sqlite3.DatabaseError):
            c.execute(sql)


def test_agent_conn_dangerous_functions_unavailable(db):
    c = connect(db)
    for sql in ("SELECT load_extension('x')", "SELECT readfile('/etc/passwd')",
                "SELECT writefile('/tmp/x','y')"):
        with pytest.raises(sqlite3.DatabaseError):
            c.execute(sql)


def test_insert_trigger_names_required_by_schema_check(db):
    c = sqlite3.connect(db)
    c.execute("DROP TRIGGER drafts_no_delete_terminal")
    c.commit()
    c.close()
    with pytest.raises(SchemaMissingError):
        connect(db)
