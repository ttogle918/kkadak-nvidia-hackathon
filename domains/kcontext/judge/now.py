"""행사 판정 (CONTEXT_NOW_KOREA 3장). LLM 호출 없음 — 규칙과 계산만 한다.

흐름: 주입 차단 → 관련성·상황 거르기 → 같은 행사 묶기 → 묶음 안 충돌 해결 → 취소 거르기 → 딱지·판정 객체.
탈락은 전부 ``Rejection`` 으로 남긴다(판단 근거 패널의 깔때기).

출처 등급이 다를 때: 공식(S·A·B) 값이 있으면 그 값끼리만 충돌을 따지고, C·D 출처가 다르게 적은 것은
caveat 로만 남긴다. 공식 값이 없을 때만 C·D 값이 채워지며, C·D 의 취소·변경 정보는 적용하지 않고
caveat 로만 남긴다(D12 "보조 수집").
"""

from __future__ import annotations

import dataclasses
import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from difflib import SequenceMatcher

from domains.kcontext.contract.records import Blocked, EventRecord, Rejection, SourceRef
from domains.kcontext.contract.source import TIERS
from domains.kcontext.contract.text import is_date, pick

from .inject import screen

__all__ = ["Conflict", "EventDecision", "NowConfig", "NowJudgement", "judge_events"]

_PUNCT = re.compile(r"[\W_]+")
_CONFLICT_FIELDS = ("status", "start_time", "start_date", "place_name")
_FIELD_LABEL = {"status": "진행 여부", "start_time": "시작 시간", "start_date": "시작일",
                "place_name": "장소"}
_OFFICIAL = ("S", "A", "B")
_BADGE_TO_VERDICT = {"확인됨": "accepted", "확인 필요": "unverified", "보류": "disputed"}
_CONFIDENCE = {"확인됨": "high", "확인 필요": "medium", "보류": "low"}


@dataclass(frozen=True)
class NowConfig:
    """[제안, 시험 후 조정] 값은 CONTEXT_NOW_KOREA 3.2 의 예시와 스프린트 명세를 따른다."""

    fresh_days: int = 14
    dedupe_m: int = 150
    title_similarity: float = 0.6
    alcohol_categories: tuple[str, ...] = ("night_market", "bar")
    merge_gap_days: int = 60  # 기간이 이보다 멀리 떨어진 같은 이름은 다른 행사(다른 해·다른 회차)


@dataclass(frozen=True)
class Conflict:
    field: str
    values: tuple[dict, ...]
    chosen: str | None
    reason: str


@dataclass(frozen=True)
class EventDecision:
    event_ids: tuple[str, ...]
    primary: EventRecord
    sources: tuple[SourceRef, ...]
    badge: str
    verdicts: tuple[dict, ...]
    caveats: tuple[str, ...]
    conflicts: tuple[Conflict, ...]


@dataclass(frozen=True)
class NowJudgement:
    decisions: tuple[EventDecision, ...]
    rejected: tuple[Rejection, ...]
    blocked: tuple[Blocked, ...]
    funnel: Mapping[str, int]
    problems: tuple[str, ...] = ()


def _title(r: EventRecord) -> str:
    return pick(r.title, "ko")


def _texts(r: EventRecord) -> str:
    """판정 출력(claim·says)이나 색인으로 나갈 수 있는 외부 문자열을 전부 모은다."""
    titles = [r.title] if isinstance(r.title, str) else list(r.title.values())
    s = r.source
    return "\n".join([*titles, r.place_name, r.description, s.name, s.locator, s.quote])


def _norm_title(r: EventRecord) -> str:
    return _PUNCT.sub("", unicodedata.normalize("NFKC", _title(r))).casefold()


def _parse_date(v: str | None) -> date | None:
    if not isinstance(v, str):
        return None
    try:
        return date.fromisoformat(v[:10])
    except ValueError:
        return None


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


def _period(r: EventRecord) -> tuple[str, str] | None:
    """(시작, 끝). 끝이 없으면 하루짜리로 본다. 시작이 없으면 끝 하나만 아는 것으로 본다."""
    start, end = r.start_date, r.end_date
    if start is None and end is None:
        return None
    return (start or end, end or start)  # type: ignore[return-value]


def _gap_days(a: EventRecord, b: EventRecord) -> int:
    """두 기간 사이의 빈 날수. 겹치거나 한쪽이라도 기간을 모르면 0."""
    pa, pb = _period(a), _period(b)
    if pa is None or pb is None:
        return 0
    gap = max(
        (date.fromisoformat(pb[0]) - date.fromisoformat(pa[1])).days,
        (date.fromisoformat(pa[0]) - date.fromisoformat(pb[1])).days,
    )
    return max(gap, 0)


def _overlap(a: EventRecord, b: EventRecord) -> bool:
    pa, pb = _period(a), _period(b)
    return pa is not None and pb is not None and pa[0] <= pb[1] and pb[0] <= pa[1]


def _coord(r: EventRecord) -> tuple[float, float] | None:
    return (r.lat, r.lng) if r.lat is not None and r.lng is not None else None


def _same_event(a: EventRecord, b: EventRecord, cfg: NowConfig) -> bool:
    if a.region != b.region or _gap_days(a, b) > cfg.merge_gap_days:
        return False
    ca, cb = _coord(a), _coord(b)
    dist = _haversine_m(ca, cb) if ca and cb else None
    if _norm_title(a) == _norm_title(b):
        # 이름만 같은 다른 곳: 둘 다 좌표가 있고 멀면 다른 행사다.
        return dist is None or dist <= cfg.dedupe_m
    if dist is None or dist > cfg.dedupe_m or not _overlap(a, b):
        return False
    return SequenceMatcher(None, _norm_title(a), _norm_title(b)).ratio() >= cfg.title_similarity


def _tier_rank(s: SourceRef) -> int:
    return TIERS.index(s.tier)


def _pub_key(s: SourceRef) -> date:
    return _parse_date(s.published) or date.min


def _rank(r: EventRecord) -> tuple:
    # 대표 선정: tier 높은 순 → published 최신 → id
    return (_tier_rank(r.source), -_pub_key(r.source).toordinal(), r.id)


def _value(r: EventRecord, field: str) -> str | None:
    v = getattr(r, field)
    if field == "status" and v == "unknown":
        return None
    return v if isinstance(v, str) and v != "" else None


def _official(r: EventRecord) -> bool:
    return r.source.tier in _OFFICIAL


def _resolve(group: Sequence[EventRecord], field: str) -> tuple[Conflict | None, list[str]]:
    """묶음 안 한 필드의 충돌. 공식 값이 있으면 공식 값끼리만 따지고 나머지는 caveat 로 돌려준다."""
    members = [r for r in group if _value(r, field)]
    official = [r for r in members if _official(r)]
    pool = official or members
    extra: list[str] = []
    if official:
        pool_vals = {_value(r, field) for r in official}
        if any(_value(r, field) not in pool_vals for r in members if not _official(r)):
            extra.append(f"비공식 출처가 {_FIELD_LABEL[field]}을(를) 다르게 적음")
    vals: dict[str, list[EventRecord]] = {}
    for r in pool:
        vals.setdefault(_value(r, field), []).append(r)  # type: ignore[arg-type]
    if len(vals) < 2:
        return None, extra
    values = tuple(
        {"value": v, "source_ids": tuple(m.source.id for m in ms),
         "tiers": tuple(m.source.tier for m in ms),
         "published": tuple(m.source.published for m in ms)}
        for v, ms in vals.items()
    )
    eligible = [r for r in pool if _official(r) and _parse_date(r.source.published)]
    if eligible:
        newest = max(_pub_key(r.source) for r in eligible)
        chosen = {_value(r, field) for r in eligible if _pub_key(r.source) == newest}
        if len(chosen) == 1:
            return Conflict(field, values, chosen.pop(), "최신 공식 공지 채택"), extra
    return Conflict(field, values, None, "최신 공식 공지를 정할 수 없음"), extra


def _merge_sources(group: Sequence[EventRecord]) -> tuple[SourceRef, ...]:
    seen: dict[str, SourceRef] = {}
    for r in sorted(group, key=_rank):
        seen.setdefault(r.source.id, r.source)
    return tuple(seen.values())


def _uniq(items: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def _claim(r: EventRecord) -> str:
    start = r.start_date or "날짜 미상"
    span = start if not r.end_date or r.end_date == r.start_date else f"{start}–{r.end_date}"
    return f"{_title(r)} 행사는 {span} {r.place_name or '장소 미상'}에서 열린다"


def _src_entry(s: SourceRef, stance: str = "support", says: str | None = None) -> dict:
    d: dict = {"id": s.id, "tier": s.tier, "date": s.published or s.collected_at, "stance": stance}
    if says is not None:
        d["says"] = says
    return d


def _adopt_single_values(
    members: Sequence[EventRecord], primary: EventRecord, conflicted: set[str]
) -> tuple[dict[str, str], list[str]]:
    """충돌은 없지만 대표 레코드에 값이 없는 필드를 다른 레코드에서 채운다.

    C·D 출처의 취소·변경은 적용하지 않고 caveat 로만 남긴다.
    """
    adopt: dict[str, str] = {}
    notes: list[str] = []
    for f in _CONFLICT_FIELDS:
        if f in conflicted or _value(primary, f) is not None:
            continue
        have = [(m, _value(m, f)) for m in members if _value(m, f)]
        if not have:
            continue
        m, v = have[0]
        if f == "status" and v in ("cancelled", "changed") and not _official(m):
            notes.append(f"비공식 출처에 '{v}' 정보가 있음 — 확인 필요")
            continue
        adopt[f] = v  # type: ignore[assignment]
    return adopt, notes


def judge_events(records: Sequence[EventRecord], situation: Mapping, *, now: date,
                 cfg: NowConfig = NowConfig()) -> NowJudgement:  # noqa: B008
    rejected: list[Rejection] = []
    blocked: list[Blocked] = []
    problems: list[str] = []
    notes: dict[str, list[str]] = {}
    kept: list[EventRecord] = []

    trip = situation.get("trip") or {}
    trip_from, trip_to = trip.get("from"), trip.get("to")
    if not (is_date(trip_from) and is_date(trip_to) and trip_from <= trip_to):
        problems.append("situation.trip 이 올바르지 않아 기간 거르기를 건너뜀")
        trip_from = trip_to = None
    party = situation.get("party") or {}
    weather = situation.get("weather") or {}

    def reject(r: EventRecord, reason: str, detail: str = "") -> None:
        rejected.append(Rejection(r.id, _title(r), reason, detail or r.source.id))

    for r in records:
        note = notes.setdefault(r.id, [])
        b = screen(_texts(r), r.source.id)
        if b is not None:
            blocked.append(b)
            if b.verdict == "injection":
                reject(r, "지시문 포함")
                continue
            note.append("자료에 지시문 의심 문구")
        if r.region is None:
            reject(r, "관련 없음", "지역 없음")
            continue
        per = _period(r)
        if per is None:
            note.append("날짜 불분명")
        elif trip_from and trip_to:
            if per[1] < trip_from:
                reject(r, "기간 지남", f"종료 {per[1]}")
                continue
            if per[0] > trip_to:
                reject(r, "관련 없음", f"시작 {per[0]} 이 여행 뒤")
                continue
        if party.get("kids") and r.category in cfg.alcohol_categories:
            reject(r, "상황 부적합", "아이 동반")
            continue
        if weather.get("rain") and r.outdoor is True:
            reject(r, "상황 부적합", "비 · 야외 행사")
            continue
        if _coord(r) is None:
            note.append("위치 미상")
        kept.append(r)

    # 같은 행사 묶기: 두 묶음을 합칠 때 양쪽의 모든 쌍이 같은 행사여야 한다(이행적 과병합 방지).
    parent = list(range(len(kept)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def members_of(root: int) -> list[int]:
        return [k for k in range(len(kept)) if find(k) == root]

    for i in range(len(kept)):
        for j in range(i + 1, len(kept)):
            ri, rj = find(i), find(j)
            if ri == rj:
                continue
            if all(_same_event(kept[x], kept[y], cfg)
                   for x in members_of(ri) for y in members_of(rj)):
                parent[rj] = ri
    groups: dict[int, list[EventRecord]] = {}
    for i, r in enumerate(kept):
        groups.setdefault(find(i), []).append(r)

    decisions: list[EventDecision] = []
    for members in groups.values():
        ordered = sorted(members, key=_rank)
        primary = ordered[0]
        conflicts_l: list[Conflict] = []
        extra: list[str] = []
        for f in _CONFLICT_FIELDS:
            c, ex = _resolve(ordered, f)
            extra.extend(ex)
            if c is not None:
                conflicts_l.append(c)
        conflicts = tuple(conflicts_l)
        resolved = {c.field: c.chosen for c in conflicts if c.chosen is not None}
        unresolved = [c for c in conflicts if c.chosen is None]
        adopted, adopt_notes = _adopt_single_values(
            ordered, primary, {c.field for c in conflicts})
        resolved = {**adopted, **resolved}
        primary = dataclasses.replace(primary, **resolved) if resolved else primary
        sources = _merge_sources(ordered)
        caveats = [c for m in ordered for c in notes.get(m.id, [])] + extra + adopt_notes

        if primary.status == "cancelled" and not any(c.field == "status" for c in unresolved):
            for m in ordered:
                reject(m, "취소됨", primary.id)
            continue

        for dup in ordered[1:]:  # 취소로 묶음 전체가 빠지는 경우에는 중복으로 또 세지 않는다
            reject(dup, "중복", primary.id)

        if unresolved:
            badge = "보류"
        else:
            official_src = [s for s in sources if s.tier in _OFFICIAL]
            if not official_src:
                caveats.append("단독 출처")
            if any(not _parse_date(s.published) for s in official_src):
                caveats.append("갱신일 미제공")
            if primary.start_date is None:
                caveats.append("날짜 불분명")
            if not primary.place_name:
                caveats.append("장소 불분명")
            latest = max((_parse_date(s.published) or _parse_date(s.collected_at) or date.min
                          for s in official_src), default=date.min)
            stale = bool(official_src) and latest < now - timedelta(days=cfg.fresh_days)
            if stale:
                caveats.append(f"{(now - latest).days}일 전 갱신")
            ok = official_src and primary.start_date and primary.place_name and not stale
            badge = "확인됨" if ok else "확인 필요"

        official_only = any(s.tier in _OFFICIAL for s in sources)
        verdicts: list[dict] = [{
            "claim": _claim(primary),
            "sources": [_src_entry(s, says=s.quote[:200]) for s in sources],
            "verdict": _BADGE_TO_VERDICT[badge],
            "reason": {"확인됨": "공식 출처에서 날짜·장소가 확인되고 최근 갱신",
                       "확인 필요": "; ".join(_uniq(caveats)) or "추가 확인 필요",
                       "보류": "출처 사이에 충돌이 있어 판단을 보류"}[badge],
            "confidence": _CONFIDENCE[badge] if badge != "확인 필요" or official_only else "low",
        }]
        for c in conflicts:
            label = _FIELD_LABEL[c.field]
            parts = " / ".join(f"{v['value']}({'·'.join(v['tiers'])})" for v in c.values)
            entries = []
            for idx, v in enumerate(c.values):
                # 채택된 값이 있으면 그 값만 support, 못 정했으면 첫 값을 기준으로 삼는다.
                keep = (v["value"] == c.chosen) if c.chosen is not None else idx == 0
                stance = "support" if keep else "contradict"
                for sid, tier, pub in zip(v["source_ids"], v["tiers"], v["published"], strict=True):
                    entries.append({"id": sid, "tier": tier, "date": pub, "stance": stance,
                                    "says": str(v["value"])})
            verdicts.append({
                "claim": f"{_title(primary)} 의 {label}: {parts}",
                "sources": entries,
                "verdict": "accepted" if c.chosen is not None else "disputed",
                "reason": c.reason,
                "confidence": "medium" if c.chosen is not None else "low",
            })
        decisions.append(EventDecision(
            tuple(m.id for m in ordered), primary, sources, badge, tuple(verdicts),
            _uniq(caveats), conflicts))

    decisions.sort(key=lambda d: (d.primary.start_date or "9999-99-99", d.primary.id))
    funnel: dict[str, int] = {"candidates": len(records),
                              "adopted": sum(1 for d in decisions if d.badge != "보류")}
    for rej in rejected:
        funnel[rej.reason] = funnel.get(rej.reason, 0) + 1
    return NowJudgement(tuple(decisions), tuple(rejected), tuple(blocked), funnel, tuple(problems))
