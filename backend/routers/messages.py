"""채팅 라우터(최소판). 순수 대화 + 입력 가드. 본문은 {text} 만 받고 신원 필드는 받지 않는다(D2)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.chat import MAX_TEXT_CHARS, ChatBusy, ChatService, ChatUnavailable

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
    try:
        body = await request.json()
    except ValueError:
        body = None
    text = body.get("text") if isinstance(body, dict) and set(body) == {"text"} else None
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT_CHARS:
        return _err(422, "bad_text", f"text 는 1~{MAX_TEXT_CHARS}자 문자열이어야 한다")
    try:
        result = await _service(request).send(text)
    except ChatBusy:
        return _err(429, "busy", "다른 요청을 처리하는 중이다")
    except ChatUnavailable:
        return _err(503, "llm_unavailable", "LLM 을 지금 쓸 수 없다")
    except Exception as exc:  # noqa: BLE001 - LlmCallError·transport 오류 모두 같은 응답
        _log.warning("chat 실패: %s", type(exc).__name__)  # 본문·키는 남기지 않는다
        return _err(502, "pipeline_failed", "답을 만들지 못했다")
    return {"reply": result.reply, "logs": result.logs}
