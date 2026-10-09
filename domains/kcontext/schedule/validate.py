"""원문 확인용 도구 — 정규화·날짜·시각 해석. 모델이 낸 값을 원문(quote)에서 확인할 때만 쓴다.

모두 순수 함수다. 시각은 Asia/Seoul 벽시계 문자열("HH:MM")·분 단위 정수로만 다룬다.
지역 이름은 코드에 두지 않는다.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date

__all__ = [
    "DateMention",
    "TimeMention",
    "find_dates",
    "find_times",
    "norm_text",
    "parse_hhmm",
    "parse_llm_date",
    "resolve_date",
    "squash_map",
]

_WS = re.compile(r"\s+")


def norm_text(s: str) -> str:
    """NFKC + 공백 한 칸. 출력용(source_quote)."""
    return _WS.sub(" ", unicodedata.normalize("NFKC", s)).strip()


def squash_map(nt: str) -> tuple[str, list[int]]:
    """공백을 없애고 casefold 한 문자열과, 각 글자가 ``nt`` 의 몇 번째 글자에서 왔는지.

    ``nt`` 는 이미 NFKC 로 정규화된 문자열이어야 한다.
    """
    out: list[str] = []
    idx: list[int] = []
    for i, ch in enumerate(nt):
        if ch.isspace():
            continue
        for c in ch.casefold():
            out.append(c)
            idx.append(i)
    return "".join(out), idx


# ---------------------------------------------------------------- 날짜

_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3, "apr": 4, "april": 4,
    "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7, "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}
_MON = "|".join(sorted(_MONTHS, key=len, reverse=True))
_ISO = re.compile(r"(?<!\d)(\d{4})\s*[-./년]\s*(\d{1,2})\s*[-./월]\s*(\d{1,2})\s*일?(?!\d)")
_KO_MD = re.compile(r"(?<!\d)(\d{1,2})\s*월\s*(\d{1,2})\s*일")
_SLASH = re.compile(r"(?<![\d/])(\d{1,2})\s*/\s*(\d{1,2})(?![\d/:])")
_EN_MD = re.compile(rf"\b({_MON})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?\b(?:\s*,?\s*(\d{{4}}))?")
_EN_DM = re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({_MON})\b\.?(?:\s*,?\s*(\d{{4}}))?")


@dataclass(frozen=True)
class DateMention:
    pos: int
    year: int | None
    month: int
    day: int


def find_dates(text: str) -> list[DateMention]:
    """텍스트 안의 날짜 표기를 위치 순으로. 달력에 없는 날(2/30 등)은 해석 단계에서 걸린다."""
    t = text.casefold()
    found: list[DateMention] = []
    spans: list[tuple[int, int]] = []

    def free(m: re.Match[str]) -> bool:
        return not any(m.start() < e and s < m.end() for s, e in spans)

    def add(m: re.Match[str], y: int | None, mo: int, d: int) -> None:
        if 1 <= mo <= 12 and 1 <= d <= 31:
            spans.append((m.start(), m.end()))
            found.append(DateMention(m.start(), y, mo, d))

    for m in _ISO.finditer(t):
        add(m, int(m[1]), int(m[2]), int(m[3]))
    for m in _KO_MD.finditer(t):
        if free(m):
            add(m, None, int(m[1]), int(m[2]))
    for m in _EN_MD.finditer(t):
        if free(m):
            add(m, int(m[3]) if m[3] else None, _MONTHS[m[1]], int(m[2]))
    for m in _EN_DM.finditer(t):
        if free(m):
            add(m, int(m[3]) if m[3] else None, _MONTHS[m[2]], int(m[1]))
    for m in _SLASH.finditer(t):
        if free(m):
            a, b = int(m[1]), int(m[2])
            # 기본은 월/일. 앞 숫자가 12 를 넘고 뒤가 12 이하일 때만 일/월로 본다.
            add(m, None, *((b, a) if a > 12 >= b else (a, b)))
    return sorted(found, key=lambda x: x.pos)


_LLM_DATE = re.compile(r"^(?:(\d{4})-)?(\d{1,2})-(\d{1,2})$")


def parse_llm_date(v: str) -> tuple[int | None, int, int] | None:
    """모델이 낸 "YYYY-MM-DD" 또는 "MM-DD". 그 밖의 형식은 None."""
    m = _LLM_DATE.match(v.strip().lstrip("-") if v.strip().startswith("--") else v.strip())
    if not m:
        return None
    return (int(m[1]) if m[1] else None, int(m[2]), int(m[3]))


def resolve_date(
    year: int | None, month: int, day: int, trip: tuple[date, date] | None, today: date | None = None
) -> tuple[date | None, str | None]:
    """(날짜, 문제코드). 연도 없는 날짜는 trip 범위 안에서 하나로 정해질 때만 보충한다.

    trip 이 없으면 today(오늘, 포함) 이후 가장 가까운 그 월·일로 정하고 ("YEAR_ASSUMED") 코드를 함께 준다(D22 ②).
    today 가 없으면 정하지 않는다("YEAR_UNKNOWN"). 존재하지 않는 날(2/29)은 다음에 존재하는 해로 간다.
    """
    if year is not None:
        try:
            d = date(year, month, day)
        except ValueError:
            return None, "DATE_INVALID"
        if trip and not (trip[0] <= d <= trip[1]):
            return None, "DATE_OUT_OF_TRIP"
        return d, None
    if trip is None:
        if today is None:
            return None, "YEAR_UNKNOWN"
        for y in range(today.year, today.year + 9):  # 2/29 는 최대 8년 뒤
            try:
                d = date(y, month, day)
            except ValueError:
                continue
            if d >= today:
                return d, "YEAR_ASSUMED"
        return None, "DATE_INVALID"
    hits: list[date] = []
    for y in range(trip[0].year, trip[1].year + 1):
        try:
            d = date(y, month, day)
        except ValueError:
            continue
        if trip[0] <= d <= trip[1]:
            hits.append(d)
    if len(hits) == 1:
        return hits[0], None
    return None, "DATE_OUT_OF_TRIP" if not hits else "DATE_AMBIGUOUS"


# ---------------------------------------------------------------- 시각


@dataclass(frozen=True)
class TimeMention:
    pos: int
    minutes: frozenset[int]  # 가능한 하루 중 분(0~1439)
    ambiguous: bool  # 오전·오후 표기가 없어 둘 다 가능


_KO_T = re.compile(
    r"(오전|오후|아침|낮|저녁|밤|새벽)?\s*(\d{1,2})\s*시(?!간)(?:\s*(\d{1,2})\s*분|\s*(반))?"
)
_CLOCK = re.compile(
    r"(?<![\d:./])(\d{1,2})(?::(\d{2}))?\s*(a\.m\.|p\.m\.|am|pm)?(?![\d:]|[a-z])"
)
_EN_BARE = re.compile(
    r"\b(?:at|from|to|until|till|before|after|by)\s+(\d{1,2})"
    r"(?![\d:/.]|\s*(?:am|pm|a\.m|p\.m)|\s*(?:people|persons?|nights?|days?|hours?|hrs?|min))"
)
_NOON = re.compile(r"정오|\bnoon\b")
_MIDNIGHT = re.compile(r"자정|\bmidnight\b")


def _ko_hour(marker: str | None, h: int) -> tuple[frozenset[int], bool] | None:
    """한국어 "N시" 의 가능한 시(0~23). 못 읽으면 None."""
    if h > 24:
        return None
    if h == 24:
        return frozenset({0}), False
    if marker in ("오전", "아침", "새벽"):
        return frozenset({0 if h == 12 else h}), False
    if marker in ("오후", "저녁"):
        return frozenset({12 if h == 12 else h + 12 if h < 12 else h}), False
    if marker == "밤":
        return frozenset({0 if h == 12 else h if h <= 5 else h + 12 if h < 12 else h}), False
    if marker == "낮":
        return frozenset({h + 12 if 1 <= h <= 6 else h}), False
    if h == 0 or h >= 13:
        return frozenset({h}), False
    return frozenset({h % 12, h % 12 + 12}), True


def find_times(text: str) -> list[TimeMention]:
    """텍스트 안의 시각 표기. 해석이 둘 이상이면 가능한 값을 모두 담고 ambiguous 로 표시한다."""
    t = text.casefold()
    out: list[TimeMention] = []
    spans: list[tuple[int, int]] = []

    def free(m: re.Match[str]) -> bool:
        return not any(m.start() < e and s < m.end() for s, e in spans)

    def add(m: re.Match[str], mins: frozenset[int], amb: bool) -> None:
        spans.append((m.start(), m.end()))
        out.append(TimeMention(m.start(), mins, amb))

    for m in _KO_T.finditer(t):
        mm = 30 if m[4] else int(m[3]) if m[3] else 0
        r = _ko_hour(m[1], int(m[2]))
        if r and mm < 60:
            add(m, frozenset(h * 60 + mm for h in r[0]), r[1])
    for m in _CLOCK.finditer(t):
        if not free(m) or (m[2] is None and m[3] is None):
            continue  # 콜론도 am/pm 도 없는 숫자는 시각이 아니다
        h, mm, mer = int(m[1]), int(m[2] or 0), m[3]
        if mm >= 60:
            continue
        if mer:
            if not 1 <= h <= 12:
                continue
            h = h % 12 + (12 if mer.startswith("p") else 0)
            add(m, frozenset({h * 60 + mm}), False)
        elif h > 24:
            continue
        elif m[1].startswith("0") or h == 0 or h >= 10:
            add(m, frozenset({(h % 24) * 60 + mm}), False)
        else:  # "2:30" — 24시간제인지 12시간제인지 모른다
            add(m, frozenset({h * 60 + mm, (h + 12) * 60 + mm}), True)
    for m in _EN_BARE.finditer(t):
        h = int(m[1])
        if free(m) and 1 <= h <= 12:
            add(m, frozenset({h % 12 * 60, (h % 12 + 12) * 60}), True)
        elif free(m) and 13 <= h <= 23:
            add(m, frozenset({h * 60}), False)
    for m in _NOON.finditer(t):
        add(m, frozenset({720}), False)
    for m in _MIDNIGHT.finditer(t):
        add(m, frozenset({0}), False)
    return sorted(out, key=lambda x: x.pos)


_HHMM = re.compile(r"^(\d{1,2}):(\d{2})$")


def parse_hhmm(v: str) -> int | None:
    """모델이 낸 "HH:MM" → 분. 0:00~23:59 밖이거나 형식이 다르면 None."""
    m = _HHMM.match(v.strip())
    if not m:
        return None
    h, mm = int(m[1]), int(m[2])
    return h * 60 + mm if h < 24 and mm < 60 else None
