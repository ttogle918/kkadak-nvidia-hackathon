"""SQLite 연결과 스키마.

한계: authorizer·역할 분리는 **정직한 코드 경로를 강제하는 장치**다. authorizer 는 연결 단위로
걸리며 프로세스 경계가 아니다. 같은 프로세스에서 `sqlite3.connect` 로 파일을 직접 열면 우회된다
(2026-10-04 실측). 실제 격리는 mcp_server 를 별도 프로세스로 띄우고 DB 파일 권한을 분리해야
얻는다. 트리거는 id 충돌 INSERT(REPLACE·upsert 포함)·종결 행 UPDATE/DELETE 를 막지만, 우회
연결이 DB 파일을 직접 조작하는 것(트리거 DROP, PRAGMA writable_schema, 파일 교체·삭제 등)까지
막는 보안 경계는 아니다. 같은 이유로 agent 연결의 허용 목록(INSERT·SELECT·함수)도 SQLite 가
노출하는 함수 전부를 검증한 것은 아니다 — 위험 함수(load_extension 등)는 기본 빌드에서 꺼져 있다는
전제에 기댄다.

공개 `connect` 는 항상 agent 역할이다. reviewer 연결은 `review.py` 의 비공개 함수로만 만든다.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from core.hitl.models import DbNotFoundError, SchemaMissingError

_SCHEMA = """
-- WITHOUT ROWID: rowid 충돌(INSERT OR REPLACE INTO drafts(rowid, ...))로 행을 덮어쓰는 경로를
-- 없앤다 (rowid 컬럼 자체가 없어 구문 오류).
CREATE TABLE IF NOT EXISTS drafts (
  id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('draft','approved','rejected')),
  created_by TEXT NOT NULL, created_at TEXT NOT NULL,
  decided_by TEXT, decided_at TEXT, reason TEXT) WITHOUT ROWID;
-- INSERT OR REPLACE 의 암묵적 삭제는 BEFORE DELETE/UPDATE 트리거도 SQLITE_DELETE authorizer 도
-- 거치지 않는다(recursive_triggers 기본 OFF, 2026-10-04 실측). 그래서 BEFORE INSERT 에서 id 충돌
-- 자체를 거부한다(EXISTS). 위조된 판정 필드를 가진 draft 도 여기서 거부한다.
CREATE TRIGGER IF NOT EXISTS drafts_insert_only_draft BEFORE INSERT ON drafts
  WHEN NEW.state <> 'draft'
    OR NEW.decided_by IS NOT NULL OR NEW.decided_at IS NOT NULL OR NEW.reason IS NOT NULL
    OR EXISTS (SELECT 1 FROM drafts WHERE id = NEW.id)
  BEGIN SELECT RAISE(ABORT, 'insert must be a fresh plain draft'); END;
CREATE TRIGGER IF NOT EXISTS drafts_update_guard BEFORE UPDATE ON drafts
  WHEN OLD.state <> 'draft'
    OR NEW.state NOT IN ('approved','rejected')
    OR NEW.decided_by IS NULL OR NEW.decided_at IS NULL
    OR NEW.id IS NOT OLD.id OR NEW.kind IS NOT OLD.kind OR NEW.payload IS NOT OLD.payload
    OR NEW.created_by IS NOT OLD.created_by OR NEW.created_at IS NOT OLD.created_at
  BEGIN SELECT RAISE(ABORT, 'illegal update'); END;
CREATE TRIGGER IF NOT EXISTS drafts_no_delete_terminal BEFORE DELETE ON drafts
  WHEN OLD.state <> 'draft'
  BEGIN SELECT RAISE(ABORT, 'terminal rows cannot be deleted'); END;
"""

_REQUIRED_TRIGGERS = (
    "drafts_insert_only_draft",
    "drafts_update_guard",
    "drafts_no_delete_terminal",
)

_COMMON_ALLOWED = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_TRANSACTION,
    sqlite3.SQLITE_FUNCTION,
    sqlite3.SQLITE_SAVEPOINT,
}


def _check_path(path: str | Path) -> Path:
    if str(path) == ":memory:":
        raise ValueError(":memory:" " 는 연결끼리 공유되지 않아 지원하지 않는다")
    return Path(path)


def init_db(path: str | Path) -> None:
    """관리용. authorizer 없이 스키마만 만든다. 파일을 새로 만들 수 있는 유일한 함수."""
    p = _check_path(path)
    if not p.resolve().parent.is_dir():
        raise FileNotFoundError(f"부모 디렉터리가 없다: {p.parent}")
    conn = sqlite3.connect(p)
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _open_existing(path: str | Path) -> sqlite3.Connection:
    p = _check_path(path)
    if not p.is_file():
        raise DbNotFoundError(f"DB 파일이 없다: {p}")
    conn = sqlite3.connect(p.resolve().as_uri() + "?mode=rw", uri=True)
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='drafts'"
        ).fetchone()
        if row is None:
            raise SchemaMissingError(f"drafts 테이블이 없다 (init_db 필요): {p}")
        have = {
            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        }
        missing = [t for t in _REQUIRED_TRIGGERS if t not in have]
        if missing:
            raise SchemaMissingError(f"drafts 트리거가 없다 {missing} (스키마 갱신 필요): {p}")
    except BaseException:
        conn.close()
        raise
    return conn


def _agent_authorizer(action, arg1, arg2, db_name, trigger) -> int:
    if action in _COMMON_ALLOWED:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_INSERT and arg1 == "drafts":
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def connect(path: str | Path) -> sqlite3.Connection:
    """agent 역할 연결. INSERT(drafts) 와 읽기만 허용한다. role 파라미터는 없다."""
    conn = _open_existing(path)
    conn.set_authorizer(_agent_authorizer)
    return conn
