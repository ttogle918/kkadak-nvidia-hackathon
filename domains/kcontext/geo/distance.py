"""두 좌표 사이 직선(대원) 거리."""

from __future__ import annotations

import math

__all__ = ["haversine_m"]

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(h)))
