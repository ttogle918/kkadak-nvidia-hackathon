"""방문 앵커 → 날짜별 이동 구간(``routes``). 호스트 에이전트 프로세스 전용(D10).

규칙(D16·D18):
- 방문(visit) 앵커만 쓴다. 숙소는 이동 구간에서 뺀다. 실록 언급 좌표로는 길을 만들지 않는다(앵커 좌표만 쓴다).
- ``from`` 이 있는 방문을 날짜별·시각순으로 놓고 이웃 쌍마다 구간 하나. 둘 다 좌표가 있어야 한다.
- 이동시간은 공급자가 준 값만 쓴다. 공급자가 모르면 ``walk_min: null``. 직선거리를 시간으로 바꾸지 않는다.
- 같은 장소가 이어지면 0m·0분·``provider: "same_place"``.
- 좌표가 없는 쪽이 있으면 skipped "좌표 없음". ``from`` 이 없는 방문은 skipped "시각 없음"(``to`` 는 빈 문자열) —
  날짜를 (여행 시작일 + day) 로 알 수 있을 때만 그 날 경로에 넣고, 모르면 어느 날에도 못 넣으므로 뺀다.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from itertools import pairwise
from typing import Any

from domains.kcontext.catalog.routes import RouteProvider
from domains.kcontext.geo.distance import haversine_m

__all__ = ["MAX_LEGS", "MAX_ROUTES", "MAX_SKIPPED", "NAME_CAP", "build_routes"]

MAX_ROUTES = 7
MAX_LEGS = 20
MAX_SKIPPED = 20
NAME_CAP = 80  # backend clean_bundle 의 from/to 상한
_ISO_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _ll(a: Mapping[str, Any]) -> tuple[float, float] | None:
    lat, lng = a.get("lat"), a.get("lng")
    if _num(lat) and _num(lng) and -90 <= lat <= 90 and -180 <= lng <= 180:
        return float(lat), float(lng)
    return None


def _name(a: Mapping[str, Any]) -> str:
    return str(a.get("name") or "").strip()[:NAME_CAP]


def _day_of(a: Mapping[str, Any]) -> int | None:
    d = a.get("day")
    return d if isinstance(d, int) and not isinstance(d, bool) else None


def _date_of(a: Mapping[str, Any], trip_from: str | None) -> str | None:
    f = a.get("from")
    if isinstance(f, str) and _ISO_DAY.match(f[:10]):
        return f[:10]
    day = _day_of(a)
    if day is not None and trip_from and _ISO_DAY.match(trip_from):
        try:
            return (date.fromisoformat(trip_from) + timedelta(days=day - 1)).isoformat()
        except ValueError:
            return None
    return None


def _leg(a: Mapping[str, Any], b: Mapping[str, Any], pa: tuple[float, float], pb: tuple[float, float],
         provider: RouteProvider) -> dict[str, Any]:
    straight = round(haversine_m(pa, pb))
    base = {"from": _name(a), "to": _name(b), "from_ll": [pa[0], pa[1]], "to_ll": [pb[0], pb[1]],
            "straight_m": straight}  # fmt: skip
    if _name(a) == _name(b) or pa == pb:
        return {**base, "straight_m": 0, "walk_min": 0, "provider": "same_place", "estimated": False}
    try:
        begin = getattr(provider, "begin", None)
        if callable(begin):
            begin()
        m = provider.minutes(pa, pb)
    except Exception:  # noqa: BLE001 - 공급자 오류는 "모름"으로 — 지어내지 않는다
        m = None
    if m is None or isinstance(m, bool) or not isinstance(m, int) or m < 0:
        return {**base, "walk_min": None, "provider": "none", "estimated": False}
    return {**base, "walk_min": m, "provider": str(provider.name)[:60], "estimated": bool(provider.estimated)}


def build_routes(
    anchors: Sequence[Mapping[str, Any]], *, provider: RouteProvider, trip_from: str | None = None
) -> list[dict[str, Any]]:
    """날짜별 ``{"id", "day", "date", "legs", "skipped"}``. 구간도 skipped 도 없는 날은 만들지 않는다."""
    by_date: dict[str, dict[str, Any]] = {}

    def bucket(d: str, a: Mapping[str, Any]) -> dict[str, Any]:
        b = by_date.setdefault(d, {"day": None, "timed": [], "untimed": []})
        if b["day"] is None:
            b["day"] = _day_of(a)
        return b

    for a in anchors:
        if not isinstance(a, Mapping) or a.get("type") != "visit" or not _name(a):
            continue
        d = _date_of(a, trip_from)
        if d is None:
            continue
        timed = isinstance(a.get("from"), str) and bool(_ISO_DAY.match(a["from"][:10]))
        bucket(d, a)["timed" if timed else "untimed"].append(a)

    routes: list[dict[str, Any]] = []
    for d in sorted(by_date):
        g = by_date[d]
        timed = sorted(g["timed"], key=lambda x: x["from"])
        legs: list[dict[str, Any]] = []
        skipped: list[dict[str, str]] = []
        for a, b in pairwise(timed):
            pa, pb = _ll(a), _ll(b)
            if pa is None or pb is None:
                skipped.append({"from": _name(a), "to": _name(b), "reason": "좌표 없음"})
            else:
                legs.append(_leg(a, b, pa, pb, provider))
        skipped += [{"from": _name(a), "to": "", "reason": "시각 없음"} for a in g["untimed"]]
        if legs or skipped:
            routes.append({"day": g["day"], "date": d, "legs": legs[:MAX_LEGS], "skipped": skipped[:MAX_SKIPPED]})
    routes = routes[:MAX_ROUTES]

    used = {r["day"] for r in routes if r["day"] is not None and r["day"] >= 1}
    seen: set[str] = set()
    n = 0
    for r in routes:
        if r["day"] is not None and r["day"] >= 1 and f"day{r['day']}" not in seen:
            rid = f"day{r['day']}"
        else:
            n += 1
            while n in used or f"day{n}" in seen:
                n += 1
            rid = f"day{n}"
        seen.add(rid)
        r["id"] = rid
    return [{"id": r["id"], "day": r["day"], "date": r["date"], "legs": r["legs"], "skipped": r["skipped"]}
            for r in routes]
