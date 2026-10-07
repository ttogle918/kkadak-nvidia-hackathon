"""행사 카탈로그 API. 계산은 전부 별도 프로세스(``catalog_runner``)가 하고, 이 라우터는 입력 검증·권한·상태 코드만 맡는다.

- 공개 API: 검색·상세·일정 추가/취소·저장한 행사의 변경·제보·수집 범위.
- 관리자 API(``/api/admin/*``): 헤더 ``X-Admin-Token`` 이 설정값과 같을 때만 열린다(설정이 비어 있으면 닫힘).
  승인·반려 같은 사람 전용 결정의 신원은 서버가 주입한다 — 요청 본문에서 받지 않는다(D2).
- 제보는 즉시 공개되지 않는다(검토 대기).
"""

from __future__ import annotations

import hmac
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.catalog_runner import CatalogRunnerError, run_catalog

router = APIRouter(prefix="/api")

_STATUS = {"bad_request": 400, "forbidden": 403, "not_found": 404, "conflict": 409, "not_implemented": 501}


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def _call(request: Request, op: str, args: dict, actor: str | None = None):
    s = request.app.state.settings
    try:
        out = run_catalog(s.catalog_dir, op, args, actor)
    except CatalogRunnerError:
        return _err(500, "internal_error", "처리 중 오류가 발생했다")
    if "error" in out:
        e = out["error"]
        return _err(_STATUS.get(e.get("code"), 500), e.get("code", "internal_error"), e.get("message", ""))
    return out


# ---- 입력 모델(알 수 없는 키는 422) ----------------------------------------------------------
class Trip(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    from_: str = Field(alias="from", pattern=r"^\d{4}-\d{2}-\d{2}$")
    to: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")


class Point(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(default="", max_length=80)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)


class Plan(BaseModel):
    model_config = ConfigDict(extra="ignore")  # 모르는 키는 버린다(크기 상한 우회 방지)
    id: str = Field(min_length=1, max_length=80)
    title: str = Field(default="", max_length=120)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    start: str = Field(pattern=r"^\d{2}:\d{2}$")
    end: str = Field(pattern=r"^\d{2}:\d{2}$")
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    source: Literal["user", "catalog", "demo"] | None = None  # 화면이 붙인 표시용 키
    entry_id: str | None = Field(default=None, max_length=40)
    end_assumed: bool | None = None


class Slot(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    from_: str = Field(alias="from", pattern=r"^\d{2}:\d{2}$")
    to: str = Field(pattern=r"^\d{2}:\d{2}$")


class SearchBody(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    trip: Trip
    origin: Point | None = None
    interests: list[Annotated[str, Field(max_length=40)]] = Field(default_factory=list, max_length=20)
    itinerary: list[Plan] | None = Field(default=None, max_length=60)
    free_slots: list[Slot] = Field(default_factory=list, max_length=60)
    max_extra_minutes: int = Field(default=30, ge=0, le=240)
    assumed_duration_min: int | None = Field(default=None, ge=1, le=720)
    require_interest: bool = False
    include_demo: bool = False


class AddBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entry_id: str = Field(min_length=1, max_length=40)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    itinerary: list[Plan] = Field(max_length=60)
    origin: Point | None = None
    max_extra_minutes: int = Field(default=30, ge=0, le=240)
    assumed_duration_min: int | None = Field(default=None, ge=1, le=720)
    force: bool = False
    demo: bool = False


class RemoveBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_id: str = Field(min_length=1, max_length=80)
    itinerary: list[Plan] = Field(max_length=60)


class SavedBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ids: list[Annotated[str, Field(max_length=40)]] = Field(max_length=100)
    since: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$")


class ReportBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["new_event", "correction", "cancel_notice", "other"] = "other"
    official_link: str = Field(max_length=500)
    reason: str = Field(max_length=1000)
    entry_id: str | None = Field(default=None, max_length=40)
    fields: dict[Literal["title", "start_date", "end_date", "start_time", "venue_name", "venue_address", "note"],
                 Annotated[str, Field(max_length=200)]] = Field(default_factory=dict, max_length=7)


def _dump(m: BaseModel) -> dict:
    return m.model_dump(by_alias=True, exclude_none=False)


# ---- 공개 -----------------------------------------------------------------------------------
@router.post("/events/search")
def search(body: SearchBody, request: Request):
    return _call(request, "search", _dump(body))


@router.post("/events/cards")
def cards(body: SearchBody, request: Request):
    """검색 결과를 화면용 `now` 카드와 판단 근거로(형식은 AGENT_CONTEXT 3.3). 일정은 요청에 실어 보낸다(서버 보관 없음)."""
    return _call(request, "cards", _dump(body))


@router.get("/events/coverage")
def coverage(request: Request):
    return _call(request, "public_sources", {})


@router.get("/events/{entry_id}")
def detail(entry_id: str, request: Request, lang: Literal["ko", "en"] = "ko", demo: bool = False):
    if len(entry_id) > 40:
        return _err(404, "not_found", "행사를 찾을 수 없다")
    return _call(request, "detail", {"entry_id": entry_id, "lang": lang, "demo": demo})


@router.post("/events/itinerary/add")
def itinerary_add(body: AddBody, request: Request):
    return _call(request, "itinerary_add", _dump(body))


@router.post("/events/itinerary/remove")
def itinerary_remove(body: RemoveBody, request: Request):
    return _call(request, "itinerary_remove", _dump(body))


@router.post("/events/saved-changes")
def saved_changes(body: SavedBody, request: Request):
    return _call(request, "saved_changes", _dump(body))


@router.post("/reports", status_code=202)
def submit_report(body: ReportBody, request: Request):
    """제보는 검토 대기로 저장된다(202). 즉시 공개 데이터가 되지 않는다."""
    return _call(request, "report_submit", _dump(body))


# ---- 관리자 ---------------------------------------------------------------------------------
class Forbidden(Exception):
    pass


def require_admin(request: Request, x_admin_token: Annotated[str | None, Header()] = None) -> str:
    s = request.app.state.settings
    if not s.admin_token:
        raise Forbidden("관리자 토큰이 설정되지 않아 관리자 API 가 닫혀 있다")
    if not x_admin_token or not hmac.compare_digest(x_admin_token.encode(), s.admin_token.encode()):
        raise Forbidden("관리자 토큰이 올바르지 않다")
    return s.reviewer_id  # 신원은 서버가 정한다


Admin = Annotated[str, Depends(require_admin)]


class DecideBody(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 신원 필드(reviewer·decided_by 등)는 422
    decision: Literal["approve", "reject"]
    note: str = Field(default="", max_length=300)


class RefreshBody(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 본문은 비어 있다. sample 키 수집은 CLI 전용이다


class LinkCheckBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note: str = Field(default="", max_length=300)


@router.get("/admin/review")
def admin_review(request: Request, actor: Admin):
    return _call(request, "admin_review_queue", {}, actor)


@router.get("/admin/sources")
def admin_sources(request: Request, actor: Admin):
    return _call(request, "admin_sources", {}, actor)


@router.get("/admin/reports")
def admin_reports(request: Request, actor: Admin, status: Literal["pending", "accepted", "rejected"] | None = None):
    return _call(request, "admin_reports", {"status": status}, actor)


@router.post("/admin/reports/{report_id}/decision")
def admin_decide(report_id: str, body: DecideBody, request: Request, actor: Admin):
    return _call(request, "admin_report_decide",
                 {"report_id": report_id, "decision": body.decision, "note": body.note}, actor)


@router.post("/admin/refresh/{source_id}")
def admin_refresh(source_id: str, body: RefreshBody, request: Request, actor: Admin):
    return _call(request, "admin_refresh", {"source_id": source_id}, actor)


@router.post("/admin/link-checks/{source_id}")
def admin_link_check(source_id: str, body: LinkCheckBody, request: Request, actor: Admin):
    return _call(request, "admin_link_check", {"source_id": source_id, "note": body.note}, actor)
