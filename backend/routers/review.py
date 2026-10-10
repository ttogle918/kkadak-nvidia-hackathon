"""사람 승인·보안 로그 라우터.

승인자 신원은 설정값이며 요청에서 받지 않는다(D2). 승인은 인증이 없는 로컬 모드에서만 열고,
공개 모드(KC_PUBLIC_MODE=1)에서는 403 disabled_in_public 이며 보안 로그는 자기 세션 것만 보인다(D24).
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.security_log import SECURITY_DRAFT_KINDS, build_entries_counted, entry_from_draft
from backend.session import session_from_request
from core.audit import AuditEvent, AuditFormatError
from core.hitl import (
    DraftNotFound,
    DraftValidationError,
    DraftWriter,
    HitlError,
    SelfApprovalError,
    TransitionError,
)
from core.hitl.review import ReviewDesk, Reviewer

router = APIRouter(prefix="/api")

_DEFAULT_REJECT_REASON = "화면에서 거절"


class DecisionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 신원 필드(reviewer·decided_by 등)는 422
    decision: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=1000)


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


@router.get("/audit")
def get_audit(request: Request, response: Response):
    s = request.app.state.settings
    if s.public_mode:  # 자기 세션의 기록만. 저장소·파일 경로를 읽지 않는다(D24 ③)
        sess = session_from_request(request)
        if sess is None:
            return []  # 계약(sprint-4 §5.1): 세션 없음·만료 -> 200 []
        for _ in range(3):  # deque 는 순회 중 변경되면 RuntimeError — 짧게 재시도
            try:
                return list(sess.logs)
            except RuntimeError:
                continue
        return []
    writer = DraftWriter(s.hitl_db, actor="backend:reader")
    drafts = []
    for kind in SECURITY_DRAFT_KINDS:
        drafts.extend(writer.list_drafts(kind=kind, limit=1000))
    events_by_run: dict = {}
    skipped = 0
    if s.audit_dir.is_dir():
        for p in sorted(s.audit_dir.glob("*.jsonl")):
            events, bad = _read_events(p)
            skipped += bad
            events_by_run[p.stem] = events
    entries, bad = build_entries_counted(drafts, events_by_run)
    skipped += bad
    if skipped:
        response.headers["X-Audit-Skipped"] = str(skipped)
    return entries


def _read_events(path) -> tuple[list[AuditEvent], int]:
    """비신뢰 JSONL 을 줄 단위로 읽는다. 깨진 줄은 건너뛰고, 읽기 실패한 파일은 1로 센다."""
    events: list[AuditEvent] = []
    skipped = 0
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    events.append(AuditEvent.from_json(line))
                except (AuditFormatError, ValueError, TypeError, KeyError, AttributeError):
                    skipped += 1
    except (OSError, ValueError):  # UnicodeDecodeError 포함
        skipped += 1
    return events, skipped


@router.post("/audit/{entry_id}/decision")
def decide(entry_id: str, body: DecisionBody, request: Request):
    s = request.app.state.settings
    if s.public_mode:
        return _err(403, "disabled_in_public", "공개 모드에서는 승인이 닫혀 있다")
    if not entry_id.startswith("draft:") or len(entry_id) == len("draft:"):
        return _err(409, "not_decidable", "결정할 수 없는 항목이다")
    draft_id = entry_id[len("draft:") :]
    reviewer = Reviewer(id=s.reviewer_id, auth_source=s.reviewer_auth_source)  # 서버가 주입
    try:
        desk = ReviewDesk(s.hitl_db)
        if body.decision == "approve":
            d = desk.approve(draft_id, reviewer=reviewer, reason=body.reason)
        else:
            d = desk.reject(
                draft_id, reviewer=reviewer, reason=body.reason or _DEFAULT_REJECT_REASON
            )
    except DraftNotFound:
        return _err(404, "not_found", "항목을 찾을 수 없다")
    except TransitionError:
        return _err(409, "already_decided", "이미 결정된 항목이다")
    except SelfApprovalError:
        return _err(403, "self_approval", "만든 주체는 자신의 요청을 결정할 수 없다")
    except DraftValidationError:
        return _err(422, "validation_error", "요청이 올바르지 않다")
    except HitlError:
        return _err(500, "internal_error", "처리 중 오류가 발생했다")
    return entry_from_draft(d)
