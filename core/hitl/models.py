"""draft 데이터 모델과 예외."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class DraftState(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Draft:
    id: str
    kind: str
    payload: dict[str, Any]
    state: DraftState
    created_by: str
    created_at: str
    decided_by: str | None
    decided_at: str | None
    reason: str | None


class HitlError(Exception):
    """hitl 모듈 공통 예외."""


class DraftNotFound(HitlError):
    """해당 id 의 draft 가 없다."""


class TransitionError(HitlError):
    """허용되지 않는 상태 전이."""

    def __init__(self, draft_id: str, current: DraftState, target: DraftState) -> None:
        super().__init__(f"draft {draft_id}: {current.value} -> {target.value} 전이는 불가")
        self.draft_id = draft_id
        self.current = current
        self.target = target


class SelfApprovalError(HitlError):
    """만든 사람과 판정하는 사람이 같다."""


class DraftValidationError(HitlError, ValueError):
    """draft 입력 검증 실패."""


class SchemaMissingError(HitlError):
    """파일은 있는데 init_db 를 거치지 않은 DB."""


class DbNotFoundError(SchemaMissingError):
    """DB 파일 자체가 없다. 파일을 만들지 않는다."""


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _iso(ts: datetime) -> str:
    return ts.astimezone(UTC).isoformat(timespec="milliseconds")
