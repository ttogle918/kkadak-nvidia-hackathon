"""챗봇 일정 흐름의 순수 조립부 — context 검증, bundle 정리, 행사 검색 요청 만들기, 고정 문구. I/O 없음(검색 호출 제외).

계약: ``docs/chat-bundle.contract.md``. 파이프라인 묶음은 신뢰하지 않는 입력이다 — 모양을 확인하고 상한을 넘으면 자른다.
reply 문구는 서버 고정 문구에 숫자만 채운다(LLM 이 쓴 문장 아님).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date
from typing import Any

CONTEXT_SCHEMA = "chat-context/v1"
MAX_TRIP_DAYS = 31
MAX_ANCHORS = 20
MAX_MENTIONS = 5
MAX_CARDS = 100
MAX_PROBLEMS = 100
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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


def build_search_args(bundle: dict[str, Any], trip: tuple[str, str] | None) -> dict[str, Any] | None:
    """`/api/events/search` 와 같은 요청 형식. trip 을 알 수 없으면 None."""
    plans = plans_from_anchors(bundle["itinerary"]["anchors"])
    trip = trip or derive_trip(plans)
    if trip is None:
        return None
    return {"trip": {"from": trip[0], "to": trip[1]}, "itinerary": plans,
            "free_slots": slots_from_free(bundle["itinerary"]["free_slots"])}


def attach_events(bundle: dict[str, Any], trip: tuple[str, str] | None,
                  search: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
    """검색을 호출해 bundle["events"] 를 채운다. 못 하면 events=None + EVENTS_UNAVAILABLE(사실만)."""
    args = build_search_args(bundle, trip)
    res: Any = None
    if args is not None:
        try:
            res = search(args)
        except Exception:  # noqa: BLE001 - 내부 오류 본문은 싣지 않는다
            res = None
    if not isinstance(res, dict) or "error" in res or not isinstance(res.get("events"), list):
        bundle["events"] = None
        bundle["problems"].append(_problem("EVENTS_UNAVAILABLE", "주변 행사를 지금 확인하지 못함"))
    else:
        bundle["events"] = res


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
