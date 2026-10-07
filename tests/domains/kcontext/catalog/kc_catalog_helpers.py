"""카탈로그 테스트 공용 도우미. 값은 전부 합성(○○)이다."""

from __future__ import annotations

from datetime import datetime

from domains.kcontext.catalog.model import (
    Eligibility,
    Evidence,
    Observation,
    Price,
    Reservation,
    Schedule,
    Session,
    Venue,
)
from domains.kcontext.catalog.rules import KST
from domains.kcontext.regions import load_regions

REGION = load_regions()["jung"]
NOW = datetime(2026, 10, 7, 12, 0, tzinfo=KST)


def ev(source_id="seoul_openapi", kind="official_api", origin="o1", quote="인용", url="https://example.invalid/x",
       collected="2026-10-07", published=None, ai=False) -> Evidence:
    return Evidence(source_id=source_id, source_name=f"○○ {source_id}", kind=kind, url=url, quote=quote,
                    origin=origin, collected_at=collected, published_at=published, ai_extracted=ai)


def obs(obs_id="s:1", title="○○ 가을 음악회", venue_name="○○ 홀", in_target="yes", start="2026-10-16",
        end="2026-10-16", sessions=(), organizer="", external_ids=(), kind="official_api", origin=None,
        lifecycle="unknown", modified=None, published=None, price_kind="unknown", reservation=None,
        eligibility=None, demo=False, lat=None, lng=None, **kw) -> Observation:
    return Observation(
        obs_id=obs_id, title=title, organizer=organizer,
        venue=Venue(name=venue_name, address="", lat=lat, lng=lng, district="중구" if in_target == "yes" else "",
                    district_basis="source_gu" if in_target != "unknown" else "unknown", in_target=in_target),
        schedule=Schedule(start_date=start, end_date=end, sessions=tuple(sessions)),
        price=Price(kind=price_kind), reservation=reservation or Reservation(),
        eligibility=eligibility or Eligibility(), external_ids=tuple(external_ids), lifecycle=lifecycle,
        evidence=ev(source_id=kw.get("source_id", "seoul_openapi"), kind=kind, origin=origin or obs_id,
                    published=published), modified_at=modified, published_at=published, demo=demo)


def session(date="2026-10-16", start="19:30", end="21:00", venue="○○ 홀", in_target="yes"):
    return Session(date=date, start_time=start, end_time=end, venue_name=venue, in_target=in_target)
