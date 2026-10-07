"""서울시 문화행사 정보(서울 열린데이터광장 OA-15486, 서울문화포털 원천) → 관찰값.

확인한 사실(2026-10-07, 공식 가이드·데이터셋 페이지·`sample` 키 응답)
- 호출: ``http://openapi.seoul.go.kr:8088/{인증키}/{json|xml}/culturalEventInfo/{시작}/{끝}/`` (한 번에 최대 1000행,
  ``sample`` 키는 5행까지). 응답 ``culturalEventInfo.{list_total_count, RESULT{CODE,MESSAGE}, row[]}``.
- 갱신주기 "매일1회", 이용허락 공공누리 1유형(출처표시). 일일 호출 한도는 데이터셋 페이지에 적혀 있지 않다(미확인).
- 행 필드: CODENAME GUNAME TITLE DATE PLACE ORG_NAME USE_TRGT USE_FEE INQUIRY PLAYER PROGRAM ETC_DESC ORG_LINK
  MAIN_IMG RGSTDATE TICKET STRTDATE END_DATE THEMECODE LOT LAT IS_FREE HMPG_ADDR PRO_TIME. ``LOT`` 가 경도, ``LAT`` 가 위도.

필드의 의미는 값으로 확인한 만큼만 쓴다(예: ``PRO_TIME`` 이 ``HH:MM`` 이면 시작 시각, 아니면 운영 시간 원문).
키는 호출 주소에 들어가므로 오류 메시지에 주소를 싣지 않는다.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Mapping, Sequence
from urllib.parse import parse_qs, urlsplit

import httpx

from domains.kcontext.contract.text import is_date, is_hhmm
from domains.kcontext.regions import Region

from .model import Evidence, Observation, Price, Reservation, Schedule, Session
from .rules import classify_venue, norm_text, parse_eligibility

__all__ = ["SeoulApiError", "fetch_rows", "observation_from_row", "observations_from_rows"]

KEY_ENV = "SEOUL_OPENAPI_KEY"
BASE = "http://openapi.seoul.go.kr:8088"
SERVICE = "culturalEventInfo"
PAGE = 1000
SOURCE_ID = "seoul_openapi"
SOURCE_NAME = "서울 열린데이터광장 · 서울시 문화행사 정보(서울문화포털)"


class SeoulApiError(RuntimeError):
    pass


def fetch_rows(
    key: str, *, client: httpx.Client | None = None, page_size: int = PAGE, max_pages: int = 30,
    start: int = 1,
) -> tuple[list[dict], int]:
    """전체 행을 쪽 단위로 가져온다. (행, list_total_count). 오류 메시지에 키·주소를 싣지 않는다."""
    if not key:
        raise SeoulApiError(f"{KEY_ENV} 가 설정되지 않았다")
    own = client is None
    http = client or httpx.Client(timeout=20.0)
    rows: list[dict] = []
    total = 0
    try:
        for n in range(max_pages):
            a = start + n * page_size
            b = a + page_size - 1
            try:
                resp = http.get(f"{BASE}/{key}/json/{SERVICE}/{a}/{b}/")
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as e:
                raise SeoulApiError(f"서울 열린데이터광장 HTTP {e.response.status_code}") from None
            except (httpx.HTTPError, ValueError) as e:
                raise SeoulApiError(f"서울 열린데이터광장 호출 실패 ({type(e).__name__})") from None
            body = data.get(SERVICE) if isinstance(data, dict) else None
            if body is None:
                code = (data.get("RESULT") or {}).get("CODE", "?") if isinstance(data, dict) else "?"
                if code == "INFO-200":  # 해당하는 데이터가 없음 = 끝
                    break
                raise SeoulApiError(f"서울 열린데이터광장 오류 코드 {code}")
            code = (body.get("RESULT") or {}).get("CODE")
            if code == "INFO-200":
                break
            if code != "INFO-000":
                raise SeoulApiError(f"서울 열린데이터광장 오류 코드 {code}")
            total = int(body.get("list_total_count") or 0)
            chunk = body.get("row") or []
            if not isinstance(chunk, list):
                raise SeoulApiError("응답 row 형식 오류")
            rows.extend(r for r in chunk if isinstance(r, dict))
            if b >= total or not chunk:
                break
    finally:
        if own:
            http.close()
    return rows, total


_DATE_RANGE = re.compile(r"(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})")


def _day(v: object) -> str | None:
    s = str(v or "")[:10]
    return s if is_date(s) else None


def _cultcode(link: str) -> str:
    try:
        return (parse_qs(urlsplit(link).query).get("cultcode") or [""])[0]
    except ValueError:
        return ""


def _float(v: object) -> float | None:
    try:
        f = float(str(v))
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) or math.isinf(f) else f


def observation_from_row(row: Mapping, *, region: Region, collected_at: str) -> Observation | None:
    """한 행 → 관찰값. 제목이 없으면 None. 모르는 값은 비워 둔다."""
    title = norm_text(str(row.get("TITLE") or ""))
    if not title:
        return None
    link = str(row.get("HMPG_ADDR") or "")
    code = _cultcode(link)
    place = norm_text(str(row.get("PLACE") or ""))
    rng = _DATE_RANGE.search(str(row.get("DATE") or ""))
    start = _day(row.get("STRTDATE")) or (rng.group(1) if rng else None)
    end = _day(row.get("END_DATE")) or (rng.group(2) if rng else None)
    if start and end and end < start:
        end = None
    seed = code or hashlib.sha1(f"{title}|{place}|{start}".encode()).hexdigest()[:12]
    pro = norm_text(str(row.get("PRO_TIME") or ""))
    sessions: tuple[Session, ...] = ()
    if start and start == end and is_hhmm(pro):
        sessions = (Session(date=start, start_time=pro, venue_name=place),)
    lat, lng = _float(row.get("LAT")), _float(row.get("LOT"))
    if lat is None or lng is None or not (-90 <= lat <= 90 and -180 <= lng <= 180):
        lat = lng = None
    venue = classify_venue(
        name=place, gu=str(row.get("GUNAME") or ""), lat=lat, lng=lng, region=region
    )
    if sessions and venue.in_target != "unknown":
        sessions = tuple(Session(**{**s.__dict__, "in_target": venue.in_target}) for s in sessions)
    free = {"무료": "free", "유료": "paid"}.get(norm_text(str(row.get("IS_FREE") or "")), "unknown")
    org = norm_text(str(row.get("ORG_NAME") or ""))
    org_link = str(row.get("ORG_LINK") or "")
    quote = norm_text(f"{title} / {row.get('DATE') or ''} / {place}")
    origin = f"culture.seoul.go.kr#{code}" if code else f"{SOURCE_ID}#{seed}"
    return Observation(
        obs_id=f"seoul:{seed}",
        title=title,
        description=norm_text(" ".join(x for x in (str(row.get("PROGRAM") or ""),
                                                   str(row.get("ETC_DESC") or "")) if x.strip())),
        event_type=norm_text(str(row.get("CODENAME") or "")),
        organizer="" if org in ("", "기타") else org,
        venue=venue,
        schedule=Schedule(start_date=start, end_date=end, sessions=sessions,
                          hours_text=pro if pro and not is_hhmm(pro) else ""),
        price=Price(kind=free, text=norm_text(str(row.get("USE_FEE") or ""))),
        reservation=Reservation(
            link=org_link if org_link.startswith(("http://", "https://")) else "",
            note="출처가 준 주최·예매 링크 — 예약 필요 여부는 확인 필요" if org_link else "",
        ),
        eligibility=parse_eligibility(str(row.get("USE_TRGT") or ""),
                                      extra=str(row.get("ETC_DESC") or "")),
        external_ids=(f"seoul_cult:{code}",) if code else (),
        evidence=Evidence(
            source_id=SOURCE_ID, source_name=SOURCE_NAME, kind="official_api",
            url=link if link.startswith(("http://", "https://")) else "", quote=quote,
            origin=origin, collected_at=collected_at, published_at=_day(row.get("RGSTDATE")),
        ),
        published_at=_day(row.get("RGSTDATE")),
    )


def observations_from_rows(
    rows: Sequence[Mapping], *, region: Region, collected_at: str
) -> list[Observation]:
    """대상 지역에서 열리는 행만 관찰값으로 만든다. 장소 판정이 ``no`` 인 행은 버린다(``unknown`` 은 남긴다)."""
    out = []
    for r in rows:
        o = observation_from_row(r, region=region, collected_at=collected_at)
        if o is not None and o.venue.in_target != "no":
            out.append(o)
    return out
