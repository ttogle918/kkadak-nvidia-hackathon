"""화면용 읽기 전용 API — 카드·출처·판단 근거. 쓰기 엔드포인트는 없고 신원 필드도 없다(D2).

- ``GET /api/cards`` · ``GET /api/cards/{id}`` · ``GET /api/sources`` · ``GET /api/cards/{id}/rationale``
- 데이터는 JSON 파일(``Settings.screen_fixture_dir``)에서 읽는다. ``domains``·``mcp_server`` 는 import 하지 않는다(D3·D10).
- 형식 기준은 프론트 ``src/api/schema.js``(validateCard·validateSource). 새 필드를 만들지 않는다.
- 응답에 내부 경로·파일 이름을 싣지 않는다: 읽기 실패는 고정 문구의 500 으로만 알린다.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api")

_ID = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
_MAX_FILE_BYTES = 2 * 1024 * 1024


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def _read_json(path: Path, kind: type):
    if path.stat().st_size > _MAX_FILE_BYTES:
        raise ValueError("too large")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, kind):
        raise TypeError("bad shape")
    return data


def load_screen_data(directory: Path) -> tuple[list[dict], list[dict], dict[str, dict]]:
    """(cards, sources, rationale) 를 읽는다.

    이 함수가 데이터 출처의 유일한 자리다. 지금은 프론트 mock 과 같은 내용의 fixture 이고,
    파이프라인(이야기·행사)이 같은 형식의 출력 묶음을 만들면 이 함수가 그 파일을 읽게 바꾼다.
    라우트 코드는 바꾸지 않는다.
    """
    cards = _read_json(directory / "cards.json", list)
    sources = _read_json(directory / "sources.json", list)
    rationale = _read_json(directory / "rationale.json", dict)
    return cards, sources, rationale


def _load(request: Request):
    try:
        return load_screen_data(request.app.state.settings.screen_fixture_dir), None
    except (OSError, ValueError, TypeError):  # JSONDecodeError 는 ValueError. 경로·파일명은 응답에 싣지 않는다
        return None, _err(500, "internal_error", "처리 중 오류가 발생했다")


def _bad_id() -> JSONResponse:
    return _err(422, "bad_id", "id 형식이 올바르지 않다")


def _not_found() -> JSONResponse:
    return _err(404, "not_found", "찾을 수 없다")


@router.get("/cards")
def list_cards(request: Request):
    data, err = _load(request)
    return err or data[0]


@router.get("/sources")
def list_sources(request: Request):
    data, err = _load(request)
    return err or data[1]


@router.get("/cards/{card_id}")
def get_card(card_id: str, request: Request):
    if not _ID.fullmatch(card_id):
        return _bad_id()
    data, err = _load(request)
    if err:
        return err
    card = next((c for c in data[0] if isinstance(c, dict) and c.get("id") == card_id), None)
    return card if card is not None else _not_found()


@router.get("/cards/{card_id}/rationale")
def get_rationale(card_id: str, request: Request):
    if not _ID.fullmatch(card_id):
        return _bad_id()
    data, err = _load(request)
    if err:
        return err
    r = data[2].get(card_id)
    return r if r is not None else _not_found()
