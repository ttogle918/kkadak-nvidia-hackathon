"""TourAPI 실시간 클라이언트 (D29). backend 전용 — `domains`·`mcp_server` 를 import 하지 않는다 (D3·D10).

하는 일: 요청 시점에 `searchFestival2` 를 한 번 부르고, 화면용 필드만 응답 문자열 그대로 돌려준다.
하지 않는 일: 저장(파일·DB·로그·캐시·메모리 재사용), 정규화(날짜 포맷 포함), 요약·번역, 좌표·이미지 사용.
모듈 상태는 일일 호출 카운터뿐이다. 오류 메시지·로그에는 요청 URL·키·원문을 싣지 않는다(D29 ⑥).
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.parse
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

import httpx

from backend.limits import kst_today
from backend.settings import REPO_ROOT
from core.llm.envfile import default_dotenv_path, resolve_env

BASE = "https://apis.data.go.kr/B551011/KorService2"
KEY_ENV = "DATA_GO_KR_SERVICE_KEY"
SHOW_FIELDS = (
    "contentid", "title", "addr1", "addr2", "eventstartdate", "eventenddate",
    "tel", "progresstype", "lDongSignguCd", "cpyrhtDivCd",
)  # T401 ⑩ 확정 필드 중 화면용 — 이미지·좌표는 쓰지 않는다
ATTRIBUTION = {
    "Type3": "출처: 한국관광공사 TourAPI · 공공누리 제3유형(변경금지)",
    "Type1": "출처: 한국관광공사 TourAPI · 공공누리 제1유형(출처표시)",
}
SOURCE_PAGE = "https://www.data.go.kr/data/15101578/openapi.do"
CODES_PATH = Path(__file__).resolve().parent / "fixtures" / "tourapi_codes.json"
MAX_BODY_BYTES = 1_000_000  # 응답 읽기 상한 1MB
SEOUL = "11"

log = logging.getLogger("backend.tourapi_live")
# httpx 는 INFO 로 "HTTP Request: GET <url>" 을 남기는데 URL 에 키가 들어 있다 — 이 모듈 쓰는 동안 끈다.
for _name in ("httpx", "httpcore"):
    logging.getLogger(_name).setLevel(logging.WARNING)


@dataclass(frozen=True)
class LiveResult:
    status: Literal["ok", "unavailable"]
    reason: str | None
    items: tuple[dict[str, str], ...] = ()
    total: int | None = None


def _unavailable(reason: str) -> LiveResult:
    return LiveResult("unavailable", reason, (), None)


def env_key_lookup(environ: Mapping[str, str] | None = None) -> str | None:
    """셸 env → `.env`(이 이름 하나만 허용). 값은 반환만 하고 어디에도 남기지 않는다."""
    env = resolve_env(default_dotenv_path(REPO_ROOT, environ=environ), environ=environ, allowed=(KEY_ENV,))
    return env.get(KEY_ENV, "").strip() or None


def load_signgu_codes(path: Path = CODES_PATH) -> dict[str, str]:
    """코드 -> 구 이름. 파일이 깨졌으면 빈 dict(구 필터 없이 서울 전체로 동작)."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))["signgu"]
        return {str(k): str(v) for k, v in raw.items()}
    except (OSError, ValueError, KeyError, AttributeError):
        return {}


def _encode_key(key: str) -> str:
    return key if "%" in key else urllib.parse.quote(key, safe="")  # 이중 인코딩 금지


def _ymd(s: str) -> str | None:
    try:
        if len(s) != 10 or s[4] != "-" or s[7] != "-":
            return None
        return date.fromisoformat(s).strftime("%Y%m%d")
    except (TypeError, ValueError):
        return None


class TourApiLive:
    def __init__(
        self,
        *,
        key_lookup: Callable[[], str | None] = env_key_lookup,
        client: httpx.Client | None = None,
        timeout_s: float = 5.0,
        daily_calls: int = 300,
        today: Callable[[], date] = kst_today,
        codes: Mapping[str, str] | None = None,
    ) -> None:
        self._key_lookup = key_lookup
        self._client = client or httpx.Client(follow_redirects=False)
        self._timeout = timeout_s
        self._limit = daily_calls
        self._today = today
        self._codes = dict(codes) if codes is not None else load_signgu_codes()
        self._lock = threading.Lock()
        self._day: date | None = None
        self._count = 0

    def _take(self) -> bool:
        with self._lock:
            d = self._today()
            if d != self._day:
                self._day, self._count = d, 0
            if self._count >= self._limit:
                return False
            self._count += 1
            return True

    def _peek_full(self) -> bool:
        with self._lock:
            return self._today() == self._day and self._count >= self._limit

    def festivals(self, *, date_from: str, date_to: str, signgu: str | None = None, rows: int = 20) -> LiveResult:
        t0 = time.monotonic()
        res = self._festivals(date_from, date_to, signgu, rows)
        log.info(
            "tourapi status=%s reason=%s n=%d ms=%d",
            res.status, res.reason, len(res.items), int((time.monotonic() - t0) * 1000),
        )
        return res

    def _festivals(self, date_from: str, date_to: str, signgu: str | None, rows: int) -> LiveResult:
        start, end = _ymd(date_from), _ymd(date_to)
        if start is None or end is None:
            return _unavailable("bad_shape")
        if self._peek_full():
            return _unavailable("limit")
        try:
            key = self._key_lookup()
        except Exception:  # noqa: BLE001 - 조회 실패 사유(경로·값)를 싣지 않는다
            key = None
        if not key or not key.strip():
            return _unavailable("no_key")
        if not self._take():
            return _unavailable("limit")

        params = {
            "MobileOS": "ETC", "MobileApp": "KContext", "_type": "json",
            "numOfRows": str(max(1, min(int(rows), 20))), "pageNo": "1",
            "eventStartDate": start, "eventEndDate": end, "lDongRegnCd": SEOUL, "arrange": "A",
        }
        if signgu is not None and str(signgu) in self._codes:
            params["lDongSignguCd"] = str(signgu)
        # 쿼리를 직접 조립해 httpx 가 키를 다시 인코딩하지 않게 한다.
        url = f"{BASE}/searchFestival2?serviceKey={_encode_key(key.strip())}&{urllib.parse.urlencode(params)}"

        deadline = time.monotonic() + self._timeout
        try:
            with self._client.stream("GET", url, timeout=self._timeout) as r:
                if r.status_code != 200:
                    return _unavailable("http")
                buf = bytearray()
                for chunk in r.iter_bytes():
                    buf += chunk
                    if len(buf) > MAX_BODY_BYTES:
                        return _unavailable("bad_shape")
                    if time.monotonic() > deadline:  # httpx timeout 은 단계별이라 조금씩 흘려보내는 응답은 따로 끊는다
                        return _unavailable("timeout")
        except httpx.TimeoutException:
            return _unavailable("timeout")
        except Exception:  # noqa: BLE001 - 예외 문자열에 URL 이 들어 있을 수 있어 버린다
            return _unavailable("http")
        return _parse(bytes(buf))


def _parse(body: bytes) -> LiveResult:
    try:
        data = json.loads(body)
    except ValueError:
        return _unavailable("bad_shape")
    if not isinstance(data, dict):
        return _unavailable("bad_shape")
    gw = data.get("OpenAPI_ServiceResponse")
    if gw is not None:
        hdr = gw.get("cmmMsgHeader") if isinstance(gw, dict) else None
        code = hdr.get("returnReasonCode") if isinstance(hdr, dict) else None
        return _unavailable(f"gateway:{code}" if isinstance(code, str) and code.isalnum() else "bad_shape")
    resp = data.get("response")
    if not isinstance(resp, dict):
        return _unavailable("bad_shape")
    header, rbody = resp.get("header"), resp.get("body")
    if not isinstance(header, dict):
        return _unavailable("bad_shape")
    rc = header.get("resultCode")
    if rc != "0000":
        return _unavailable(f"result:{rc}" if isinstance(rc, str) and rc.isalnum() else "bad_shape")
    if not isinstance(rbody, dict):
        return _unavailable("bad_shape")
    tc = rbody.get("totalCount")
    total = int(tc) if isinstance(tc, str) and tc.isdigit() else (tc if isinstance(tc, int) and not isinstance(tc, bool) and tc >= 0 else None)

    items = rbody.get("items")
    if items in ("", None) or items == {}:
        return LiveResult("ok", None, (), total)
    raw = items.get("item") if isinstance(items, dict) else None
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return _unavailable("bad_shape")
    out: list[dict[str, str]] = []
    for it in raw:
        if not isinstance(it, dict) or it.get("lDongRegnCd") != SEOUL:
            continue  # 서울 밖(또는 구분 불가) 항목은 버린다 — 값은 바꾸지 않는다
        out.append({f: it[f] for f in SHOW_FIELDS if isinstance(it.get(f), str)})
    return LiveResult("ok", None, tuple(out), total)
