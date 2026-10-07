"""검증 실패를 던지는 유일한 곳. 검증기 자체는 던지지 않고 문제 목록을 돌려준다."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from .card import validate_card
from .route import validate_route
from .situation import validate_situation
from .source import validate_source
from .verdict import validate_verdict

Kind = Literal["card", "route", "verdict", "situation", "source"]

__all__ = ["ContractError", "ensure_valid"]


class ContractError(ValueError):
    """계약 위반. ``problems`` 에 문제 문구 전체가 있다."""

    def __init__(self, problems: list[str] | tuple[str, ...]) -> None:
        self.problems: tuple[str, ...] = tuple(problems)
        shown = "; ".join(self.problems[:5])
        more = f" (외 {len(self.problems) - 5}건)" if len(self.problems) > 5 else ""
        super().__init__(f"계약 위반 {len(self.problems)}건: {shown}{more}")


def ensure_valid(kind: Kind, obj: Mapping) -> None:
    validators = {
        "card": validate_card,
        "route": validate_route,
        "verdict": validate_verdict,
        "situation": validate_situation,
        "source": validate_source,
    }
    if kind not in validators:
        raise ValueError(f"알 수 없는 kind: {kind!r}")
    problems = validators[kind](obj)
    if problems:
        raise ContractError(problems)
