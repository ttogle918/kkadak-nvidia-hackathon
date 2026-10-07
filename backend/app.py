import os

if os.environ.get("APP_PROCESS_ROLE") == "agent":
    raise RuntimeError("backend 는 APP_PROCESS_ROLE=agent 로 실행할 수 없다 (D2)")

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.routers import events, messages, review, screen
from backend.routers.events import Forbidden
from backend.settings import Settings
from core.hitl import init_db

# 라우터 추가는 이 목록에 한 줄 + 위 import 한 줄로 끝낸다.
ROUTERS = [review.router, messages.router, events.router, screen.router]


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


MAX_BODY_BYTES = 256 * 1024


def create_app(settings: Settings | None = None) -> FastAPI:
    s = settings or Settings.from_env()
    s.hitl_db.parent.mkdir(parents=True, exist_ok=True)
    if not s.hitl_db.exists():
        init_db(s.hitl_db)
    app = FastAPI(title="backend")
    app.state.settings = s
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(s.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Admin-Token"],
        expose_headers=["X-Audit-Skipped"],
    )

    @app.middleware("http")
    async def _limit_body(request: Request, call_next):
        size = request.headers.get("content-length")
        if size and size.isdigit() and int(size) > MAX_BODY_BYTES:
            return _error(413, "too_large", "요청이 너무 크다")
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, __: RequestValidationError) -> JSONResponse:
        return _error(422, "validation_error", "요청이 올바르지 않다")

    @app.exception_handler(Forbidden)
    async def _forbidden(_: Request, exc: Forbidden) -> JSONResponse:
        return _error(403, "forbidden", str(exc))

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error(exc.status_code, "http_error", "요청을 처리할 수 없다")

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, __: Exception) -> JSONResponse:
        return _error(500, "internal_error", "처리 중 오류가 발생했다")

    for r in ROUTERS:
        app.include_router(r)
    return app


app = create_app()
