from kc_catalog_helpers import NOW, obs

from domains.kcontext.catalog.fit import fit_event
from domains.kcontext.catalog.grounding import build_ai_context, validate_ai_output
from domains.kcontext.catalog.merge import build_entries
from domains.kcontext.catalog.query import search_events
from domains.kcontext.catalog.routes import TableRouteProvider
from domains.kcontext.catalog.stories import link_stories, load_stories
from domains.kcontext.contract.records import story_from_dict

TRIP = {"from": "2026-10-16", "to": "2026-10-16"}
HERE = (37.5700, 126.9950)


def entry(**kw):
    (e,) = build_entries([obs("s:1", lat=HERE[0], lng=HERE[1], **kw)], now=NOW)
    return e


def src(tier="A", kind="fact", quote="원문 구절 (합성)"):
    return {"source": {"id": "x1", "tier": tier, "name": "○○ 출처", "locator": "○쪽", "url": "https://example.invalid/s",
                       "published": None, "collected_at": "2026-10-07", "quote": quote},
            "stance": "support", "says": None, "claim_kind": kind}


def story(**over):
    base = {"id": "st1", "region": "jung", "title": {"ko": "○○ 길", "en": "○○ Road"}, "theme": "○○", "era": None,
            "geometry": {"type": "segment", "coords": [[37.5701, 126.9951], [37.5710, 126.9960]],
                         "basis": "합성 예시", "space": "geo"},
            "alignment": "approx",
            "claims": [{"text": "이 구간은 옛 기록에 나온다 (합성)", "evidence": [src()]},
                       {"text": "전해 내려오는 이야기 (합성)", "evidence": [src("B", "lore")]}],
            "narration": None, "synthetic": False}
    base.update(over)
    return story_from_dict(base)


# ---- 공간의 이야기 ----------------------------------------------------------------------------
def test_no_stories_ship_with_the_repo_yet():
    assert load_stories() == []  # 검증된 이야기가 없으면 만들어 내지 않는다


def test_verified_story_is_linked_with_facts_lore_and_suggestions_kept_apart():
    (s,) = link_stories(entry(), [story()])
    assert [c["kind"] for c in s["facts"]] == ["fact"] and [c["kind"] for c in s["lore"]] == ["lore"]
    assert s["lore"][0]["label"] == "전설·속설" and s["facts"][0]["label"] == "역사적 사실"
    assert s["facts"][0]["sources"][0]["quote"] and s["facts"][0]["sources"][0]["tier"] == "A"
    assert s["experience"]["kind"] == "service_suggestion" and s["record_prompt"]["kind"] == "service_suggestion"
    assert "사랑" not in s["experience"]["text"] and "효과" not in s["experience"]["text"]
    assert s["location_basis"] == "합성 예시"


def test_synthetic_or_unsourced_or_far_stories_are_not_shown():
    e = entry()
    assert link_stories(e, [story(synthetic=True)]) == []
    assert len(link_stories(e, [story(synthetic=True)], include_synthetic=True)) == 1
    far = story(geometry={"type": "point", "coords": [[37.60, 127.05]], "basis": "합성", "space": "geo"})
    assert link_stories(e, [far]) == []
    only_blog = story(claims=[{"text": "주장 (합성)", "evidence": [src("D")]}])
    assert link_stories(e, [only_blog]) == []  # 공식·학술 출처(S·A·B)가 없으면 소개하지 않는다


def test_events_without_coordinates_get_no_stories():
    (e,) = build_entries([obs("s:1")], now=NOW)
    assert link_stories(e, [story()]) == []


def test_english_text_is_used_when_requested():
    (s,) = link_stories(entry(), [story()], lang="en")
    assert s["title"] == "○○ Road" and s["experience"]["text"].startswith("Walk")


# ---- AI 근거 범위 -----------------------------------------------------------------------------
def verified_event():
    e = entry(sessions=())
    r = search_events([e], {"trip": TRIP}, now=NOW)
    return r["events"][0]


def test_ai_context_only_contains_verified_events():
    ok = verified_event()
    unverified = {**ok, "id": "ev:u", "verification": "needs_check"}
    demo = {**ok, "id": "ev:d", "demo": True}
    ctx = build_ai_context([ok, unverified, demo])
    assert [e["entry_id"] for e in ctx["events"]] == [ok["id"]]
    assert ctx["events"][0]["evidence_urls"] == ["https://example.invalid/x"]
    assert "만들지 마라" in ctx["rules"]


def test_ai_output_must_cite_known_ids_and_provided_links():
    ev = verified_event()
    ctx = build_ai_context([ev])
    eid = ev["id"]
    good = {"entry_id": eid, "text": "2026-10-16 에 ○○ 홀에서 열립니다.", "evidence_urls": ["https://example.invalid/x"]}
    ok, bad = validate_ai_output([
        good,
        {**good, "entry_id": "ev:zzz"},
        {**good, "evidence_urls": []},
        {**good, "evidence_urls": ["https://evil.invalid/"]},
        {**good, "text": ""},
        {**good, "text": "2026-10-17 에 열립니다."},       # 사실에 없는 날짜
        {**good, "text": "이동은 25분 걸립니다."},          # 사실에 없는 숫자(이동시간)
    ], ctx)
    assert ok == [good] and len(bad) == 6
    assert {b["reason"] for b in bad} == {"알 수 없는 행사 id", "근거 링크가 없거나 제공된 링크가 아님",
                                          "문장이 없음", "사실에 없는 숫자가 들어 있음"}


def test_numbers_from_fit_results_are_allowed_but_only_those():
    import dataclasses

    o = obs("s:1", lat=HERE[0], lng=HERE[1])
    from kc_catalog_helpers import session

    o = dataclasses.replace(o, schedule=dataclasses.replace(o.schedule, sessions=(session("2026-10-16", "19:00", "20:30"),)))
    (e,) = build_entries([o], now=NOW)
    ev = search_events([e], {"trip": TRIP}, now=NOW)["events"][0]
    a, b, c = (37.5650, 126.9900), HERE, (37.5750, 127.0)
    prov = TableRouteProvider({(a, b): 10, (b, c): 12, (a, c): 15})
    sug = fit_event(ev, [{"id": "낮", "title": "낮", "date": "2026-10-16", "start": "14:00", "end": "17:00",
                          "lat": a[0], "lng": a[1]},
                         {"id": "밤", "title": "밤", "date": "2026-10-16", "start": "22:00", "end": "23:00",
                          "lat": c[0], "lng": c[1]}], prov)
    ctx = build_ai_context([ev], sug)
    ok, bad = validate_ai_output([{"entry_id": ev["id"], "text": "추가 이동은 7분입니다.",
                                   "evidence_urls": [ev["links"][0]["url"]]},
                                  {"entry_id": ev["id"], "text": "추가 이동은 8분입니다.",
                                   "evidence_urls": [ev["links"][0]["url"]]}], ctx)
    assert len(ok) == 1 and len(bad) == 1
