"""공개 행사 카탈로그의 데이터 모델.

`EventRecord`(수집 단계 레코드, contract/records.py)와 별개다. 여러 출처의 관찰값(`Observation`)을
하나의 행사(`EventEntry`)로 묶은 결과이며, 사용자에게 보이는 값은 전부 여기서 나온다.

원칙
- **모르는 값은 비워 두거나 ``"unknown"``.** 무료·예약 불필요·영어 지원·외국인 참여 가능을 추측하지 않는다.
- 3값 논리 ``Tri`` = ``"yes" | "no" | "unknown"``. 출처가 그렇게 적은 경우에만 yes/no 다.
- 영어 홈페이지가 있다는 사실(``site_english_page``)과 행사 진행 언어(``languages``·``english_guidance``)는 다른 필드다.
- 값마다 근거(``Evidence``: 출처 기관·원문 링크·근거 문구)를 연결한다. AI·OCR 추출값은 ``ai_extracted=True`` 로 표시한다.
- ``demo=True`` 는 데모·합성 자료다. 실제 행사처럼 보이게 하지 않는다.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from typing import Any, Literal, get_args, get_origin, get_type_hints

from domains.kcontext.contract.errors import ContractError
from domains.kcontext.contract.text import is_date, is_hhmm

__all__ = [
    "Eligibility",
    "EventEntry",
    "Evidence",
    "Language",
    "Observation",
    "Price",
    "Reservation",
    "Schedule",
    "Session",
    "Tri",
    "Venue",
    "entry_from_dict",
    "observation_from_dict",
]

Tri = Literal["yes", "no", "unknown"]
Lifecycle = Literal["scheduled", "ongoing", "ended", "cancelled", "postponed", "unknown"]
ReservationStatus = Literal["not_required", "open", "closed", "full", "unknown"]
Verification = Literal["verified", "needs_check", "conflict"]
EvidenceKind = Literal[
    "official_api", "official_site", "press", "sns", "report", "manual", "ai_extracted", "demo"
]
ForeignerStatus = Literal["allowed", "excluded", "unknown"]
DistrictBasis = Literal["source_gu", "address", "coords", "unknown"]
PriceKind = Literal["free", "paid", "unknown"]

TRI = ("yes", "no", "unknown")
LIFECYCLE = ("scheduled", "ongoing", "ended", "cancelled", "postponed", "unknown")
RESERVATION_STATUS = ("not_required", "open", "closed", "full", "unknown")
VERIFICATION = ("verified", "needs_check", "conflict")
EVIDENCE_KINDS = (
    "official_api", "official_site", "press", "sns", "report", "manual", "ai_extracted", "demo",
)
FOREIGNER = ("allowed", "excluded", "unknown")
DISTRICT_BASIS = ("source_gu", "address", "coords", "unknown")
PRICE_KINDS = ("free", "paid", "unknown")
PLACEHOLDER = "확인 필요"


@dataclass(frozen=True)
class Evidence:
    """값 하나의 근거. ``origin`` 이 같은 근거끼리는 독립 출처로 세지 않는다(재배포·같은 원천)."""

    source_id: str  # 예: "seoul_openapi"
    source_name: str  # 출처 기관 이름
    kind: EvidenceKind
    url: str  # 원문 링크(없으면 "")
    quote: str  # 근거 문구(원문에 있는 그대로)
    origin: str  # 원천 식별자. 재배포는 원천을 따라간다(예: "culture.seoul.go.kr#158770")
    collected_at: str  # YYYY-MM-DD
    published_at: str | None = None  # 원문 게시·수정 시각(원문이 준 만큼)
    ai_extracted: bool = False
    location: str | None = None  # 이미지·PDF·첨부의 원문 위치("첨부 2쪽 표 1")


@dataclass(frozen=True)
class Venue:
    name: str = ""
    address: str = ""
    lat: float | None = None
    lng: float | None = None
    district: str = ""  # 행정구역(자치구). 개최 장소 기준이다.
    district_basis: DistrictBasis = "unknown"
    in_target: Tri = "unknown"  # 대상 지역(설정 data/regions) 개최 여부 — 장소로만 정한다(주최기관 이름은 근거가 아니다)


@dataclass(frozen=True)
class Session:
    """회차. 시간은 Asia/Seoul 기준 ``HH:MM``."""

    date: str
    start_time: str | None = None
    end_time: str | None = None
    venue_name: str = ""
    in_target: Tri = "unknown"  # 장소가 여러 곳이면 대상 지역에서 열리는 회차를 구분한다
    note: str = ""


@dataclass(frozen=True)
class Schedule:
    start_date: str | None = None
    end_date: str | None = None
    sessions: tuple[Session, ...] = ()  # 회차가 확인된 경우만. 비어 있으면 "회차 확인 필요"
    weekly_closed_days: tuple[int, ...] = ()  # 월=0 … 일=6 (정기 휴무)
    closed_dates: tuple[str, ...] = ()  # 임시 휴무일
    holiday_rule: str = ""  # "월요일이 공휴일이면 정상 운영" 같은 원문 규칙
    entry_cutoff: str = ""  # 입장 마감(원문)
    hours_text: str = ""  # 운영 시간 원문
    timezone: str = "Asia/Seoul"


@dataclass(frozen=True)
class Price:
    kind: PriceKind = "unknown"  # 출처가 무료/유료라고 적은 경우만
    text: str = ""  # 요금 원문


@dataclass(frozen=True)
class Reservation:
    required: Tri = "unknown"
    link: str = ""
    deadline: str | None = None  # YYYY-MM-DD 또는 YYYY-MM-DDTHH:MM
    status: ReservationStatus = "unknown"
    note: str = ""


@dataclass(frozen=True)
class Eligibility:
    audience: str = ""  # 이용대상 원문
    restrictions: tuple[dict, ...] = ()  # [{"kind": "resident"|"age"|"other", "text", "reason"}]
    resident_only: Tri = "unknown"
    age_limit: str = ""
    foreigner: ForeignerStatus = "unknown"  # 외국인 참여 조건 — 출처가 적은 경우만 allowed/excluded
    stated_open: Tri = "unknown"  # 출처가 "누구나·제한 없음" 이라고 적은 경우만 yes


@dataclass(frozen=True)
class Language:
    languages: tuple[str, ...] = ()  # 행사 진행 언어(출처가 적은 것만)
    english_guidance: Tri = "unknown"  # 영어 안내(현장·자료)
    english_subtitles: Tri = "unknown"  # 영어 자막·통역
    site_english_page: Tri = "unknown"  # 출처 홈페이지의 영어 페이지 — 행사 언어와 다르다


@dataclass(frozen=True)
class Observation:
    """출처 하나가 행사 하나에 대해 말한 것. 묶기 전 단위이며 값은 아직 정리되지 않았다."""

    obs_id: str
    title: str
    title_en: str = ""
    description: str = ""
    event_type: str = ""
    organizer: str = ""
    operator: str = ""
    venue: Venue = field(default_factory=Venue)
    schedule: Schedule = field(default_factory=Schedule)
    price: Price = field(default_factory=Price)
    reservation: Reservation = field(default_factory=Reservation)
    eligibility: Eligibility = field(default_factory=Eligibility)
    language: Language = field(default_factory=Language)
    lifecycle: Lifecycle = "unknown"  # 출처가 취소·연기를 알린 경우만 cancelled/postponed
    external_ids: tuple[str, ...] = ()  # 주최 측·원천이 준 식별자("seoul_cult:158770")
    evidence: Evidence | None = None
    published_at: str | None = None
    modified_at: str | None = None
    demo: bool = False


@dataclass(frozen=True)
class EventEntry:
    id: str
    title: str
    title_en: str = ""
    description: str = ""
    event_type: str = ""
    organizer: str = ""
    operator: str = ""
    venue: Venue = field(default_factory=Venue)
    schedule: Schedule = field(default_factory=Schedule)
    price: Price = field(default_factory=Price)
    reservation: Reservation = field(default_factory=Reservation)
    eligibility: Eligibility = field(default_factory=Eligibility)
    language: Language = field(default_factory=Language)
    external_ids: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    published_at: str | None = None
    modified_at: str | None = None
    collected_at: str = ""
    last_verified_at: str | None = None  # 출처를 마지막으로 다시 확인한 시각(수집 성공 시각)
    lifecycle: Lifecycle = "unknown"
    reservation_status: ReservationStatus = "unknown"
    verification: Verification = "needs_check"
    needs_check: tuple[str, ...] = ()  # 확인이 필요한 항목 이름들
    conflicts: tuple[dict, ...] = ()  # [{"field", "values":[{"value","source_id"}], "resolved"}]
    independent_sources: int = 0
    demo: bool = False

    def to_dict(self) -> dict[str, Any]:
        return _plain(self)


def _plain(v: Any) -> Any:
    if dataclasses.is_dataclass(v) and not isinstance(v, type):
        return {f.name: _plain(getattr(v, f.name)) for f in fields(v)}
    if isinstance(v, Mapping):
        return {k: _plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    return v


def _load(cls: type, d: object, at: str, problems: list[str]) -> Any:
    """strict 로더: 모르는 키·잘못된 형식은 problems 에 쌓는다."""
    if not isinstance(d, Mapping):
        problems.append(f"{at}: 객체가 아님")
        return None
    hints = get_type_hints(cls)
    names = {f.name for f in fields(cls)}
    problems.extend(f"{at}.{k}: 모르는 키" for k in d if k not in names)
    kwargs: dict[str, Any] = {}
    for f in fields(cls):
        if f.name not in d:
            continue
        kwargs[f.name] = _coerce(hints[f.name], d[f.name], f"{at}.{f.name}", problems)
    return kwargs


def _coerce(tp: Any, v: Any, at: str, problems: list[str]) -> Any:
    origin = get_origin(tp)
    if origin is Literal:
        if v not in get_args(tp):
            problems.append(f"{at}: {'|'.join(map(str, get_args(tp)))} 중 하나")
        return v
    if dataclasses.is_dataclass(tp):
        kw = _load(tp, v, at, problems)
        return tp(**kw) if kw is not None and not problems else None
    if origin is tuple:
        if not isinstance(v, (list, tuple)):
            problems.append(f"{at}: 배열")
            return ()
        (inner, *_) = get_args(tp)
        return tuple(_coerce(inner, x, f"{at}[{i}]", problems) for i, x in enumerate(v))
    if origin is not None and type(None) in get_args(tp):  # Optional[...]
        if v is None:
            return None
        inner = next(a for a in get_args(tp) if a is not type(None))
        return _coerce(inner, v, at, problems)
    if tp is Any or tp is dict:
        return v
    if tp is float:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            problems.append(f"{at}: 숫자")
        return v
    if tp is int:
        if isinstance(v, bool) or not isinstance(v, int):
            problems.append(f"{at}: 정수")
        return v
    if tp is str:
        if not isinstance(v, str):
            problems.append(f"{at}: 문자열")
        return v
    if tp is bool:
        if not isinstance(v, bool):
            problems.append(f"{at}: boolean")
        return v
    return v


def entry_from_dict(d: Mapping) -> EventEntry:
    """저장된 JSON → ``EventEntry``. 형식이 틀리면 ``ContractError``."""
    problems: list[str] = []
    kw = _load(EventEntry, d, "entry", problems)
    if kw is not None:
        _check_entry(kw, problems)
    if problems or kw is None:
        raise ContractError(problems or ["entry: 읽을 수 없다"])
    return EventEntry(**kw)


def _check_entry(kw: dict, problems: list[str]) -> None:
    for k in ("id", "title"):
        if not isinstance(kw.get(k), str) or not kw[k]:
            problems.append(f"entry.{k}: 비어 있지 않은 문자열 필요")
    sch = kw.get("schedule")
    if isinstance(sch, Schedule):
        for k in ("start_date", "end_date"):
            v = getattr(sch, k)
            if v is not None and not is_date(v):
                problems.append(f"entry.schedule.{k}: YYYY-MM-DD 또는 null")
        if sch.start_date and sch.end_date and sch.start_date > sch.end_date:
            problems.append("entry.schedule: 시작일이 종료일보다 늦음")
        for i, s in enumerate(sch.sessions):
            if not is_date(s.date):
                problems.append(f"entry.schedule.sessions[{i}].date")
            for k in ("start_time", "end_time"):
                v = getattr(s, k)
                if v is not None and not is_hhmm(v):
                    problems.append(f"entry.schedule.sessions[{i}].{k}: HH:MM 또는 null")
        if any(not isinstance(x, int) or not 0 <= x <= 6 for x in sch.weekly_closed_days):
            problems.append("entry.schedule.weekly_closed_days: 0~6")
        if any(not is_date(x) for x in sch.closed_dates):
            problems.append("entry.schedule.closed_dates: YYYY-MM-DD")
        if sch.timezone != "Asia/Seoul":
            problems.append("entry.schedule.timezone: Asia/Seoul")
    ven = kw.get("venue")
    if isinstance(ven, Venue) and ((ven.lat is None) != (ven.lng is None)):
        problems.append("entry.venue: lat·lng 는 둘 다 있거나 둘 다 null")
    if kw.get("independent_sources", 0) < 0:
        problems.append("entry.independent_sources: 0 이상")


def observation_from_dict(d: Mapping) -> Observation:
    """저장된 JSON → ``Observation``. 형식이 틀리면 ``ContractError``."""
    problems: list[str] = []
    kw = _load(Observation, d, "observation", problems)
    if kw is not None and (not isinstance(kw.get("obs_id"), str) or not kw.get("obs_id")):
        problems.append("observation.obs_id: 비어 있지 않은 문자열 필요")
    if problems or kw is None:
        raise ContractError(problems or ["observation: 읽을 수 없다"])
    return Observation(**kw)
