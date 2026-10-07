"""직선 추정 도보 공급자. 결과는 **예상 시간**이며 경로 서비스의 값이 아니다(``estimated=True``).

도보 시간 ≈ 직선거리 × 우회 계수 ÷ 보행 속도. 두 값은 [제안, 시험 후 조정]이다(sprint-2 T212 의 GeoConfig 와 같은 값).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from domains.kcontext.catalog.routes import LatLng

from .distance import haversine_m

__all__ = ["GeoConfig", "StraightLineEstimator"]


@dataclass(frozen=True)
class GeoConfig:
    speed_m_per_min: float = 67.0  # 약 4 km/h
    detour_factor: float = 1.3  # 직선보다 길 위로는 더 돌아간다


class StraightLineEstimator:
    name = "straight_line_estimate"
    mode = "walk"
    estimated = True

    def __init__(self, cfg: GeoConfig = GeoConfig()) -> None:  # noqa: B008
        if cfg.speed_m_per_min <= 0 or cfg.detour_factor < 1:
            raise ValueError("speed_m_per_min 은 양수, detour_factor 는 1 이상이어야 한다")
        self._cfg = cfg

    def minutes(self, a: LatLng, b: LatLng) -> int | None:
        for p in (a, b):
            if not (len(p) == 2 and all(isinstance(x, (int, float)) and math.isfinite(x) for x in p)
                    and -90 <= p[0] <= 90 and -180 <= p[1] <= 180):
                return None
        return max(1, math.ceil(haversine_m(a, b) * self._cfg.detour_factor / self._cfg.speed_m_per_min)) if a != b else 0
