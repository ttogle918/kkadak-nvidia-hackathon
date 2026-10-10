import os

if os.environ.get("APP_PROCESS_ROLE") == "agent":
    raise RuntimeError("backend 는 APP_PROCESS_ROLE=agent 로 실행할 수 없다 (D2)")

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware

from backend.catalog_runner import configure_concurrency
from backend.limits import RULES, AdminGuard, DailyBudget, RateLimiter, classify, client_ip
from backend.routers import events, messages, meta, review, screen
from backend.routers.events import Forbidden
from backend.session import SESSION_HEADER, SessionStore
from backend.settings import Settings
from core.hitl import init_db

# 라우터 추가는 이 목록에 한 줄 + 위 import 한 줄로 끝낸다.
ROUTERS = [review.router, messages.router, events.router, screen.router, meta.router]


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


MAX_BODY_BYTES = 256 * 1024


def create_app(settings: Settings | None = None) -> FastAPI:
    s = settings or Settings.from_env()
    s.hitl_db.parent.mkdir(parents=True, exist_ok=True)
    if not s.hitl_db.exists():
        init_db(s.hitl_db)
    # 공개 모드에서는 API 문서를 끈다
    kw = {"docs_url": None, "redoc_url": None, "openapi_url": None} if s.public_mode else {}
    app = FastAPI(title="backend", **kw)
    app.state.settings = s
    app.state.sessions = SessionStore(ttl_s=s.session_ttl_s, max_sessions=s.session_max)
    app.state.limiter = RateLimiter()
    app.state.budget = DailyBudget(s.llm_daily_units)
    app.state.admin_guard = AdminGuard()
    configure_concurrency(s.catalog_concurrency)

    # 미들웨어 순서: 나중에 붙인 것이 바깥이다. _limit_body -> _rate_limit -> GZip -> CORS(가장 바깥).
    @app.middleware("http")
    async def _limit_body(request: Request, call_next):
        size = request.headers.get("content-length")
        if size and size.isdigit() and int(size) > MAX_BODY_BYTES:
            return _error(413, "too_large", "요청이 너무 크다")
        return await call_next(request)

    if s.public_mode:
        @app.middleware("http")
        async def _rate_limit(request: Request, call_next):
            bucket = classify(request.url.path, request.method)
            if bucket is not None:
                sess = request.app.state.sessions.get(request.headers.get(SESSION_HEADER))
                keys = {"ip": client_ip(request, s.trusted_proxy_hops),
                        "session": sess.id if sess else None, "global": "all"}
                wait = request.app.state.limiter.hit(bucket, keys, RULES[bucket])
                if wait is not None:
                    r = _error(429, "rate_limited", "요청이 너무 많다. 잠시 뒤 다시 시도한다")
                    r.headers["Retry-After"] = str(wait)
                    return r
            return await call_next(request)

    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(  # 마지막에 추가 = 가장 바깥: 413·429·403·503 응답에도 CORS 헤더가 붙는다
        CORSMiddleware,
        allow_origins=list(s.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Admin-Token", SESSION_HEADER],
        expose_headers=["X-Audit-Skipped", "Retry-After"],
    )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, __: RequestValidationError) -> JSONResponse:
        return _error(422, "validation_error", "요청이 올바르지 않다")

    @app.exception_handler(Forbidden)
    async def _forbidden(_: Request, exc: Forbidden) -> JSONResponse:
        return _error(403, getattr(exc, "code", "forbidden"), str(exc))

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
