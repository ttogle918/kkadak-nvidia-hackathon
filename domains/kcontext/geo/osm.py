"""OSM 기반 도보 경로 공급자: OSRM 호환 HTTP 경로 엔진(예: 직접 띄운 OSRM foot 프로필·Valhalla 의 OSRM 호환 API).

요청·응답 형식은 OSRM HTTP API(route service) 문서를 따른다:
  ``GET {base}/route/v1/{profile}/{lng},{lat};{lng},{lat}?overview=false`` → ``{"code": "Ok", "routes": [{"duration": 초}]}``
**실서버로 확인하지 못했다.** 공개 데모 서버(router.project-osrm.org)는 자동차 경로만 주므로 기본으로 쓰지 않고,
``KC_OSM_ROUTER_URL`` 이 설정됐을 때만 만든다. 오류·형식 불일치는 None(= 모름)이고 URL 은 어디에도 싣지 않는다.
"""

from __future__ import annotations

import ipaddress
import json
import math
import time
from urllib.parse import urlsplit

import httpx

from domains.kcontext.catalog.routes import LatLng

__all__ = ["OsrmWalkProvider", "is_loopback_url"]

MAX_CALLS = 200  # 한 인스턴스(= 한 요청)에서 부르는 횟수 상한
MAX_BODY = 64 * 1024  # 응답 본문 상한(바이트)
BUDGET_S = 20.0  # 한 인스턴스가 쓸 수 있는 전체 시간(호출 프로세스 제한 60초보다 짧게)


def _loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def is_loopback_url(url: str) -> bool:
    """주소의 호스트가 루프백(localhost·127.x·::1)인가. 파싱이 안 되면 False."""
    try:
        host = urlsplit(url).hostname
    except ValueError:
        return False
    return bool(host) and _loopback(host)


class OsrmWalkProvider:
    name = "osm_route_engine"
    mode = "walk"
    estimated = False  # 경로 엔진의 계산값이다(직선 추정이 아니다)

    def __init__(self, base_url: str, *, profile: str = "foot", client: httpx.Client | None = None,
                 timeout: float = 5.0, max_calls: int = MAX_CALLS,
                 budget_s: float = BUDGET_S) -> None:
        u = urlsplit(base_url)
        if u.scheme not in ("http", "https") or not u.hostname or u.username or u.password:
            raise ValueError("base_url 은 사용자 정보가 없는 http(s) 주소여야 한다")
        if u.scheme == "http" and not _loopback(u.hostname):
            raise ValueError("원격 경로 엔진은 https 만 쓴다(좌표가 평문으로 나가지 않게). http 는 루프백만 허용")
        self._base = base_url.rstrip("/")
        self._profile = profile
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=False)
        self._deadline = time.monotonic() + max(0.0, min(BUDGET_S, float(budget_s)))
        self._max = max_calls
        self._calls = 0
        self._cache: dict[tuple, int | None] = {}

    def minutes(self, a: LatLng, b: LatLng) -> int | None:
        key = (round(a[0], 5), round(a[1], 5), round(b[0], 5), round(b[1], 5))
        if key in self._cache:
            return self._cache[key]
        for p in (a, b):
            if not (all(isinstance(x, (int, float)) and math.isfinite(x) for x in p) and -90 <= p[0] <= 90
                    and -180 <= p[1] <= 180):
                return None
        if self._calls >= self._max or time.monotonic() > self._deadline:
            return None
        self._calls += 1
        url = f"{self._base}/route/v1/{self._profile}/{a[1]:.6f},{a[0]:.6f};{b[1]:.6f},{b[0]:.6f}"
        try:
            with self._client.stream("GET", url, params={"overview": "false", "alternatives": "false"}) as r:
                r.raise_for_status()
                body = b""
                for chunk in r.iter_bytes():
                    body += chunk
                    if len(body) > MAX_BODY:
                        raise ValueError("response too large")
            data = json.loads(body)
            dur = data["routes"][0]["duration"] if isinstance(data, dict) and data.get("code") == "Ok" else None
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, AttributeError):
            dur = None
        out = max(1, math.ceil(float(dur) / 60)) if isinstance(dur, (int, float)) and not isinstance(dur, bool) \
            and math.isfinite(dur) and dur >= 0 else None
        self._cache[key] = out
        return out
