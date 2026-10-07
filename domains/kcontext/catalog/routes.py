"""이동시간 공급자. 이동시간은 지도·경로 서비스의 결과만 쓰고, 직선거리를 도보시간으로 바꾸지 않는다(D9).

이 모듈에는 일부러 거리 기반 추정 공급자를 두지 않았다. 경로 서비스가 연결되지 않았으면 ``NullRouteProvider`` 가
``None`` 을 돌려주고, 호출한 쪽은 "이동시간 확인 필요"로 표시한다.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

__all__ = ["LatLng", "NullRouteProvider", "RouteProvider", "TableRouteProvider"]

LatLng = tuple[float, float]


class RouteProvider(Protocol):
    name: str
    mode: str  # "walk" 등. 한 번의 계산에서는 같은 mode 만 쓴다.
    estimated: bool  # 공급자가 추정값을 줬다면 True (화면에 "추정"으로 표시)

    def minutes(self, a: LatLng, b: LatLng) -> int | None:
        """a → b 이동 분. 얻을 수 없으면 None."""
        ...


class NullRouteProvider:
    name = "none"
    mode = "walk"
    estimated = False

    def minutes(self, a: LatLng, b: LatLng) -> int | None:
        return None


class TableRouteProvider:
    """미리 받아 둔 경로 결과 표(테스트·오프라인 데모용). 같은 쌍이 없으면 None."""

    def __init__(self, table: Mapping[tuple[LatLng, LatLng], int], *, name: str = "table",
                 mode: str = "walk", estimated: bool = False, symmetric: bool = True) -> None:
        self._t = {(_k(a), _k(b)): int(m) for (a, b), m in table.items()}
        if symmetric:
            self._t.update({(b, a): m for (a, b), m in list(self._t.items()) if (b, a) not in self._t})
        self.name, self.mode, self.estimated = name, mode, estimated

    def minutes(self, a: LatLng, b: LatLng) -> int | None:
        return self._t.get((_k(a), _k(b)))


def _k(p: LatLng) -> LatLng:
    return (round(float(p[0]), 5), round(float(p[1]), 5))
