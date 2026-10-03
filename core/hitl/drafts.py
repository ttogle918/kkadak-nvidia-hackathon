"""에이전트 도구 경로의 draft 저장소. 쓰기는 draft 생성뿐이다 (D2)."""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from core.hitl.db import connect
from core.hitl.models import (
    Draft,
    DraftNotFound,
    DraftState,
    DraftValidationError,
    _iso,
    _utcnow,
)

_KIND_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_MAX_PAYLOAD_BYTES = 256 * 1024


def _row_to_draft(row: Any) -> Draft:
    return Draft(
        id=row["id"],
        kind=row["kind"],
        payload=json.loads(row["payload"]),
        state=DraftState(row["state"]),
        created_by=row["created_by"],
        created_at=row["created_at"],
        decided_by=row["decided_by"],
        decided_at=row["decided_at"],
        reason=row["reason"],
    )


class DraftWriter:
    def __init__(
        self,
        db_path: str | Path,
        *,
        actor: str,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError("actor 는 비어 있지 않은 str 이어야 한다 (서버가 주입)")
        self._db_path = db_path
        self._actor = actor
        self._clock = clock
        connect(db_path).close()  # 존재·스키마 확인

    def create(self, kind: str, payload: Mapping[str, Any]) -> Draft:
        if not isinstance(kind, str) or not _KIND_RE.match(kind):
            raise DraftValidationError(f"kind 형식 오류: {kind!r}")
        try:
            text = json.dumps(dict(payload), ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError) as e:
            raise DraftValidationError(f"payload 직렬화 실패: {e}") from e
        if len(text.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
            raise DraftValidationError("payload 가 256 KiB 를 넘는다")
        draft_id = uuid.uuid4().hex
        created_at = _iso(self._clock())
        conn = connect(self._db_path)
        try:
            with conn:
                conn.execute(
                    "INSERT INTO drafts(id,kind,payload,state,created_by,created_at) "
                    "VALUES (?,?,?,'draft',?,?)",
                    (draft_id, kind, text, self._actor, created_at),
                )
        finally:
            conn.close()
        return self.get(draft_id)

    def get(self, draft_id: str) -> Draft:
        conn = connect(self._db_path)
        try:
            row = conn.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
        finally:
            conn.close()
        if row is None:
            raise DraftNotFound(draft_id)
        return _row_to_draft(row)

    def list_drafts(
        self,
        *,
        state: DraftState | None = None,
        kind: str | None = None,
        limit: int = 100,
    ) -> list[Draft]:
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 1000:
            raise ValueError("limit 은 1..1000 이어야 한다")
        where: list[str] = []
        params: list[Any] = []
        if state is not None:
            where.append("state=?")
            params.append(DraftState(state).value)
        if kind is not None:
            where.append("kind=?")
            params.append(kind)
        sql = "SELECT * FROM drafts"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at, id LIMIT ?"
        params.append(limit)
        conn = connect(self._db_path)
        try:
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
        return [_row_to_draft(r) for r in rows]
