"""공개 배포 메타·세션 발급(D24 ①). 상태를 바꾸는 사람 전용 API 가 아니라 방문자 세션만 만든다."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api")


@router.get("/meta")
def meta(request: Request) -> dict:
    closed = "closed" if request.app.state.settings.public_mode else "open"
    return {"schema": "kc-meta/v1", "public": request.app.state.settings.public_mode,
            "decisions": closed, "reports": closed}


@router.post("/session")
def create_session(request: Request) -> JSONResponse:
    store = request.app.state.sessions
    s = store.create()
    if s is None:
        return JSONResponse({"error": {"code": "busy", "message": "지금은 새 세션을 만들 수 없다"}},
                            status_code=429)
    return JSONResponse({"session": s.id, "ttl_s": int(store.ttl_s)}, status_code=201)
