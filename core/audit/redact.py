"""비밀 마스킹과 문자열 자르기. 표준 라이브러리만 쓴다.

마스킹 정책(오탐보다 누출 방지 우선, 단 아래 경계는 지킨다):
- 토큰 모양: nvapi-*, sk-*, Bearer *.
- `Authorization: (Basic|Bearer|Token) 값` 은 헤더 전체를 가린다.
- key=value / key: value / repr 의 `'key': 'value'`: 키 이름이
  api[_-]?key|token|secret|password|passwd|authorization 으로 끝나는 식별자(접두 허용:
  access_token, x-api-key)이면 값만 가린다. 키는 남긴다.
- 키 이름은 단어 경계에서 끝나야 한다: `max_tokens=5`, `tokens: 3` 은 가리지 않는다.
- 구분자(= 또는 :)가 없는 일반 문장 속 "token" 은 가리지 않는다.
- 알려진 오탐: `token: 설명` 처럼 구분자가 붙은 문장은 값이 가려진다(누출보다 낫다고 판단).
- dict 의 키 자리에 든 토큰 모양 문자열도 가린다.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

REDACTED = "***REDACTED***"
SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"nvapi-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/\-]{10,}=*"),
)
_NAME = r"(?:api[_-]?key|token|secret|password|passwd|authorization)"
_VALUE = r"""(?:"[^"]*"|'[^']*'|[^\s,;&"'})\]]+)"""
_AUTH_HEADER = re.compile(r"(?i)(\bauthorization\b[\"']?\s*[=:]\s*)(?:basic|bearer|token)\s+\S+")
_KEY_VALUE = re.compile(
    rf"(?i)(\b[\w-]*{_NAME}\b[\"']?\s*[=:]\s*)(?!{re.escape(REDACTED)}){_VALUE}"
)
SECRET_KEY_PARTS = ("key", "token", "secret", "password", "authorization", "cookie", "credential")
MAX_STR = 512

_JSON_SCALARS = (str, int, float, bool, type(None))


def redact_text(s: str) -> str:
    """패턴과 일치하는 부분만 REDACTED 로 바꾼다. 자르지 않는다."""
    for pattern in SECRET_PATTERNS:
        s = pattern.sub(REDACTED, s)
    s = _AUTH_HEADER.sub(lambda m: m.group(1) + REDACTED, s)
    s = _KEY_VALUE.sub(lambda m: m.group(1) + REDACTED, s)
    return s


def truncate(s: str, n: int = MAX_STR) -> str:
    if len(s) > n:
        return s[:n] + f"…(+{len(s) - n})"
    return s


def _redact_value(v: Any) -> Any:
    if isinstance(v, str):
        return truncate(redact_text(v))
    if isinstance(v, Mapping):
        return redact(v)
    if isinstance(v, (list, tuple)):
        return [_redact_value(x) for x in v]
    if isinstance(v, _JSON_SCALARS):
        return v
    return truncate(redact_text(repr(v)))


def redact(args: Mapping[str, Any]) -> dict[str, Any]:
    """인자를 재귀로 마스킹한다. 비밀스러운 키의 값은 통째로 가린다."""
    out: dict[str, Any] = {}
    for k, v in args.items():
        key = redact_text(str(k))
        lowered = key.lower()
        if any(part in lowered for part in SECRET_KEY_PARTS):
            out[key] = REDACTED
        else:
            out[key] = _redact_value(v)
    return out
