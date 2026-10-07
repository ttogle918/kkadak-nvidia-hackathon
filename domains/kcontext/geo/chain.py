"""공급자를 D9 순서대로 이어 붙인다: 앞 공급자가 모르면 다음 공급자. 어느 공급자가 답했는지와 추정 여부를 기록한다."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence

from domains.kcontext.catalog.routes import LatLng, NullRouteProvider, RouteProvider

from .estimate import StraightLineEstimator
from .osm import OsrmWalkProvider

__all__ = ["ChainRouteProvider", "make_route_provider"]

MODES = ("none", "estimate", "osm", "chain")


class ChainRouteProvider:
    mode = "walk"

    def __init__(self, providers: Sequence[RouteProvider]) -> None:
        self._ps = list(providers)
        self._used: list[str] = []
        self._estimated = False

    def begin(self) -> None:
        """한 계산(앞→행사·행사→뒤·앞→뒤)을 시작한다. 쓴 공급자·추정 여부를 비운다."""
        self._used, self._estimated = [], False

    @property
    def name(self) -> str:
        return "+".join(self._used) if self._used else "none"

    @property
    def estimated(self) -> bool:
        return self._estimated  # 한 구간이라도 추정값이면 True

    def minutes(self, a: LatLng, b: LatLng) -> int | None:
        for p in self._ps:
            m = p.minutes(a, b)
            if m is not None:
                if p.name not in self._used:
                    self._used.append(p.name)
                self._estimated = self._estimated or bool(p.estimated)
                return m
        return None


def make_route_provider(env: Mapping[str, str] | None = None) -> RouteProvider:
    """``KC_ROUTE_PROVIDER``: none(기본) | estimate | osm | chain. 모르는 값은 none.

    ``osm``·``chain`` 은 ``KC_OSM_ROUTER_URL`` 이 있을 때만 OSM 공급자를 넣는다. 카카오맵 MCP 는 연결하지 않았다.
    """
    e = os.environ if env is None else env
    mode = e.get("KC_ROUTE_PROVIDER", "none")
    if mode not in MODES or mode == "none":
        return NullRouteProvider()
    chain: list[RouteProvider] = []
    url = e.get("KC_OSM_ROUTER_URL", "").strip()
    if mode in ("osm", "chain") and url:
        try:
            chain.append(OsrmWalkProvider(url))
        except ValueError:
            pass  # 잘못된 주소는 쓰지 않는다
    # D13 ⑥ 은 직선 추정을 금지한다. 결정이 바뀌기 전(docs/geo-walk.proposal.md)에는 운영자가 명시해야만 켠다.
    if mode in ("estimate", "chain") and e.get("KC_ROUTE_ESTIMATE_APPROVED") == "1":
        chain.append(StraightLineEstimator())
    return ChainRouteProvider(chain) if chain else NullRouteProvider()
