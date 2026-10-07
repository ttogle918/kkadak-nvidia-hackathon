"""다국어 문자열(Text)과 검증기가 공유하는 작은 도우미.

``Text`` 는 ``str`` 또는 ``{"ko": str, "en": str}`` 이다(프론트 ``isText`` 와 같은 모양).
Python 쪽은 프론트보다 엄격해서 빈 문자열을 허용하지 않는다.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping

Text = str | dict[str, str]

__all__ = ["Text", "is_date", "is_hhmm", "is_nonempty_str", "is_number", "is_text", "pick"]

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_HHMM_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def is_nonempty_str(v: object) -> bool:
    return isinstance(v, str) and v != ""


def is_number(v: object) -> bool:
    """bool 은 숫자가 아니다. NaN·inf 도 아니다."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return False
    return math.isfinite(v)


def is_text(v: object) -> bool:
    if isinstance(v, str):
        return v != ""
    if isinstance(v, Mapping):
        return is_nonempty_str(v.get("ko")) and is_nonempty_str(v.get("en"))
    return False


def pick(v: Text, lang: str = "ko") -> str:
    """Text 에서 ``lang`` 문자열을 고른다. dict 에 그 키가 없으면 ko."""
    if isinstance(v, str):
        return v
    return v.get(lang) or v["ko"]


def is_date(v: object) -> bool:
    """``YYYY-MM-DD`` 이고 실제 달력에 있는 날짜."""
    if not isinstance(v, str) or not _DATE_RE.match(v):
        return False
    import datetime

    try:
        datetime.date.fromisoformat(v)
    except ValueError:
        return False
    return True


def is_hhmm(v: object) -> bool:
    return isinstance(v, str) and bool(_HHMM_RE.match(v))
