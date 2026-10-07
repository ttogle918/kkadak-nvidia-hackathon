"""OSM 기반 도보 경로 공급자: OSRM 호환 HTTP 경로 엔진(예: 직접 띄운 OSRM foot 프로필·Valhalla 의 OSRM 호환 API).

요청·응답 형식은 OSRM HTTP API(route service) 문서를 따른다:
  ``GET {base}/route/v1/{profile}/{lng},{lat};{lng},{lat}?overview=false`` → ``{"code": "Ok", "routes": [{"duration": 초}]}``
**실서버로 확인하지 못했다.** 공개 데모 서버(router.project-osrm.org)는 자동차 경로만 주므로 기본으로 쓰지 않고,
``KC_OSM_ROUTER_URL`` 이 설정됐을 때만 만든다. 오류·형식 불일치는 None(= 모름)이고 URL 은 어디에도 싣지 않는다.
"""

from __future__ import annotations

import math
from urllib.parse import urlsplit

import httpx

from domains.kcontext.catalog.routes import LatLng

__all__ = ["OsrmWalkProvider"]

MAX_CALLS = 200  # 한 인스턴스(= 한 요청)에서 부르는 횟수 상한


class OsrmWalkProvider:
    name = "osm_route_engine"
    mode = "walk"
    estimated = False  # 경로 엔진의 계산값이다(직선 추정이 아니다)

    def __init__(self, base_url: str, *, profile: str = "foot", client: httpx.Client | None = None,
                 timeout: float = 5.0, max_calls: int = MAX_CALLS) -> None:
        u = urlsplit(base_url)
        if u.scheme not in ("http", "https") or not u.hostname or u.username or u.password:
            raise ValueError("base_url 은 사용자 정보가 없는 http(s) 주소여야 한다")
        self._base = base_url.rstrip("/")
        self._profile = profile
        self._client = client or httpx.Client(timeout=timeout)
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
        if self._calls >= self._max:
            return None
        self._calls += 1
        url = f"{self._base}/route/v1/{self._profile}/{a[1]:.6f},{a[0]:.6f};{b[1]:.6f},{b[0]:.6f}"
        try:
            r = self._client.get(url, params={"overview": "false", "alternatives": "false"})
            r.raise_for_status()
            data = r.json()
            dur = data["routes"][0]["duration"] if data.get("code") == "Ok" else None
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            dur = None
        out = max(1, math.ceil(float(dur) / 60)) if isinstance(dur, (int, float)) and not isinstance(dur, bool) \
            and math.isfinite(dur) and dur >= 0 else None
        self._cache[key] = out
        return out
