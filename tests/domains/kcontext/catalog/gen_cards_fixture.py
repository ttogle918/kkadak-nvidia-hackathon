"""화면 계약 검증용 `now` 카드 fixture 를 만든다(프론트 `node --test` 가 schema.js 로 검증한다).

    uv run python tests/domains/kcontext/catalog/gen_cards_fixture.py        # 파일을 다시 쓴다
테스트(`test_kc_catalog_cards.py::test_committed_fixture_is_current`)가 커밋된 파일과 같은지 확인한다. 값은 전부 합성(○○)이다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3]))
REPO = HERE.parents[3]
OUT = REPO / "frontend/k-context/tests/fixtures/now_cards.json"


def build() -> dict:
    from kc_catalog_helpers import NOW, obs, session

    from domains.kcontext.catalog.cards import build_now_cards
    from domains.kcontext.catalog.fit import fit_event
    from domains.kcontext.catalog.merge import build_entries
    from domains.kcontext.catalog.model import Reservation
    from domains.kcontext.catalog.query import search_events
    from domains.kcontext.catalog.routes import TableRouteProvider
    from domains.kcontext.catalog.rules import parse_eligibility

    a, v, b = (37.5650, 126.9900), (37.5700, 126.9950), (37.5750, 127.0000)
    open_all = parse_eligibility("누구나 외국인 참여 가능")
    confirmed = obs("s:1", title="○○ 저녁 공연", venue_name="○○ 홀", lat=v[0], lng=v[1], eligibility=open_all,
                    reservation=Reservation(required="no"), sessions=(session("2026-10-16", "19:00", "20:30"),))
    range_only = obs("s:2", title="△△ 상설 전시", venue_name="□□ 관", lat=37.58, lng=127.01, start="2026-10-14",
                     end="2026-10-20")
    searched = obs("w:1", title="◇◇ 검색 수집 행사", venue_name="◇◇ 공원", lat=37.59, lng=127.02, kind="sns",
                   source_id="web_search", start="2026-10-17", end="2026-10-17")
    ca = obs("s:3", title="☆☆ 충돌 행사", venue_name="☆☆ 홀", lat=37.60, lng=127.03, external_ids=("k",), origin="o1")
    cb = obs("s:4", title="☆☆ 충돌 행사", venue_name="☆☆ 홀", lat=37.60, lng=127.03, external_ids=("k",), origin="o2",
             start="2026-10-17", end="2026-10-17")
    trip = {"from": "2026-10-15", "to": "2026-10-18"}
    itin = [{"id": "낮", "title": "점심", "date": "2026-10-16", "start": "14:00", "end": "17:00", "lat": a[0], "lng": a[1]},
            {"id": "밤", "title": "호텔", "date": "2026-10-16", "start": "22:00", "end": "23:00", "lat": b[0], "lng": b[1]}]
    req = {"trip": trip, "itinerary": itin, "interests": ["공연"]}
    res = search_events(build_entries([confirmed, range_only, searched, ca, cb], now=NOW), req, now=NOW)
    prov = TableRouteProvider({(a, v): 10, (v, b): 12, (a, b): 15})
    res["suggestions"] = [s for e in res["events"] for s in fit_event(e, itin, prov)]
    return build_now_cards(res, req)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")
