"""채팅 라우터(최소판). 순수 대화 + 입력 가드. 본문은 {text} 만 받고 신원 필드는 받지 않는다(D2)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.chat import MAX_TEXT_CHARS, ChatBusy, ChatService, ChatUnavailable
from backend.chat_story import BadContext, validate_context

router = APIRouter(prefix="/api")
_log = logging.getLogger(__name__)


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def _service(request: Request) -> ChatService:
    svc = getattr(request.app.state, "chat", None)
    if svc is None:
        svc = request.app.state.chat = ChatService(request.app.state.settings)
    return svc


@router.get("/messages")
def get_messages(request: Request) -> list[dict]:
    return _service(request).messages()


@router.post("/messages")
async def post_message(request: Request):
    # Content-Type 이 application/json 이 아니면 거절한다. text/plain 등은 CORS preflight 없이 보낼 수 있는
    # 'simple request' 라 다른 사이트의 폼이 로컬 backend 로 대화를 보낼 수 있기 때문이다(W6).
    # 상태 코드는 415 대신 422 bad_text 를 쓴다 — sprint-2 §5.1 계약에 본문 오류 코드가 bad_text 하나뿐이고
    # 프론트 ERROR_MESSAGES 도 이를 안다. 415 는 새 오류 코드가 되어 계약 변경이 필요하다.
    ctype = request.headers.get("content-type", "").split(";")[0].strip().lower()
    body = None
    if ctype == "application/json":
        try:
            body = await request.json()
        except ValueError:
            body = None
    # 허용 키는 text(필수)와 context(선택, chat-context/v1). 그 밖의 키는 그대로 422 다.
    ok_keys = isinstance(body, dict) and "text" in body and set(body) <= {"text", "context"}
    text = body.get("text") if ok_keys else None
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT_CHARS:
        return _err(422, "bad_text", f"text 는 1~{MAX_TEXT_CHARS}자 문자열이어야 한다")
    context = None
    if "context" in body:
        try:
            context = validate_context(body["context"])
        except BadContext:
            return _err(422, "bad_text", "context 가 올바르지 않다")
    try:
        result = await _service(request).send(text, context)
    except ChatBusy:
        return _err(429, "busy", "다른 요청을 처리하는 중이다")
    except ChatUnavailable:
        return _err(503, "llm_unavailable", "LLM 을 지금 쓸 수 없다")
    except Exception as exc:  # noqa: BLE001 - LlmCallError·transport 오류 모두 같은 응답
        _log.warning("chat 실패: %s", type(exc).__name__)  # 본문·키는 남기지 않는다
        return _err(502, "pipeline_failed", "답을 만들지 못했다")
    out = {"reply": result.reply, "logs": result.logs}
    if result.bundle is not None:
        out["bundle"] = result.bundle
    return out
