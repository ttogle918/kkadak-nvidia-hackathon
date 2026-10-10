"""T438 — 채팅 주변 행사 거리 정렬·반경(D30 ①②)."""
from backend.chat_story import NEARBY_MAX, attach_events

TRIP = ("2026-10-16", "2026-10-16")
JONGNO = (37.5700, 126.9769)


def _bundle(anchors):
    return {"itinerary": {"anchors": anchors, "free_slots": []}, "problems": [], "coverage_note": None}


def _anchor(name, ll=None):
    a = {"type": "visit", "name": name, "from": "2026-10-16T10:00:00", "to": "2026-10-16T11:00:00"}
    if ll:
        a["lat"], a["lng"] = ll
    return a


def _ev(i, ll):
    v = {"name": f"v{i}"}
    if ll:
        v["lat"], v["lng"] = ll
    return {"id": f"e{i}", "title": f"t{i}", "venue": v}


def _run(anchors, events, excluded=()):
    b = _bundle(anchors)
    res = {"events": events, "excluded": list(excluded), "problems": []}
    attach_events(b, TRIP, lambda args: res)
    return b


def test_sorted_by_distance_and_far_excluded():
    evs = [_ev(1, (37.5700, 126.9969)), _ev(2, (37.5710, 126.9769)), _ev(3, (37.4979, 127.0276)), _ev(4, None)]
    b = _run([_anchor("광화문", JONGNO)], evs)
    e = b["events"]
    assert e["events_scope"] == "nearby"
    assert [x["id"] for x in e["events"]] == ["e2", "e1", "e4"]
    d = [x["distance_m"] for x in e["events"]]
    assert isinstance(d[0], int) and 100 < d[0] < 130 and 1700 < d[1] < 1800 and d[2] is None
    assert e["events_far_total"] == 1


def test_min_over_anchors_and_cap():
    evs = [_ev(i, (37.4979, 127.0276)) for i in range(30)] + [_ev(99, None)]
    b = _run([_anchor("a", JONGNO), _anchor("b", (37.4979, 127.0276))], evs)
    e = b["events"]
    assert len(e["events"]) == NEARBY_MAX and e["events"][0]["distance_m"] == 0
    assert all(x["distance_m"] == 0 for x in e["events"])  # 좌표 없는 행사는 20건 밖으로 밀림


def test_no_coordinate_anchor_is_seoul_scope_unchanged():
    evs = [_ev(1, (37.4979, 127.0276)), _ev(2, None)]
    b = _run([_anchor("모름")], evs)
    e = b["events"]
    assert e["events_scope"] == "seoul" and "events_far_total" not in e
    assert [x["id"] for x in e["events"]] == ["e1", "e2"] and all("distance_m" not in x for x in e["events"])


def test_rationale_counts_from_original():
    evs = [_ev(1, (37.5700, 126.9769)), _ev(2, (37.4979, 127.0276))]
    far = _run([_anchor("a", JONGNO)], evs)
    near_all = _run([_anchor("a")], evs)
    assert far["events_rationale"] == near_all["events_rationale"]
    assert len(far["events"]["events"]) == 1 and len(near_all["events"]["events"]) == 2
