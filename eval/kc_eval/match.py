"""일정 앵커 비교 규칙 — 레포에서 유일한 정의(T304 offline · T305 stability · T323 가 import).

- ``norm_name``: NFKC → 공백 제거 → casefold.
- 이름이 서로 포함 관계면 같은 장소.
- 날짜는 실제 ``from``(없으면 ``to``)의 앞 10자, 시각은 ``from``/``to`` 의 11~16자.
- 기대 ``"*"`` 는 무엇이든 통과, ``None`` 은 실제도 ``None``. 숙소 date 는 체크인 날짜(= from).
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any

__all__ = ["match_anchors", "norm_name", "same_place"]

WILDCARD = "*"
_FIELDS = ("type", "date", "from", "to")


def norm_name(s: str) -> str:
    return "".join(unicodedata.normalize("NFKC", s).split()).casefold()


def same_place(expected: str, actual: str) -> bool:
    e, a = norm_name(expected), norm_name(actual)
    if not e or not a:
        return False
    return e in a or a in e


def _slice(value: Any, start: int, stop: int) -> str | None:
    return value[start:stop] if isinstance(value, str) and value else None


def _actual_field(actual: Mapping, field: str) -> Any:
    if field == "type":
        return actual.get("type")
    if field == "date":
        return _slice(actual.get("from"), 0, 10) or _slice(actual.get("to"), 0, 10)
    if field == "from":
        return _slice(actual.get("from"), 11, 16)
    return _slice(actual.get("to"), 11, 16)


def _field_ok(expected: Mapping, actual: Mapping, field: str) -> bool:
    if field not in expected:
        return True
    want = expected[field]
    if want == WILDCARD:
        return True
    return _actual_field(actual, field) == want


def _fails(expected: Mapping, actual: Mapping) -> list[str]:
    return [f for f in _FIELDS if not _field_ok(expected, actual, f)]


def match_anchors(expected: Sequence[Mapping], actual: Sequence[Mapping]) -> dict:
    """기대·실제 앵커 목록을 이름으로 1:1 대응시키고 필드를 비교한다.

    ``{"pairs": [(ei, ai)], "missing": [ei], "extra": [ai],
       "field_fail": [{"i": ei, "field": str}], "exact": bool}``
    같은 이름 후보가 여럿이면 필드가 더 많이 맞는 것(동률이면 앞선 것)을 고른다.
    """
    used: set[int] = set()
    pairs: list[tuple[int, int]] = []
    missing: list[int] = []
    field_fail: list[dict] = []
    for ei, exp in enumerate(expected):
        name = exp.get("name")
        cands = [
            ai
            for ai, act in enumerate(actual)
            if ai not in used
            and isinstance(name, str)
            and isinstance(act.get("name"), str)
            and same_place(name, act["name"])
        ]
        if not cands:
            missing.append(ei)
            continue
        best = min(cands, key=lambda ai: (len(_fails(exp, actual[ai])), ai))
        used.add(best)
        pairs.append((ei, best))
        field_fail.extend({"i": ei, "field": f} for f in _fails(exp, actual[best]))
    extra = [ai for ai in range(len(actual)) if ai not in used]
    exact = not missing and not extra and not field_fail and len(expected) == len(actual)
    return {"pairs": pairs, "missing": missing, "extra": extra, "field_fail": field_fail,
            "exact": exact}  # fmt: skip
