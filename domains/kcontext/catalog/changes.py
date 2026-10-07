"""행사 변경 비교. 날짜·시간·장소·요금·예약조건·취소 변경을 이력으로 남긴다.

개최 상태는 시간이 흘러 바뀌는 값(예정→진행→종료)이 아니라 **출처가 알린 취소·연기**만 변경으로 본다.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass

from .model import EventEntry

__all__ = ["MAJOR_FIELDS", "Change", "diff_catalog", "diff_entries"]


@dataclass(frozen=True)
class Change:
    entry_id: str
    field: str
    old: object
    new: object
    detected_at: str
    importance: str  # "major" | "minor" | "new"
    title: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _sessions(e: EventEntry) -> list:
    return [[s.date, s.start_time, s.end_time, s.venue_name] for s in e.schedule.sessions]


def _reported_lifecycle(e: EventEntry) -> str:
    return e.lifecycle if e.lifecycle in ("cancelled", "postponed") else "none"


_TRACKED: list[tuple[str, str, Callable[[EventEntry], object]]] = [
    ("start_date", "major", lambda e: e.schedule.start_date),
    ("end_date", "major", lambda e: e.schedule.end_date),
    ("sessions", "major", _sessions),
    ("hours", "major", lambda e: e.schedule.hours_text),
    ("closures", "major", lambda e: [list(e.schedule.weekly_closed_days), list(e.schedule.closed_dates),
                                      e.schedule.holiday_rule]),
    ("entry_cutoff", "major", lambda e: e.schedule.entry_cutoff),
    ("venue", "major", lambda e: [e.venue.name, e.venue.address]),
    ("price", "major", lambda e: [e.price.kind, e.price.text]),
    ("reservation", "major", lambda e: [e.reservation.required, e.reservation.link, e.reservation.deadline,
                                         e.reservation.status]),
    ("lifecycle", "major", _reported_lifecycle),
    ("eligibility", "major", lambda e: [e.eligibility.audience, e.eligibility.resident_only,
                                         e.eligibility.age_limit, e.eligibility.foreigner,
                                         e.eligibility.stated_open]),
    ("language", "minor", lambda e: [list(e.language.languages), e.language.english_guidance,
                                      e.language.english_subtitles]),
    ("title", "minor", lambda e: e.title),
    ("description", "minor", lambda e: e.description),
]
MAJOR_FIELDS = tuple(f for f, imp, _ in _TRACKED if imp == "major")


def diff_entries(old: EventEntry, new: EventEntry, at: str) -> list[Change]:
    out = []
    for name, importance, get in _TRACKED:
        a, b = get(old), get(new)
        if a != b:
            out.append(Change(new.id, name, a, b, at, importance, new.title))
    return out


def diff_catalog(old: Sequence[EventEntry], new: Sequence[EventEntry], at: str) -> list[Change]:
    """새 항목은 ``field="__new__"``. 사라진 항목은 변경으로 세지 않는다(관찰값은 지우지 않는다)."""
    before = {e.id: e for e in old}
    out: list[Change] = []
    for e in new:
        if e.id not in before:
            out.append(Change(e.id, "__new__", None, e.title, at, "new", e.title))
        else:
            out.extend(diff_entries(before[e.id], e, at))
    return out
