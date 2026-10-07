from kc_catalog_helpers import NOW, obs, session

from domains.kcontext.catalog.merge import build_entries, same_event
from domains.kcontext.catalog.model import Eligibility, Observation, Reservation


def build(*o, **kw):
    return build_entries(list(o), now=NOW, **kw)


# ---- 같은 행사 묶기 ---------------------------------------------------------------------------
def test_same_external_id_merges_into_one_entry_with_both_sources():
    a = obs("seoul:1", external_ids=("seoul_cult:1",), origin="culture.seoul.go.kr#1")
    b = obs("hanok:9", external_ids=("seoul_cult:1",), kind="official_site", origin="hanokmaeul.co.kr#9",
            source_id="hanok")
    (e,) = build(a, b)
    assert e.independent_sources == 2 and len(e.evidence) == 2
    assert {"seoul:1", "hanok:9", "seoul_cult:1"} <= set(e.external_ids)


def test_same_title_alone_never_merges():
    a = obs("s:1", venue_name="○○ 홀", start="2026-10-16", end="2026-10-16")
    b = obs("s:2", venue_name="△△ 극장", start="2026-10-16", end="2026-10-16")  # 장소가 다르다
    assert not same_event(a, b)
    assert len(build(a, b)) == 2


def test_same_title_same_venue_but_different_dates_stay_separate_editions():
    a = obs("s:1", start="2026-10-16", end="2026-10-16")
    b = obs("s:2", start="2026-11-20", end="2026-11-20")
    entries = build(a, b)
    assert len(entries) == 2  # 서로 다른 회차는 유지


def test_unknown_venue_or_dates_do_not_merge():
    a = obs("s:1", venue_name="")
    b = obs("s:2", venue_name="")
    assert not same_event(a, b)
    c = obs("s:3", start=None, end=None)
    d = obs("s:4", start=None, end=None)
    assert not same_event(c, d)


def test_duplicate_posts_with_same_venue_dates_and_organizer_merge():
    a = obs("s:1", title="○○ 가을 음악회", organizer="○○문화재단")
    b = obs("s:2", title="2026 ○○ 가을음악회 안내", organizer="○○문화재단", origin="other")
    (e,) = build(a, b)
    assert len(e.external_ids) == 2


def test_similar_title_merges_only_with_same_venue_and_overlapping_dates():
    a = obs("s:1", title="○○ 가을 음악회")
    b = obs("s:2", title="○○ 가을 음악회 (앵콜)")
    c = obs("s:3", title="○○ 가을 음악회 (앵콜)", start="2026-12-01", end="2026-12-01")
    assert same_event(a, b) and not same_event(a, c)


def test_demo_observations_never_merge_with_real_ones():
    real = obs("s:1", external_ids=("x:1",))
    demo = obs("d:1", external_ids=("x:1",), demo=True)
    entries = build(real, demo)
    assert len(entries) == 2 and {e.demo for e in entries} == {True, False}


def test_complete_linkage_blocks_transitive_overmerge():
    a = obs("s:1", title="○○ 음악회", venue_name="○○ 홀", lat=37.5000, lng=127.0000)
    b = obs("s:2", title="○○ 음악회", venue_name="○○ 홀", lat=None, lng=None)
    c = obs("s:3", title="○○ 음악회", venue_name="○○ 홀 별관", lat=37.6, lng=127.1)
    entries = build(a, b, c)
    assert sum(len(e.external_ids) for e in entries) == 3 and len(entries) >= 1


def test_same_origin_republication_is_not_an_independent_source():
    a = obs("seoul:1", external_ids=("seoul_cult:1",), origin="culture.seoul.go.kr#1")
    b = obs("tour:7", external_ids=("seoul_cult:1",), origin="culture.seoul.go.kr#1", source_id="tourapi")
    (e,) = build(a, b)
    assert len(e.evidence) == 2 and e.independent_sources == 1


# ---- 값 고르기·충돌 ---------------------------------------------------------------------------
def test_operator_site_beats_api_and_newer_wins_within_rank():
    api = obs("s:1", external_ids=("k",), start="2026-10-16", end="2026-10-16", kind="official_api")
    site = obs("h:1", external_ids=("k",), start="2026-10-17", end="2026-10-17", kind="official_site",
               origin="hanok#1")
    (e,) = build(api, site)
    assert e.schedule.start_date == "2026-10-17"
    c = {x["field"]: x for x in e.conflicts}["start_date"]
    assert c["resolved"] is True and c["chosen"] == "2026-10-17"
    assert e.verification == "verified"


def test_same_rank_conflict_is_unresolved_until_one_is_newer():
    a = obs("s:1", external_ids=("k",), start="2026-10-16", end="2026-10-16", origin="o1")
    b = obs("s:2", external_ids=("k",), start="2026-10-17", end="2026-10-17", origin="o2")
    (e,) = build(a, b)
    assert e.verification == "conflict" and any(not c["resolved"] for c in e.conflicts)
    a2 = obs("s:1", external_ids=("k",), start="2026-10-16", end="2026-10-16", origin="o1", modified="2026-10-01")
    b2 = obs("s:2", external_ids=("k",), start="2026-10-17", end="2026-10-17", origin="o2", modified="2026-10-05")
    (e2,) = build(a2, b2)
    assert e2.schedule.start_date == "2026-10-17" and e2.verification == "verified"


def test_non_official_source_cannot_resolve_a_conflict():
    official = obs("s:1", external_ids=("k",), start="2026-10-16", end="2026-10-16", kind="official_api")
    report = obs("r:1", external_ids=("k",), start="2026-10-20", end="2026-10-20", kind="report",
                 origin="rep", modified="2026-10-06")
    (e,) = build(official, report)
    assert e.schedule.start_date == "2026-10-16"  # 공식 값 유지
    assert {c["field"] for c in e.conflicts} >= {"start_date"}


def test_cancellation_only_from_official_sources():
    base = obs("s:1", external_ids=("k",), kind="official_api", published="2026-10-01")
    cancel_official = obs("h:1", external_ids=("k",), kind="official_site", origin="h", lifecycle="cancelled",
                          published="2026-10-05")
    (e,) = build(base, cancel_official)
    assert e.lifecycle == "cancelled"
    rumor = obs("r:1", external_ids=("k",), kind="sns", origin="sns", lifecycle="cancelled",
                published="2026-10-06")
    (e2,) = build(base, rumor)
    assert e2.lifecycle != "cancelled"
    assert any(c["field"] == "lifecycle" and not c["resolved"] for c in e2.conflicts)
    assert e2.verification == "conflict"


def test_newer_non_cancel_notice_overrides_an_older_cancellation():
    cancel = obs("h:1", external_ids=("k",), kind="official_site", origin="h", lifecycle="cancelled",
                 published="2026-10-01")
    resume = obs("h:2", external_ids=("k",), kind="official_site", origin="h2", published="2026-10-05")
    (e,) = build(cancel, resume)
    assert e.lifecycle != "cancelled"


def test_closed_dates_are_unioned_conservatively():
    a = obs("s:1", external_ids=("k",))
    b = obs("s:2", external_ids=("k",), origin="o2")
    import dataclasses

    a = dataclasses.replace(a, schedule=dataclasses.replace(a.schedule, closed_dates=("2026-10-17",)))
    b = dataclasses.replace(b, schedule=dataclasses.replace(b.schedule, closed_dates=("2026-10-18",)))
    (e,) = build(a, b)
    assert e.schedule.closed_dates == ("2026-10-17", "2026-10-18")


# ---- 알 수 없는 값은 비워 둔다 ----------------------------------------------------------------
def test_unknown_facts_are_listed_and_never_guessed():
    (e,) = build(obs("s:1"))
    assert e.price.kind == "unknown" and e.reservation.required == "unknown"
    assert e.eligibility.stated_open == "unknown" and e.eligibility.foreigner == "unknown"
    assert e.language.english_guidance == "unknown" and e.language.languages == ()
    assert {"sessions", "price", "reservation", "eligibility", "language"} <= set(e.needs_check)
    assert e.reservation_status == "unknown"


def test_site_english_page_is_separate_from_event_language():
    import dataclasses

    o = obs("s:1")
    o = dataclasses.replace(o, language=dataclasses.replace(o.language, site_english_page="yes"))
    (e,) = build(o)
    assert e.language.site_english_page == "yes"
    assert e.language.english_guidance == "unknown" and e.language.languages == ()
    assert "language" in e.needs_check


def test_verification_needs_official_source_target_region_and_dates():
    assert build(obs("s:1"))[0].verification == "verified"
    assert build(obs("s:1", kind="sns"))[0].verification == "needs_check"
    assert build(obs("s:1", in_target="unknown"))[0].verification == "needs_check"
    assert build(obs("s:1", start=None, end=None))[0].verification == "needs_check"
    assert build(obs("s:1", demo=True))[0].verification == "needs_check"


def test_sessions_and_reservation_status_come_through():
    o = obs("s:1", sessions=(session("2026-10-16"),),
            reservation=Reservation(required="yes", deadline="2026-10-06", link="https://example.invalid/r"))
    (e,) = build(o)
    assert len(e.schedule.sessions) == 1 and "sessions" not in e.needs_check
    assert e.reservation_status == "closed"  # 신청 마감일이 지남


def test_restrictions_are_unioned_and_resident_only_is_kept():
    from domains.kcontext.catalog.rules import parse_eligibility

    a = obs("s:1", external_ids=("k",), eligibility=parse_eligibility("누구나"))
    b = obs("s:2", external_ids=("k",), origin="o2", eligibility=parse_eligibility("중구민"))
    (e,) = build(a, b)
    assert any(r["kind"] == "resident" for r in e.eligibility.restrictions)


def test_ids_are_stable_and_follow_prior_mapping():
    a = obs("s:1", external_ids=("k",))
    (e1,) = build(a)
    (e2,) = build(a)
    assert e1.id == e2.id and e1.id.startswith("ev:")
    b = obs("a:0", external_ids=("k",), origin="o2")  # 사전순으로 앞서는 새 출처가 붙어도
    (e3,) = build(a, b, prior={"k": e1.id})
    assert e3.id == e1.id


def test_last_verified_at_defaults_to_now_in_seoul():
    (e,) = build(obs("s:1"))
    assert e.last_verified_at == "2026-10-07T12:00"
    (e2,) = build(obs("s:1"), verified_at="2026-10-07T13:30")
    assert e2.last_verified_at == "2026-10-07T13:30"


def test_entry_roundtrips_through_json():
    import json

    from domains.kcontext.catalog.model import entry_from_dict

    (e,) = build(obs("s:1", sessions=(session(),)))
    again = entry_from_dict(json.loads(json.dumps(e.to_dict(), ensure_ascii=False)))
    assert again == e


def test_observation_type_is_exported():
    assert isinstance(obs("s:1"), Observation) and Eligibility().stated_open == "unknown"


def test_different_events_in_same_venue_and_dates_do_not_merge():
    a = obs("s:1", title="○○ 가을 음악회")
    b = obs("s:2", title="○○ 겨울 사진 전시회")
    assert not same_event(a, b) and len(build(a, b)) == 2
