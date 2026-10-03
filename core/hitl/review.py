"""사람 전용 상태 전이 (D2). `core.hitl` 패키지는 이 모듈을 내보내지도 import 하지도 않는다.

한계: authorizer·역할 분리는 **정직한 코드 경로를 강제하는 장치**다. authorizer 는 연결 단위로
걸리며 프로세스 경계가 아니다. 같은 프로세스에서 `sqlite3.connect` 로 파일을 직접 열면 우회된다
(2026-10-04 실측). 실제 격리는 mcp_server 를 별도 프로세스로 띄우고 DB 파일 권한을 분리해야
얻는다. 트리거는 id 충돌 INSERT·종결 행 UPDATE/DELETE 를 막지만, 우회 연결이 DB 파일을 직접
조작하는 것(트리거 DROP, 파일 교체 등)까지 막는 보안 경계는 아니다.
`APP_PROCESS_ROLE` import 가드는 **보안 보증이 아니라 실수 방지 메커니즘**이다. 환경변수만
바꾸면 우회된다.
"""

from __future__ import annotations

import os

if os.environ.get("APP_PROCESS_ROLE") == "agent":
    raise ImportError("core.hitl.review 는 사람 전용 프로세스에서만 import 할 수 있다 (D2)")

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.hitl.db import _COMMON_ALLOWED, _open_existing
from core.hitl.drafts import _row_to_draft
from core.hitl.models import (
    Draft,
    DraftNotFound,
    DraftState,
    DraftValidationError,
    SelfApprovalError,
    TransitionError,
    _iso,
    _utcnow,
)

_UPDATABLE = {"state", "decided_by", "decided_at", "reason"}


@dataclass(frozen=True)
class Reviewer:
    id: str  # 서버(인증 계층)가 만든다. 요청 본문에서 받지 않는다
    auth_source: str  # 예: "backend-session"

    def __post_init__(self) -> None:
        for name in ("id", "auth_source"):
            v = getattr(self, name)
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"Reviewer.{name} 은 비어 있지 않은 str 이어야 한다")


def _reviewer_authorizer(action, arg1, arg2, db_name, trigger) -> int:
    if action in _COMMON_ALLOWED:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_UPDATE and arg1 == "drafts" and arg2 in _UPDATABLE:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _connect_reviewer(path: str | Path) -> sqlite3.Connection:
    conn = _open_existing(path)
    conn.set_authorizer(_reviewer_authorizer)
    return conn


class ReviewDesk:
    def __init__(
        self, db_path: str | Path, *, clock: Callable[[], datetime] = _utcnow
    ) -> None:
        self._db_path = db_path
        self._clock = clock
        _connect_reviewer(db_path).close()  # 존재·스키마 확인

    def approve(self, draft_id: str, *, reviewer: Reviewer, reason: str | None = None) -> Draft:
        return self._decide(draft_id, DraftState.APPROVED, reviewer, reason)

    def reject(self, draft_id: str, *, reviewer: Reviewer, reason: str) -> Draft:
        if not isinstance(reason, str) or not reason.strip():
            if not isinstance(reviewer, Reviewer):
                raise TypeError("reviewer 는 Reviewer 인스턴스여야 한다")
            raise DraftValidationError("반려 사유(reason)는 필수다")
        return self._decide(draft_id, DraftState.REJECTED, reviewer, reason)

    def _decide(
        self, draft_id: str, target: DraftState, reviewer: Reviewer, reason: str | None
    ) -> Draft:
        if not isinstance(reviewer, Reviewer):
            raise TypeError("reviewer 는 Reviewer 인스턴스여야 한다")
        conn = _connect_reviewer(self._db_path)
        try:
            row = conn.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
            if row is None:
                raise DraftNotFound(draft_id)
            if reviewer.id == row["created_by"]:
                raise SelfApprovalError("만든 사람은 자신의 draft 를 판정할 수 없다")
            with conn:
                cur = conn.execute(
                    "UPDATE drafts SET state=?, decided_by=?, decided_at=?, reason=? "
                    "WHERE id=? AND state='draft'",
                    (target.value, reviewer.id, _iso(self._clock()), reason, draft_id),
                )
            if cur.rowcount == 0:
                row = conn.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
                if row is None:
                    raise DraftNotFound(draft_id)
                raise TransitionError(draft_id, DraftState(row["state"]), target)
            row = conn.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
            return _row_to_draft(row)
        finally:
            conn.close()
