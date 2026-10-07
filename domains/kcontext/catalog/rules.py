"""행사 사실을 판정하는 규칙. 날짜·시간 계산, 지역 판정, 참여조건 해석은 AI 가 아니라 이 코드가 한다.

모든 규칙은 보수적이다: 출처 문구에서 확인되지 않으면 ``"unknown"`` 이다.
지역 이름은 코드에 적지 않는다 — 대상 지역은 ``data/regions/*.json`` 의 ``Region`` 으로 받는다.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from domains.kcontext.regions import Region

from .model import (
    Eligibility,
    EventEntry,
    Lifecycle,
    Reservation,
    ReservationStatus,
    Schedule,
    Tri,
    Venue,
)

__all__ = [
    "KST",
    "classify_venue",
    "date_range_days",
    "event_lifecycle",
    "is_operating_day",
    "norm_text",
    "parse_eligibility",
    "reservation_status",
    "to_kst",
]

KST = ZoneInfo("Asia/Seoul")
_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[\W_]+")


def norm_text(s: str) -> str:
    """NFKC·공백 정리."""
    return _WS.sub(" ", unicodedata.normalize("NFKC", s or "")).strip()


def squash(s: str) -> str:
    """비교용: NFKC·공백·문장부호 제거·소문자."""
    return _PUNCT.sub("", unicodedata.normalize("NFKC", s or "")).casefold()


def to_kst(dt: datetime) -> datetime:
    """시간대 없는 값은 Asia/Seoul 로 본다."""
    return dt.replace(tzinfo=KST) if dt.tzinfo is None else dt.astimezone(KST)


# ---- 지역(개최 장소 기준) -------------------------------------------------------------------


def classify_venue(
    *,
    name: str = "",
    address: str = "",
    gu: str = "",
    lat: float | None = None,
    lng: float | None = None,
    region: Region,
    city_hint: str = "서울",
) -> Venue:
    """개최 장소로 대상 지역 여부를 정한다. 주최·운영기관 이름은 보지 않는다.

    근거 순서: ① 출처가 준 자치구 필드 ② 주소 안의 자치구 이름(``city_hint`` 도 있어야 한다 — 같은 이름의 구가
    다른 도시에도 있다) ③ 좌표가 지역 bbox 안인지(bbox 가 설정된 경우만). 어느 것도 없으면 ``unknown``.
    """
    base = {"name": name, "address": address, "lat": lat, "lng": lng}
    gu = norm_text(gu)
    addr = norm_text(address)
    addr_gu = _address_district(addr, city_hint)
    if gu:
        if addr_gu and addr_gu != gu:  # 출처의 자치구와 주소의 자치구가 다르면 어느 쪽도 믿지 않는다
            return Venue(**base)
        inside = gu in region.gu
        return Venue(**base, district=gu, district_basis="source_gu", in_target="yes" if inside else "no")
    if addr_gu:
        return Venue(**base, district=addr_gu, district_basis="address",
                     in_target="yes" if addr_gu in region.gu else "no")
    if lat is not None and lng is not None and region.bbox is not None:
        s, w, n, e = region.bbox
        inside = s <= lat <= n and w <= lng <= e
        return Venue(**base, district_basis="coords", in_target="yes" if inside else "no")
    return Venue(**base)


def _address_district(addr: str, city_hint: str) -> str:
    """주소가 ``city_hint``(예: 서울)로 시작할 때만, 그 뒤 첫 ``○○구`` 를 자치구로 본다. 아니면 빈 문자열."""
    m = re.match(rf"^(?:대한민국\s*)?{re.escape(city_hint)}(?:특별시|시)?(?![가-힣])", addr)
    if not m:
        return ""
    d = re.search(r"(?<![가-힣])([가-힣]{1,4}구)(?![가-힣])", addr[m.end():])
    return d.group(1) if d else ""


# ---- 참여조건 -------------------------------------------------------------------------------

_RESIDENT = re.compile(r"([가-힣]{1,4}(?:시민|구민|군민|도민))")
_RESIDENT2 = re.compile(r"([가-힣]{1,6})\s*(?:거주자?|거주민|주민)(?!\s*등록)")
_GENERIC_PREFIX = ("일반", "모든", "전체", "모두", "내외국인", "외국인")
_PERK = re.compile(r"우대|할인|가산|감면|무료|혜택")
_EXCLUSIVE = re.compile(r"^\s*(?:에게만|만|한정|전용|대상|에\s*한함|에\s*한해)")
_AGE = re.compile(
    r"(?:만\s*)?(\d{1,2})\s*세\s*(이상|이하|미만|초과)|(\d{1,3})\s*개월\s*(이상|이하|미만|초과)"
    r"|(영유아|유아|어린이|초등학생|중학생|고등학생|청소년|성인|어르신|노인)"
)
_MEMBER = re.compile(r"(회원|가입자|멤버십|동호회|재학생|재직자|학부모|수강생|참가팀)")
_OPEN = re.compile(r"누구나|전\s*연령|전체\s*관람가|제한\s*없음|연령\s*제한\s*없음|모든\s*시민|모두\s*참여")
_FOREIGN_OK = re.compile(
    r"외국인(?!등록)(?:\s*(?:관광객|방문객))?\s*(?:도\s*)?(?:참여|참가|관람|이용|입장)?\s*(?:가능|환영)"
    r"(?!\s*(?:여부|문의|확인|협의|한지|한\s*경우|시))"
)
_FOREIGN_NO = re.compile(r"외국인[^.,;\n]{0,8}(?:제외|불가|참여\s*불가|참가\s*불가)|내국인\s*(?:만|한정|전용)")


def _resident_hits(text: str) -> list[tuple[int, int, str]]:
    hits = []
    for rx in (_RESIDENT, _RESIDENT2):
        for m in rx.finditer(text):
            word = m.group(1)
            prefix = re.sub(r"(?:시민|구민|군민|도민)$", "", word) if rx is _RESIDENT else word
            if prefix in _GENERIC_PREFIX or (rx is _RESIDENT and not prefix):
                continue
            hits.append((m.start(), m.end(), m.group(0)))
    return hits


def parse_eligibility(audience: str, *, extra: str = "") -> Eligibility:
    """이용대상 문구 → 참여조건. 출처가 적은 것만 yes/no, 나머지는 unknown 이다.

    "누구나" 같은 명시가 있고 제한 문구가 없을 때만 ``stated_open="yes"``. 제한 문구(거주·연령·회원 등)가 하나라도
    있으면 열려 있다고 쓰지 않는다. 외국인 조건은 외국인을 명시한 문구가 있을 때만 allowed/excluded.
    거주민 우대·할인("○○구민 무료")은 제한이 아니라 혜택이다. 다만 "○○구민만"처럼 배타적이면 제한이다.
    """
    text = norm_text(f"{audience} {extra}")
    restrictions: list[dict] = []
    resident = "unknown"
    for start, end, word in _resident_hits(text):
        tail = text[end: end + 8]
        before = text[max(0, start - 8): start]
        if not _EXCLUSIVE.match(tail) and (_PERK.search(tail) or _PERK.search(before)):
            restrictions.append({"kind": "perk", "text": word, "reason": "거주민 우대·할인 — 참여 제한이 아님"})
            continue
        resident = "yes"
        restrictions.append({"kind": "resident", "text": word, "reason": f"거주 조건: {word}"})
    age_text = ""
    for m in _AGE.finditer(text):
        age_text = (age_text + " " + m.group(0)).strip()
        restrictions.append({"kind": "age", "text": m.group(0), "reason": f"연령 조건: {m.group(0)}"})
    for m in _MEMBER.finditer(text):
        restrictions.append({"kind": "other", "text": m.group(0), "reason": f"대상 조건: {m.group(0)}"})
    foreigner = "unknown"
    if _FOREIGN_NO.search(text):
        foreigner = "excluded"
        restrictions.append({"kind": "foreigner", "text": _FOREIGN_NO.search(text).group(0),
                             "reason": "외국인 참여 제한"})
    elif _FOREIGN_OK.search(text):
        foreigner = "allowed"
    hard = [r for r in restrictions if r["kind"] in ("resident", "age", "foreigner", "other")]
    stated_open = "yes" if _OPEN.search(text) and not hard else "unknown"
    return Eligibility(
        audience=norm_text(audience),
        restrictions=tuple(restrictions),
        resident_only=resident,
        age_limit=age_text,
        foreigner=foreigner,
        stated_open=stated_open,
    )


# ---- 날짜·운영일 ----------------------------------------------------------------------------


def date_range_days(start: str | None, end: str | None) -> list[date]:
    """시작~종료(포함). 하나라도 없으면 알려진 하루만, 둘 다 없으면 빈 목록."""
    if not start and not end:
        return []
    a = date.fromisoformat(start or end)  # type: ignore[arg-type]
    b = date.fromisoformat(end or start)  # type: ignore[arg-type]
    if b < a:
        return []
    return [a + timedelta(days=i) for i in range((b - a).days + 1)]


def is_operating_day(sched: Schedule, day: date) -> tuple[Tri, str]:
    """그날 운영하는지. 정기·임시 휴무를 반영한다. 회차가 있으면 회차가 있는 날만 yes.

    반환 ``(yes|no|unknown, 이유)``. 기간 안이지만 회차·운영 시간을 모르면 ``unknown`` 이다 — 열린다고 확정하지 않는다.
    """
    iso = day.isoformat()
    if sched.start_date and iso < sched.start_date:
        return "no", "시작 전"
    if sched.end_date and iso > sched.end_date:
        return "no", "종료 후"
    if not sched.start_date and not sched.end_date and not sched.sessions:
        return "unknown", "날짜 미확인"
    if iso in sched.closed_dates:
        return "no", "임시 휴무일"
    if day.weekday() in sched.weekly_closed_days:
        note = f" ({sched.holiday_rule})" if sched.holiday_rule else ""
        return "unknown" if sched.holiday_rule else "no", f"정기 휴무 요일{note}"
    if sched.sessions:
        return ("yes", "회차 있음") if any(s.date == iso for s in sched.sessions) else (
            "no", "이 날짜에 회차 없음")
    return "unknown", "기간 안 — 회차·운영 시간 확인 필요"


# ---- 상태 -----------------------------------------------------------------------------------


def event_lifecycle(entry: EventEntry, now: datetime) -> Lifecycle:
    """개최 상태. 취소·연기는 출처가 알린 값(``entry.lifecycle``)을 유지하고, 그 밖에는 날짜로만 정한다."""
    if entry.lifecycle in ("cancelled", "postponed"):
        return entry.lifecycle
    today = to_kst(now).date().isoformat()
    s, e = entry.schedule.start_date, entry.schedule.end_date
    sess = [x.date for x in entry.schedule.sessions]
    if not s and not e and not sess:
        return "unknown"
    first = min(x for x in (s, e, *sess) if x)
    if first > today:
        return "scheduled"
    last = max([e or "", *sess])
    if not last:  # 종료일·회차를 모르면 시작일이 지났다고 끝났다고 단정하지 않는다
        return "ongoing" if s == today else "unknown"
    return "ended" if last < today else "ongoing"


def reservation_status(res: Reservation, now: datetime) -> ReservationStatus:
    """예약 상태. 출처가 마감·정원을 알렸거나 신청 마감일이 지난 경우만 closed/full 이다."""
    if res.status in ("closed", "full"):
        return res.status
    if res.required == "no":
        return "not_required"
    if res.deadline:
        d = res.deadline
        now_k = to_kst(now)
        try:
            limit = datetime.fromisoformat(d if "T" in d else f"{d}T23:59")
        except ValueError:
            return "unknown"
        if to_kst(limit) < now_k:
            return "closed"
    if res.required == "yes":
        return "open" if res.status == "open" else "unknown"
    return "unknown"
