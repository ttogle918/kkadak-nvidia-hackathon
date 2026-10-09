"""챗봇 일정 흐름의 순수 조립부 — context 검증, bundle 정리, 행사 검색 요청 만들기, 고정 문구. I/O 없음(검색 호출 제외).

계약: ``docs/chat-bundle.contract.md``. 파이프라인 묶음은 신뢰하지 않는 입력이다 — 모양을 확인하고 상한을 넘으면 자른다.
reply 문구는 서버 고정 문구에 숫자만 채운다(LLM 이 쓴 문장 아님).
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping
from datetime import date, timedelta
from typing import Any

CONTEXT_SCHEMA = "chat-context/v1"
MAX_TRIP_DAYS = 31
MAX_ANCHORS = 20
MAX_MENTIONS = 5
MAX_CARDS = 100
MAX_PROBLEMS = 100
# kc-chat-bundle/v2 상한(sprint-3 §5.2)
MAX_ROUTES = 7
MAX_LEGS = 20
MAX_SKIPPED = 20
MAX_RATIONALE = 100
MAX_CHIPS = 8
MAX_ROWS = 12
MAX_ITEMS = 20
CAP_TEXT = 300  # 프론트 CAP.text 와 같은 문자열 상한
CAP_KEY = 120
SCHEDULE_KEYS = frozenset({"source", "attempts", "model", "prompt_sha", "cache_created_at"})
SCHEDULE_SOURCES = ("llm", "cache", "rules")
SKIP_REASONS = ("좌표 없음", "시각 없음")
MENTION_PREFIX = "mention:"
EVENT_PREFIX = "event:"
# 시간이 모자라 행사 검색을 건너뛸 때 coverage_note 에 덧붙이는 고정 문구(W5)
EVENTS_SKIPPED_NOTE = "시간이 모자라 행사 검색을 건너뜀"
MIN_EVENT_SEARCH_S = 3.0  # 남은 시간이 이보다 적으면 행사 검색을 건너뛴다
EVENT_SEARCH_MAX_S = 60.0  # 행사 검색 한도 상한(catalog_runner 기본값과 같다)
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class BadContext(ValueError):
    pass


def _d(v: Any) -> date:
    if not isinstance(v, str) or not _ISO.match(v):
        raise BadContext("date")
    try:
        return date.fromisoformat(v)
    except ValueError:
        raise BadContext("date") from None


def validate_context(ctx: Any) -> dict[str, Any]:
    """chat-context/v1 엄격 검증. 허용 키만, 날짜 형식·from<=to·최대 31일. 정규화한 dict 를 돌려준다."""
    if not isinstance(ctx, dict) or not set(ctx) <= {"schema", "lang", "trip"}:
        raise BadContext("keys")
    if "schema" in ctx and ctx["schema"] != CONTEXT_SCHEMA:
        raise BadContext("schema")
    lang = ctx.get("lang", "ko")
    if lang not in ("ko", "en"):
        raise BadContext("lang")
    out: dict[str, Any] = {"lang": lang, "trip": None}
    trip = ctx.get("trip")
    if trip is not None:
        if not isinstance(trip, dict) or set(trip) != {"from", "to"}:
            raise BadContext("trip")
        a, b = _d(trip["from"]), _d(trip["to"])
        if a > b or (b - a).days + 1 > MAX_TRIP_DAYS:
            raise BadContext("trip range")
        out["trip"] = (a.isoformat(), b.isoformat())
    return out


# ---- bundle 정리 ---------------------------------------------------------------------------
class BadBundle(ValueError):
    pass


def _problem(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


# ---- v2 필드 검사 (모두 신뢰하지 않는 입력: 새 객체로 다시 만들고, 틀리면 그 필드만 버린다) --------------
class _Drop(ValueError):
    """이 v2 필드는 모양이 틀렸다 — 필드 전체를 버린다."""


def _int(v: Any) -> int:
    if isinstance(v, bool) or not isinstance(v, int):
        raise _Drop
    return v


def _str(v: Any, cap: int = CAP_TEXT) -> str:
    if not isinstance(v, str):
        raise _Drop
    return v[:cap]


def _bi(v: Any) -> dict[str, str]:
    if not isinstance(v, dict) or not isinstance(v.get("ko"), str) or not isinstance(v.get("en"), str):
        raise _Drop
    return {"ko": v["ko"][:CAP_TEXT], "en": v["en"][:CAP_TEXT]}


def _num(v: Any) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise _Drop
    return v


def _ll(v: Any) -> list[float]:
    if not isinstance(v, list) or len(v) != 2:
        raise _Drop
    lat, lng = _num(v[0]), _num(v[1])
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise _Drop
    return [lat, lng]


def clean_schedule(v: Any) -> dict[str, Any]:
    """허용 키(source·attempts·model·prompt_sha·cache_created_at)만, 타입 확인. 틀리면 _Drop."""
    if not isinstance(v, dict) or not set(v) <= SCHEDULE_KEYS or v.get("source") not in SCHEDULE_SOURCES:
        raise _Drop
    out: dict[str, Any] = {"source": v["source"]}
    if "attempts" in v:
        a = _int(v["attempts"])
        if a < 0:
            raise _Drop
        out["attempts"] = a
    if v.get("model") is not None:
        out["model"] = _str(v["model"], 100)
    elif "model" in v:
        out["model"] = None
    if "prompt_sha" in v:
        out["prompt_sha"] = _str(v["prompt_sha"], 64)
    if v.get("cache_created_at") is not None:
        c = _str(v["cache_created_at"], 20)
        if not _UTC.match(c):
            raise _Drop
        out["cache_created_at"] = c
    elif "cache_created_at" in v:
        out["cache_created_at"] = None
    return out


def _leg(v: Any) -> dict[str, Any]:
    if not isinstance(v, dict):
        raise _Drop
    wm = v.get("walk_min")
    if not isinstance(v.get("estimated"), bool):
        raise _Drop
    straight = _int(v.get("straight_m"))
    walk = None if wm is None else _int(wm)
    if straight < 0 or (walk is not None and walk < 0):
        raise _Drop
    return {"from": _str(v.get("from"), 80), "to": _str(v.get("to"), 80),
            "from_ll": _ll(v.get("from_ll")), "to_ll": _ll(v.get("to_ll")),
            "straight_m": straight, "walk_min": walk,
            "provider": _str(v.get("provider"), 60), "estimated": v["estimated"]}


def _skipped(v: Any) -> dict[str, str]:
    if not isinstance(v, dict) or v.get("reason") not in SKIP_REASONS:
        raise _Drop
    return {"from": _str(v.get("from"), 80), "to": _str(v.get("to"), 80), "reason": v["reason"]}


def clean_routes(v: Any, cut: list[str]) -> list[dict[str, Any]]:
    if not isinstance(v, list):
        raise _Drop
    if len(v) > MAX_ROUTES:
        v, cut[:] = v[:MAX_ROUTES], [*cut, "routes"]
    out = []
    for r in v:
        if not isinstance(r, dict) or not isinstance(r.get("legs"), list) \
                or not isinstance(r.get("skipped"), list):
            raise _Drop
        d = r.get("date")
        if not isinstance(d, str) or not _ISO.match(d):
            raise _Drop
        legs, skipped = r["legs"], r["skipped"]
        if len(legs) > MAX_LEGS:
            legs, cut[:] = legs[:MAX_LEGS], [*cut, "legs"]
        if len(skipped) > MAX_SKIPPED:
            skipped, cut[:] = skipped[:MAX_SKIPPED], [*cut, "skipped"]
        day = r.get("day")
        out.append({"id": _str(r.get("id"), CAP_KEY), "day": None if day is None else _int(day), "date": d,
                    "legs": [_leg(x) for x in legs], "skipped": [_skipped(x) for x in skipped]})
    return out


def _rationale(key: str, v: Any, cut: list[str]) -> dict[str, Any]:
    """Rationale 한 건. card_id 는 키와 같아야 한다."""
    if not isinstance(v, dict) or v.get("card_id") != key or not isinstance(v.get("chips"), list) \
            or not isinstance(v.get("items"), dict):
        raise _Drop
    chips = v["chips"]
    if len(chips) > MAX_CHIPS:
        chips, cut[:] = chips[:MAX_CHIPS], [*cut, "chips"]
    out_chips = []
    for c in chips:
        if not isinstance(c, dict) or c.get("tone") not in ("old", "now"):
            raise _Drop
        out_chips.append({"key": _str(c.get("key"), 60), "tone": c["tone"], "label": _bi(c.get("label"))})
    items_raw = list(v["items"].items())
    if len(items_raw) > MAX_ITEMS:
        items_raw, cut[:] = items_raw[:MAX_ITEMS], [*cut, "items"]
    items: dict[str, Any] = {}
    for k, it in items_raw:
        if not isinstance(k, str) or not isinstance(it, dict) or not isinstance(it.get("rows"), list):
            raise _Drop
        rows = it["rows"]
        if len(rows) > MAX_ROWS:
            rows, cut[:] = rows[:MAX_ROWS], [*cut, "rows"]
        items[k[:60]] = {"title": _bi(it.get("title")), "text": _bi(it.get("text")),
                         "rows": [{"k": _bi(r.get("k") if isinstance(r, dict) else None),
                                   "v": _bi(r.get("v") if isinstance(r, dict) else None)} for r in rows]}
    return {"card_id": key, "chips": out_chips, "items": items}


def clean_rationale(v: Any, cut: list[str]) -> tuple[dict[str, Any], bool]:
    """키가 ``mention:`` 로 시작하는 것만 남긴다. (결과, 일부 항목을 버렸는가). dict 가 아니면 _Drop."""
    if not isinstance(v, dict):
        raise _Drop
    out: dict[str, Any] = {}
    dropped = False
    for key, val in v.items():
        if not isinstance(key, str) or not key.startswith(MENTION_PREFIX) or len(key) > CAP_KEY:
            dropped = True
            continue
        if len(out) >= MAX_RATIONALE:
            cut.append("rationale")
            break
        try:
            out[key] = _rationale(key, val, cut)
        except _Drop:
            dropped = True
    return out, dropped


def _clean_v2(raw: dict[str, Any], b: dict[str, Any], problems: list[dict[str, str]], cut: list[str]) -> None:
    """v2 가산 필드를 b 에 다시 쓴다. 틀린 필드는 지우고 FIELD_DROPPED. events_rationale 은 서버가 만든다 — 입력은 버린다."""
    b.pop("events_rationale", None)

    def drop(name: str) -> None:
        b.pop(name, None)
        problems.append(_problem("FIELD_DROPPED", f"모양이 틀려 버린 필드: {name}"))

    if "schedule" in raw:
        try:
            b["schedule"] = clean_schedule(raw["schedule"])
        except _Drop:
            drop("schedule")
    if "routes" in raw:
        c: list[str] = []
        try:
            b["routes"] = clean_routes(raw["routes"], c)
            cut.extend(c)
        except _Drop:
            drop("routes")
    if "rationale" in raw:
        c = []
        try:
            b["rationale"], partial = clean_rationale(raw["rationale"], c)
            cut.extend(c)
            if partial:
                problems.append(_problem("FIELD_DROPPED", "모양이 틀려 버린 항목: rationale"))
        except _Drop:
            drop("rationale")
    if "story_routes_note" in raw:
        try:
            b["story_routes_note"] = _bi(raw["story_routes_note"])
        except _Drop:
            drop("story_routes_note")


def clean_bundle(raw: dict[str, Any]) -> dict[str, Any]:
    """모양을 확인하고 상한(앵커 20·앵커당 언급 5·카드·problems)을 넘으면 자른다(+TRUNCATED). 모양이 틀리면 BadBundle."""
    itin, ments = raw.get("itinerary"), raw.get("mentions")
    if not isinstance(itin, dict) or not isinstance(itin.get("anchors"), list) \
            or not isinstance(itin.get("free_slots"), list):
        raise BadBundle("itinerary")
    if not isinstance(ments, dict) or not isinstance(ments.get("anchors"), list):
        raise BadBundle("mentions")
    if not isinstance(raw.get("cards"), list) or not isinstance(raw.get("problems"), list):
        raise BadBundle("cards")
    b = dict(raw)
    problems = [p for p in raw["problems"] if isinstance(p, dict)][:MAX_PROBLEMS]
    cut: list[str] = []
    anchors = itin["anchors"]
    if len(anchors) > MAX_ANCHORS:
        anchors, cut = anchors[:MAX_ANCHORS], [*cut, "anchors"]
    rows = []
    for r in ments["anchors"]:
        if not isinstance(r, dict) or not isinstance(r.get("mentions"), list):
            raise BadBundle("mentions row")
        if len(r["mentions"]) > MAX_MENTIONS:
            r = {**r, "mentions": r["mentions"][:MAX_MENTIONS]}
            cut.append("mentions")
        rows.append(r)
    if len(rows) > MAX_ANCHORS:
        rows, cut = rows[:MAX_ANCHORS], [*cut, "mention_rows"]
    cards = raw["cards"]
    if len(cards) > MAX_CARDS:
        cards, cut = cards[:MAX_CARDS], [*cut, "cards"]
    b["itinerary"] = {**itin, "anchors": anchors}
    b["mentions"] = {**ments, "anchors": rows}
    b["cards"] = cards
    _clean_v2(raw, b, problems, cut)
    if cut:
        problems.append(_problem("TRUNCATED", "상한을 넘어 일부를 잘랐음: " + ",".join(sorted(set(cut)))))
    b["problems"] = problems
    b["status"] = "ok" if anchors else "no_anchors"
    b.setdefault("trip", None)
    b["events"] = None
    return b


# ---- 행사 검색 요청 ------------------------------------------------------------------------
def _hm(iso: Any) -> str | None:
    return iso[11:16] if isinstance(iso, str) and len(iso) >= 16 and iso[10] == "T" else None


def _day(iso: Any) -> str | None:
    return iso[:10] if isinstance(iso, str) and _ISO.match(iso[:10] or "") else None


def _mins(hm: str) -> int:
    return int(hm[:2]) * 60 + int(hm[3:5])


def _fmt(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


def plans_from_anchors(anchors: list[Any]) -> list[dict[str, Any]]:
    """방문(visit) 앵커 중 날짜·시작 시각이 있는 것만 Plan 으로. 끝 시각이 없으면 시작 +60분(최대 23:59)로 가정하고 표시한다."""
    plans: list[dict[str, Any]] = []
    for i, a in enumerate(anchors):
        if not isinstance(a, dict) or a.get("type") != "visit":
            continue
        d, s = _day(a.get("from")), _hm(a.get("from"))
        if d is None or s is None:
            continue
        end, assumed = None, False
        if _day(a.get("to")) == d and _hm(a["to"]) and _mins(_hm(a["to"])) > _mins(s):
            end = _hm(a["to"])
        else:
            m = min(_mins(s) + 60, 23 * 60 + 59)
            if m <= _mins(s):
                continue
            end, assumed = _fmt(m), True
        p: dict[str, Any] = {"id": f"chat_{i}", "title": str(a.get("name") or "")[:120],
                             "date": d, "start": s, "end": end}
        for k in ("lat", "lng"):
            v = a.get(k)
            p[k] = float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None
        if assumed:
            p["end_assumed"] = True
        plans.append(p)
    return plans


def slots_from_free(slots: list[Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for s in slots:
        if not isinstance(s, dict):
            continue
        d, a = _day(s.get("from")), _hm(s.get("from"))
        b = _hm(s.get("to"))
        if d is None or a is None or b is None:
            continue
        if _day(s.get("to")) != d:
            b = "23:59"  # 자정을 넘는 빈 시간은 그날 끝까지만 쓴다
        if _mins(a) < _mins(b):
            out.append({"date": d, "from": a, "to": b})
    return out


def derive_trip(plans: list[dict[str, Any]]) -> tuple[str, str] | None:
    days = sorted({p["date"] for p in plans})
    if not days:
        return None
    a, b = date.fromisoformat(days[0]), date.fromisoformat(days[-1])
    return (days[0], days[-1]) if (b - a).days + 1 <= MAX_TRIP_DAYS else None


# 행사 검색 범위를 어느 기준으로 정했는지 coverage_note 에 남기는 고정 문구(D22 ③)
RANGE_NOTES = {
    "anchors": "일정 날짜 범위로 찾았어요",
    "trip": "여행 기간으로 찾았어요",
    "today": "날짜를 몰라 오늘부터 7일 안에서 찾았어요",
}
TODAY_WINDOW_DAYS = 7


def anchor_range(anchors: list[Any]) -> tuple[str, str] | None:
    """모든 앵커의 from·to 날짜 중 최소~최대. 비었거나 31일을 넘으면 None."""
    days = sorted({d for a in anchors if isinstance(a, dict) for d in (_day(a.get("from")), _day(a.get("to"))) if d})
    if not days:
        return None
    n = (date.fromisoformat(days[-1]) - date.fromisoformat(days[0])).days + 1
    return (days[0], days[-1]) if n <= MAX_TRIP_DAYS else None


def event_range(bundle: dict[str, Any], trip: tuple[str, str] | None,
                today: date | None) -> tuple[tuple[str, str] | None, str | None]:
    """((from, to), 기준 "anchors"|"trip"|"today"). 우선순위: 일정 앵커 날짜 → 화면 여행 기간 → 오늘부터 7일."""
    r = anchor_range(bundle["itinerary"]["anchors"])
    if r is not None:
        return r, "anchors"
    if trip is not None:
        return trip, "trip"
    if today is not None:
        return (today.isoformat(), (today + timedelta(days=TODAY_WINDOW_DAYS - 1)).isoformat()), "today"
    return None, None


def build_search_args(bundle: dict[str, Any], trip: tuple[str, str] | None,
                      today: date | None = None) -> dict[str, Any] | None:
    """`/api/events/search` 와 같은 요청 형식. 범위를 정할 수 없으면 None."""
    rng, _ = event_range(bundle, trip, today)
    if rng is None:
        return None
    plans = plans_from_anchors(bundle["itinerary"]["anchors"])
    return {"trip": {"from": rng[0], "to": rng[1]}, "itinerary": plans,
            "free_slots": slots_from_free(bundle["itinerary"]["free_slots"])}


def _add_note(bundle: dict[str, Any], phrase: str) -> None:
    note = bundle.get("coverage_note")
    bundle["coverage_note"] = f"{note} {phrase}."[:CAP_TEXT] if isinstance(note, str) and note else f"{phrase}."


def attach_events(bundle: dict[str, Any], trip: tuple[str, str] | None,
                  search: Callable[[dict[str, Any]], dict[str, Any]], *, skip: bool = False,
                  today: date | None = None) -> None:
    """검색을 호출해 bundle["events"]·["events_rationale"] 을 채운다.

    범위 우선순위(D22 ③): 일정 앵커 날짜 최소~최대 → trip → today 부터 7일. 쓴 기준을 coverage_note 에 고정 문구로 남긴다.
    못 하면 events=None + EVENTS_UNAVAILABLE(사실만). ``skip`` 이면 검색을 부르지 않고(시간 예산 부족, W5)
    ``coverage_note`` 에 고정 문구를 덧붙인다.
    """
    bundle.pop("events_rationale", None)
    rng, basis = (None, None) if skip else event_range(bundle, trip, today)
    args = None if rng is None else build_search_args(bundle, trip, today)
    res: Any = None
    if args is not None:
        try:
            res = search(args)
        except Exception:  # noqa: BLE001 - 내부 오류 본문은 싣지 않는다
            res = None
    if basis is not None:
        _add_note(bundle, RANGE_NOTES[basis])
    if not isinstance(res, dict) or "error" in res or not isinstance(res.get("events"), list):
        bundle["events"] = None
        msg = EVENTS_SKIPPED_NOTE if skip else (
            "주변 행사를 지금 확인하지 못함" if args is not None else "여행 기간과 일정 날짜를 몰라 행사를 찾지 않았어요")
        bundle["problems"].append(_problem("EVENTS_UNAVAILABLE", msg))
        if skip:
            _add_note(bundle, EVENTS_SKIPPED_NOTE)
    else:
        bundle["events"] = res
        er = event_rationale(res)
        if er:
            bundle["events_rationale"] = er


def search_budget_s(elapsed_s: float, *, front_limit_s: float, margin_s: float) -> float | None:
    """행사 검색 한도 = 프론트 상한 - 여유 - 파이프라인 경과(최대 60초). 3초 미만이면 None(건너뜀)."""
    left = min(EVENT_SEARCH_MAX_S, front_limit_s - margin_s - elapsed_s)
    return None if left < MIN_EVENT_SEARCH_S else left


# ---- 행사 판단 근거 (고정 템플릿 + 검색 결과 값만; LLM·새 문장 없음) -----------------------------------
_TIER = {"official_site": "A", "official_api": "B", "press": "B", "sns": "C", "ai_extracted": "C",
         "report": "D", "manual": "D", "demo": "D"}
_AVAIL = {
    "session_match": ({"ko": "회차 확인됨", "en": "Session confirmed"}, "now"),
    "date_range_unconfirmed": ({"ko": "기간 안 — 회차 확인 필요", "en": "Within the run — sessions unconfirmed"}, "now"),
    "postponed": ({"ko": "연기됨", "en": "Postponed"}, "old"),
}
_TIER_LABEL = {
    "A": {"ko": "주최 공식 출처", "en": "Official organizer source"},
    "B": {"ko": "공식 API·보도자료", "en": "Official API or press release"},
    "C": {"ko": "검색 수집 · 미확인", "en": "Search-collected · unverified"},
    "D": {"ko": "제보·수기 · 미확인", "en": "Tip or manual entry · unverified"},
}
_NO_SOURCE = {"ko": "출처 링크 없음", "en": "No source link"}
_STATE = {"yes": {"ko": "열림", "en": "Open"}, "no": {"ko": "휴무", "en": "Closed"},
          "unknown": {"ko": "확인 필요", "en": "Needs checking"}}


def _b(ko: str, en: str) -> dict[str, str]:
    return {"ko": ko[:CAP_TEXT], "en": en[:CAP_TEXT]}


def _tier(ev: dict[str, Any]) -> str | None:
    links = ev.get("links")
    tiers = sorted(_TIER.get(lk.get("kind"), "D") for lk in links if isinstance(lk, dict)) \
        if isinstance(links, list) else []
    return tiers[0] if tiers else None


def _one_event_rationale(key: str, ev: dict[str, Any], res: dict[str, Any]) -> dict[str, Any]:
    chips: list[dict[str, Any]] = []
    items: dict[str, Any] = {}
    # avail — 가용성 고정 라벨 + 맞는 날짜 행
    label, tone = _AVAIL.get(ev.get("availability"), ({"ko": "확인 필요", "en": "Needs checking"}, "now"))
    chips.append({"key": "avail", "tone": tone, "label": {"ko": f"● {label['ko']}", "en": f"● {label['en']}"}})
    rows = []
    for d in (ev.get("matching_dates") if isinstance(ev.get("matching_dates"), list) else [])[:MAX_ROWS]:
        if isinstance(d, dict) and isinstance(d.get("date"), str):
            st = _STATE.get(d.get("state"), _STATE["unknown"])
            rows.append({"k": _b(d["date"], d["date"]), "v": _b(st["ko"], st["en"])})
    items["avail"] = {"title": label, "text": _b("날짜·회차·휴무는 코드가 계산했습니다(AI 가 계산하지 않음).",
                                                 "Dates, sessions and closures were computed by code, not by AI."),
                      "rows": rows}
    # src — 출처 등급
    t = _tier(ev)
    tl = _TIER_LABEL[t] if t else _NO_SOURCE
    n_links = len(ev["links"]) if isinstance(ev.get("links"), list) else 0
    chips.append({"key": "src", "tone": "now", "label": {"ko": f"● {tl['ko']}", "en": f"● {tl['en']}"}})
    srows = []
    for lk in (ev.get("links") if isinstance(ev.get("links"), list) else [])[:MAX_ROWS]:
        if isinstance(lk, dict):
            tier = _TIER.get(lk.get("kind"), "D")
            nm = lk.get("source_name") if isinstance(lk.get("source_name"), str) else ""
            when = str(lk.get("published_at") or ev.get("collected_at") or "—")
            srows.append({"k": _b(f"[{tier}] {nm}", f"[{tier}] {nm}"), "v": _b(when, when)})
    items["src"] = {"title": tl, "text": _b(f"출처 링크 {n_links}건. 같은 원천에서 재배포된 자료는 독립 출처로 세지 않습니다.",
                                            f"{n_links} source link(s). Re-published copies of one origin do not count as independent."),
                    "rows": srows}
    # funnel — 걸러진 개수
    n_ev = len(res["events"])
    excl = res.get("excluded") if isinstance(res.get("excluded"), list) else []
    total = n_ev + len(excl)
    chips.append({"key": "funnel", "tone": "now",
                  "label": _b(f"● 수집 {total}건 중 {n_ev}건 남김", f"● {n_ev} of {total} collected kept")})
    reasons: dict[str, int] = {}
    for x in excl:
        if isinstance(x, dict) and isinstance(x.get("reason"), str):
            reasons[x["reason"][:80]] = reasons.get(x["reason"][:80], 0) + 1
    items["funnel"] = {"title": _b(f"수집 {total}건 중 {n_ev}건 남김", f"{n_ev} of {total} collected kept"),
                       "text": _b("걸러 낸 이유는 아래와 같습니다.", "Reasons for dropping the rest are below."),
                       "rows": [{"k": _b(k, k), "v": _b(str(v), str(v))}
                                for k, v in sorted(reasons.items())[:MAX_ROWS]]}
    # interest — 일치가 있을 때만
    hits = [h[:40] for h in ev["interest_match"] if isinstance(h, str)] \
        if isinstance(ev.get("interest_match"), list) else []
    if hits:
        chips.append({"key": "interest", "tone": "now", "label": _b("● 관심사 일치", "● Matches interests")})
        items["interest"] = {"title": _b("관심사 일치", "Matches interests"),
                             "text": _b(", ".join(hits[:5]), ", ".join(hits[:5])), "rows": []}
    # coverage — 검색 범위 문구(카탈로그가 준 값)
    cov = res.get("coverage")
    note = cov.get("note") if isinstance(cov, dict) and isinstance(cov.get("note"), str) else None
    if note:
        chips.append({"key": "coverage", "tone": "now", "label": _b("● 검색 범위", "● Search coverage")})
        items["coverage"] = {"title": _b("검색 범위", "Search coverage"), "text": _b(note, note), "rows": []}
    return {"card_id": key, "chips": chips[:MAX_CHIPS], "items": items}


def event_rationale(search: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """검색 결과 JSON 값으로만 만든 행사별 근거. 키는 ``event:<id>``(card_id 도 같은 키). 문자열 아닌 id 는 건너뛴다."""
    events = search.get("events") if isinstance(search, Mapping) else None
    if not isinstance(events, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for ev in events:
        if not isinstance(ev, dict) or not isinstance(ev.get("id"), str) or not ev["id"]:
            continue
        key = EVENT_PREFIX + ev["id"]
        if len(key) > CAP_KEY:
            continue
        out[key] = _one_event_rationale(key, ev, dict(search))
        if len(out) >= MAX_RATIONALE:
            break
    return out


# ---- 고정 문구 -----------------------------------------------------------------------------
def counts(bundle: dict[str, Any]) -> tuple[int, int, int | None]:
    n = len(bundle["itinerary"]["anchors"])
    m = sum(len(r["mentions"]) for r in bundle["mentions"]["anchors"])
    ev = bundle.get("events")
    return n, m, (len(ev["events"]) if isinstance(ev, dict) else None)


def reply_text(bundle: dict[str, Any]) -> dict[str, str]:
    n, m, k = counts(bundle)
    p = len(bundle["problems"])
    ko = f"일정 {n}개를 정리했어요. 실록에서 언급된 기록 {m}건"
    en = f"I organized {n} schedule item(s). Joseon Annals mentions found: {m}"
    if k is None:
        ko += "을 찾았어요. 주변 행사는 지금 확인하지 못했어요."
        en += ". Nearby events could not be checked right now."
    else:
        ko += f", 주변 행사 {k}건을 찾았어요."
        en += f", nearby events: {k}."
    if p:
        ko += f" 가정했거나 확인이 필요한 항목이 {p}건 있어요."
        en += f" {p} item(s) were assumed or need checking."
    return {"ko": ko, "en": en}
