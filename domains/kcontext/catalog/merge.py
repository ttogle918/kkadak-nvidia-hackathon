"""관찰값(출처별 보고) → 행사 항목. 묶기·값 고르기·충돌·검증 상태.

묶기 규칙
- 같은 외부 식별자(주최 측·원천이 준 id)를 공유하면 같은 행사다.
- 식별자가 없으면 **장소 + 기간 + (주최 또는 거의 같은 행사명)** 을 함께 본다. 행사명만 같다고 합치지 않는다.
  장소·날짜를 모르면 합치지 않는다. 같은 이름·같은 장소라도 기간이 겹치지 않으면 다른 회차로 남긴다.
- 데모(합성) 관찰은 실제 관찰과 합치지 않는다.
- 같은 원천(`Evidence.origin`)에서 재배포된 자료는 독립 출처로 세지 않는다.

값 고르기: 출처 우선순위(주최·운영 측 홈페이지 > 공식 API > 보도자료 > SNS > 제보·수기 > AI 추출) → 더 최근 수정.
충돌: 서로 다른 원천이 다른 값을 말하면 기록한다. 우선순위나 시각으로 한쪽이 확실히 앞서면 해결, 아니면 미해결 —
미해결 충돌이 있으면 검증 상태는 ``conflict`` 이고 값은 "확인 필요"로 보인다.
"""

from __future__ import annotations

import dataclasses
import hashlib
from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime
from difflib import SequenceMatcher

from .model import (
    Eligibility,
    EventEntry,
    Evidence,
    Language,
    Observation,
    Price,
    Reservation,
    Schedule,
    Session,
    Venue,
)
from .rules import date_range_days, event_lifecycle, reservation_status, squash

__all__ = ["build_entries", "evidence_rank", "same_event"]

_RANK = {
    "official_site": 0, "official_api": 1, "press": 2, "sns": 3,
    "report": 4, "manual": 4, "ai_extracted": 5, "demo": 9,
}
_OFFICIAL = ("official_site", "official_api")
TITLE_SIMILARITY = 0.8  # [제안, 시험 후 조정] 장소·기간이 맞은 뒤에만 쓰는 보조 조건
NEAR_M = 150


def evidence_rank(o: Observation) -> int:
    return _RANK.get(o.evidence.kind, 8) if o.evidence else 8


def _stamp(o: Observation) -> str:
    return o.modified_at or o.published_at or (o.evidence.collected_at if o.evidence else "") or ""


def _order_key(o: Observation) -> tuple:
    # 우선순위 → 더 최근 수정 → 식별자(안정)
    return (evidence_rank(o), _neg(_stamp(o)), o.obs_id)


def _neg(s: str) -> tuple:
    return tuple(-ord(c) for c in s)


# ---- 같은 행사인가 --------------------------------------------------------------------------


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    import math

    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


def _same_venue(a: Venue, b: Venue) -> bool:
    na, nb = squash(a.name), squash(b.name)
    if na and nb and (na == nb or (min(len(na), len(nb)) >= 4 and (na in nb or nb in na))):
        return True
    if a.lat is not None and b.lat is not None and a.lng is not None and b.lng is not None:
        return _haversine_m((a.lat, a.lng), (b.lat, b.lng)) <= NEAR_M
    aa, ab = squash(a.address), squash(b.address)
    return bool(aa and ab and aa == ab)


def _days(s: Schedule) -> set[date]:
    days = set(date_range_days(s.start_date, s.end_date))
    days |= {date.fromisoformat(x.date) for x in s.sessions}
    return days


def same_event(a: Observation, b: Observation) -> bool:
    if a.demo != b.demo:
        return False
    if set(a.external_ids) & set(b.external_ids):
        return True
    if not _same_venue(a.venue, b.venue):
        return False
    da, db = _days(a.schedule), _days(b.schedule)
    if not da or not db or not (da & db):
        return False
    org_a, org_b = squash(a.organizer), squash(b.organizer)
    if org_a and org_a == org_b:
        return True
    ta, tb = squash(a.title), squash(b.title)
    return bool(ta and tb and SequenceMatcher(None, ta, tb).ratio() >= TITLE_SIMILARITY)


def _group(obs: Sequence[Observation]) -> list[list[Observation]]:
    groups: list[list[Observation]] = []
    for o in sorted(obs, key=lambda x: x.obs_id):
        for g in groups:
            if all(same_event(o, x) for x in g):  # 모든 쌍이 같은 행사일 때만(과병합 방지)
                g.append(o)
                break
        else:
            groups.append([o])
    return groups


# ---- 값 고르기 ------------------------------------------------------------------------------


def _first(ordered: Sequence[Observation], get: Callable[[Observation], object]):
    for o in ordered:
        v = get(o)
        if v not in (None, "", (), [], "unknown"):
            return v
    return None


def _pick(ordered, get, default):
    v = _first(ordered, get)
    return default if v is None else v


def _conflict(
    ordered: Sequence[Observation], field: str, get: Callable[[Observation], object]
) -> tuple[dict | None, object]:
    """서로 다른 원천의 값이 다르면 충돌. (충돌 기록, 채택값)."""
    cands = [(o, get(o)) for o in ordered if get(o) not in (None, "", (), [], "unknown")]
    if not cands:
        return None, None
    by_origin: dict[str, tuple[Observation, object]] = {}
    for o, v in cands:  # 원천별 대표(가장 앞선 관찰)
        by_origin.setdefault(o.evidence.origin if o.evidence else o.obs_id, (o, v))
    values = {repr(v) for _, v in by_origin.values()}
    chosen = cands[0][1]
    if len(values) < 2:
        return None, chosen
    reps = sorted(by_origin.values(), key=lambda ov: _order_key(ov[0]))
    top, second = reps[0], reps[1]
    resolved = (
        evidence_rank(top[0]) < evidence_rank(second[0])
        or (evidence_rank(top[0]) == evidence_rank(second[0])
            and _stamp(top[0]) > _stamp(second[0]) and _stamp(second[0]) != "")
    ) and evidence_rank(top[0]) <= _RANK["press"]
    rec = {
        "field": field,
        "values": [{"value": v if isinstance(v, (str, int, float, bool)) else repr(v),
                    "source_id": o.evidence.source_id if o.evidence else "",
                    "kind": o.evidence.kind if o.evidence else ""} for o, v in reps],
        "resolved": bool(resolved),
        "chosen": top[1] if isinstance(top[1], (str, int, float, bool)) else repr(top[1]),
    }
    return rec, top[1]


def _sessions(ordered: Sequence[Observation]) -> tuple[Session, ...]:
    for o in ordered:
        if o.schedule.sessions:
            return tuple(sorted(o.schedule.sessions, key=lambda s: (s.date, s.start_time or "")))
    return ()


def _stable_id(obs: Sequence[Observation], prior: Mapping[str, str] | None) -> str:
    keys = sorted({k for o in obs for k in (o.obs_id, *o.external_ids)})
    if prior:
        for k in keys:
            if k in prior:
                return prior[k]
    seed = "|".join(keys[:1])
    return "ev:" + hashlib.sha1(seed.encode()).hexdigest()[:12]


def _evidence(obs: Sequence[Observation]) -> tuple[Evidence, ...]:
    seen: dict[tuple, Evidence] = {}
    for o in sorted(obs, key=_order_key):
        if o.evidence is not None:
            seen.setdefault((o.evidence.source_id, o.evidence.url, o.evidence.quote), o.evidence)
    return tuple(seen.values())


def _entry(group: Sequence[Observation], *, now: datetime, verified_at: str,
           prior: Mapping[str, str] | None, seen_at: Mapping[str, str] | None = None) -> EventEntry:
    ordered = sorted(group, key=_order_key)
    conflicts: list[dict] = []
    needs: list[str] = []

    def chosen(field: str, get: Callable[[Observation], object]):
        rec, val = _conflict(ordered, field, get)
        if rec:
            conflicts.append(rec)
        return val

    start = chosen("start_date", lambda o: o.schedule.start_date)
    end = chosen("end_date", lambda o: o.schedule.end_date)
    venue_name = chosen("venue_name", lambda o: squash(o.venue.name) and o.venue.name)
    price_kind = chosen("price_kind", lambda o: o.price.kind)
    res_required = chosen("reservation_required", lambda o: o.reservation.required)
    # 개최 상태: 취소·연기는 공식(주최·공식 API·보도) 출처만 확정한다. 그 밖의 출처는 충돌로만 남긴다.
    reported = [o for o in ordered if o.lifecycle in ("cancelled", "postponed")]
    life = "unknown"
    if reported:
        official_report = [o for o in reported if evidence_rank(o) <= _RANK["press"]]
        newest_non_cancel = max((_stamp(o) for o in ordered if o.lifecycle == "unknown"), default="")
        if official_report and _stamp(official_report[0]) >= newest_non_cancel:
            life = official_report[0].lifecycle
        else:
            conflicts.append({
                "field": "lifecycle",
                "values": [{"value": o.lifecycle, "source_id": o.evidence.source_id if o.evidence else "",
                            "kind": o.evidence.kind if o.evidence else ""} for o in reported],
                "resolved": False, "chosen": "unknown"})

    venue = _pick(ordered, lambda o: o.venue if (o.venue.name or o.venue.address) else None, Venue())
    if venue_name and venue.name != venue_name:
        venue = next((o.venue for o in ordered if o.venue.name == venue_name), venue)
    schedule = Schedule(
        start_date=start, end_date=end, sessions=_sessions(ordered),
        weekly_closed_days=tuple(_pick(ordered, lambda o: o.schedule.weekly_closed_days, ())),
        closed_dates=tuple(sorted({d for o in ordered for d in o.schedule.closed_dates})),
        holiday_rule=_pick(ordered, lambda o: o.schedule.holiday_rule, ""),
        entry_cutoff=_pick(ordered, lambda o: o.schedule.entry_cutoff, ""),
        hours_text=_pick(ordered, lambda o: o.schedule.hours_text, ""),
    )
    price_text = _pick(ordered, lambda o: o.price.text if o.price.kind == price_kind or not price_kind
                       else None, "")
    price = Price(kind=price_kind or "unknown", text=price_text)
    res_src = next((o.reservation for o in ordered if o.reservation.required == res_required
                    and res_required), None)
    reservation = Reservation(
        required=res_required or "unknown",
        link=_pick(ordered, lambda o: o.reservation.link, ""),
        deadline=_pick(ordered, lambda o: o.reservation.deadline, None),
        status=(res_src.status if res_src else _pick(ordered, lambda o: o.reservation.status, "unknown")),
        note=_pick(ordered, lambda o: o.reservation.note, ""),
    )
    elig_src = next((o.eligibility for o in ordered if o.eligibility.audience
                     or o.eligibility.restrictions), Eligibility())
    restrictions = tuple({r["text"] + r["kind"]: r for o in ordered
                          for r in o.eligibility.restrictions}.values())
    eligibility = dataclasses.replace(elig_src, restrictions=restrictions)
    lang = Language(
        languages=tuple(dict.fromkeys(x for o in ordered for x in o.language.languages)),
        english_guidance=_pick(ordered, lambda o: o.language.english_guidance, "unknown"),
        english_subtitles=_pick(ordered, lambda o: o.language.english_subtitles, "unknown"),
        site_english_page=_pick(ordered, lambda o: o.language.site_english_page, "unknown"),
    )
    evid = _evidence(group)
    entry = EventEntry(
        id=_stable_id(group, prior),
        title=_pick(ordered, lambda o: o.title, ""),
        title_en=_pick(ordered, lambda o: o.title_en, ""),
        description=_pick(ordered, lambda o: o.description, ""),
        event_type=_pick(ordered, lambda o: o.event_type, ""),
        organizer=_pick(ordered, lambda o: o.organizer, ""),
        operator=_pick(ordered, lambda o: o.operator, ""),
        venue=venue, schedule=schedule, price=price, reservation=reservation,
        eligibility=eligibility, language=lang,
        external_ids=tuple(sorted({k for o in group for k in (o.obs_id, *o.external_ids)})),
        evidence=evid,
        published_at=max((o.published_at for o in group if o.published_at), default=None),
        modified_at=max((o.modified_at for o in group if o.modified_at), default=None),
        collected_at=max((e.collected_at for e in evid), default=""),
        last_verified_at=max((seen_at[o.obs_id] for o in group if seen_at and o.obs_id in seen_at),
                             default=verified_at),
        lifecycle=life,
        independent_sources=len({e.origin for e in evid}),
        demo=any(o.demo for o in group),
    )
    # 확인이 필요한 항목(값을 모를 때). 알려진 값만 보여 주고 나머지는 "확인 필요"로 둔다.
    if not (entry.schedule.start_date or entry.schedule.end_date or entry.schedule.sessions):
        needs.append("dates")
    if not entry.schedule.sessions:
        needs.append("sessions")
    if not entry.schedule.hours_text and not entry.schedule.sessions:
        needs.append("hours")
    if entry.price.kind == "unknown":
        needs.append("price")
    if entry.reservation.required == "unknown":
        needs.append("reservation")
    if not (entry.eligibility.audience or entry.eligibility.restrictions):
        needs.append("eligibility")
    elif entry.eligibility.foreigner == "unknown":
        needs.append("foreigner")
    if not entry.language.languages and entry.language.english_guidance == "unknown":
        needs.append("language")
    if not (entry.venue.name or entry.venue.address):
        needs.append("venue")
    if entry.venue.in_target == "unknown":
        needs.append("region")
    unresolved = [c for c in conflicts if not c["resolved"]]
    official = any(e.kind in _OFFICIAL for e in entry.evidence)
    verified = (official and entry.venue.in_target == "yes" and bool(entry.schedule.start_date)
                and not unresolved and not entry.demo)
    entry = dataclasses.replace(
        entry, conflicts=tuple(conflicts), needs_check=tuple(needs),
        verification="conflict" if unresolved else ("verified" if verified else "needs_check"),
    )
    return dataclasses.replace(
        entry, lifecycle=event_lifecycle(entry, now),
        reservation_status=reservation_status(entry.reservation, now),
    )


def build_entries(
    observations: Sequence[Observation], *, now: datetime, verified_at: str | None = None,
    prior: Mapping[str, str] | None = None, seen_at: Mapping[str, str] | None = None,
) -> list[EventEntry]:
    """관찰값 전체 → 행사 항목(시작일·id 순).

    ``prior``: 이전 실행의 관찰·외부 id → 항목 id (id 유지용). ``seen_at``: 관찰 id → 마지막으로 출처에서
    다시 확인한 시각 — 항목의 마지막 검증 시각은 그 묶음의 가장 최근 값이다(없으면 ``verified_at``).
    """
    vat = verified_at or now.strftime("%Y-%m-%dT%H:%M")
    out = [_entry(g, now=now, verified_at=vat, prior=prior, seen_at=seen_at) for g in _group(observations)]
    out.sort(key=lambda e: (e.schedule.start_date or "9999-99-99", e.id))
    return out
