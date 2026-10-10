"""검색 수집 레코드(``EventRecord``, ``fetched_from="web"``, D12) → 카탈로그 관찰값.

수집 단계가 이미 quote 검증을 한 값만 온다(날짜·장소는 quote 에서 확인된 값, 아니면 None·빈 문자열).
여기서는 값을 더하지 않고, 근거 등급을 낮게(``ai_extracted``) 매긴다 — merge 가 이 등급의 값으로 예약·언어·
참여조건을 채우지 않고, 독립 출처로 세지 않으며, 공식 출처와 값이 다르면 공식 쪽을 쓴다(충돌은 기록).
공식 출처 없이 이 출처만 있는 행사는 ``verification="needs_check"`` 로 남고, 대상 지역은 **개최 장소**로만
정한다(D13 ②) — 구청 사이트에 올라온 글이라는 사실은 근거가 아니므로 장소가 서울 ○○구로 확인되지 않으면 ``unknown``.
합성 fixture 레코드(``synthetic``)는 넣지 않는다.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from domains.kcontext.contract.records import EventRecord
from domains.kcontext.contract.text import pick
from domains.kcontext.ingest.events.store import read_jsonl
from domains.kcontext.paths import var_dir
from domains.kcontext.places import load_places
from domains.kcontext.regions import Region

from .model import Evidence, Observation, Schedule
from .rules import classify_venue, norm_text
from .target import region_ids

__all__ = ["SOURCE_ID", "default_events_file", "make_web_fetcher", "observation_from_record",
           "observations_from_records"]

SOURCE_ID = "junggu_site"
_LABEL = "(검색 수집)"
_LABEL_UNCONFIRMED = "(검색 수집 · 미확인)"


def default_events_file(web_source_id: str | None = None) -> Path:
    """수집기 출력 위치. 출처 id 가 있으면 ``web.<id>.jsonl``, 그 파일이 없고 예전 ``web.jsonl`` 이 있으면 그것(호환)."""
    base = var_dir() / "data" / "events"
    if web_source_id is None:
        return base / "web.jsonl"
    own = base / f"web.{web_source_id}.jsonl"
    legacy = base / "web.jsonl"
    return legacy if (not own.is_file() and legacy.is_file()) else own


def observation_from_record(r: EventRecord, *, region: Region, places=None,
                            source_id: str = SOURCE_ID) -> Observation | None:
    if r.fetched_from != "web" or r.synthetic:
        return None
    title = norm_text(pick(r.title, "ko") or "")
    if not title:
        return None
    place = norm_text(r.place_name)
    address = place if place.startswith(("서울", "대한민국")) else ""
    venue = classify_venue(name=place, address=address, region=region)
    hit = places.lookup(place) if (places is not None and place) else None
    if hit is not None:  # 검증된 사전의 좌표만(없으면 비운다). 대상 지역 여부는 바꾸지 않는다
        venue = type(venue)(**{**venue.__dict__, "lat": hit.lat, "lng": hit.lng})
    s = r.source
    name = s.name.replace(_LABEL, _LABEL_UNCONFIRMED) if _LABEL in s.name else f"{s.name} {_LABEL_UNCONFIRMED}"
    return Observation(
        obs_id=r.id,
        title=title,
        description=norm_text(r.description or ""),
        event_type=r.category,
        venue=venue,
        schedule=Schedule(start_date=r.start_date, end_date=r.end_date),
        evidence=Evidence(
            source_id=source_id, source_name=name, kind="ai_extracted", url=s.url, quote=s.quote,
            origin=s.id, collected_at=s.collected_at, published_at=s.published, ai_extracted=True,
            location=s.locator,  # 게시일·수집일과 "날짜 게시일 기준 추정" 표시가 여기로 나간다
        ),
        published_at=s.published,
    )


def observations_from_records(records: Iterable[EventRecord], *, region: Region,
                              source_id: str = SOURCE_ID,
                              only_region: str | None = None) -> list[Observation]:
    """``only_region`` 이 있으면 그 지역 레코드만(출처 하나가 지역 하나를 맡을 때)."""
    try:
        places = load_places()
    except Exception:  # noqa: BLE001 - 좌표 사전이 없거나 깨져도 좌표만 비운다
        places = None
    out = []
    for r in records:
        if r.region not in region_ids(region):
            continue
        if only_region is not None and r.region != only_region:
            continue
        o = observation_from_record(r, region=region, places=places, source_id=source_id)
        if o is not None:
            out.append(o)
    return out


def make_web_fetcher(path: Path | None, *, region: Region, source_id: str = SOURCE_ID,
                     only_region: str | None = None) -> Callable[[], list[Observation]]:
    """수집기가 쓴 JSONL 을 읽는 수집 함수. 계약에 어긋나는 줄이 있으면 예외 → 실행 기록에 실패로 남고 기존 데이터는 그대로."""
    p = Path(path) if path is not None else default_events_file()

    def fetch() -> list[Observation]:
        return observations_from_records(read_jsonl(p), region=region, source_id=source_id,
                                         only_region=only_region)

    return fetch
