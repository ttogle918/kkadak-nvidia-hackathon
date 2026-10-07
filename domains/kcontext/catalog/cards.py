"""행사 검색 결과 → 화면용 `now` 카드와 판단 근거(rationale).

형식은 새로 만들지 않는다: 카드는 `frontend/k-context/src/api/schema.js` 의 `validateCard`(kind=now)를 통과해야 하고,
판단 근거는 `src/data/rationale.js` 의 `{card_id, chips[], items{}}` 모양이다(AGENT_CONTEXT 3.3).

원칙
- 모르는 값은 카드에도 모른다고 쓴다. 딱지는 ``확인됨`` 이 아니면 ``확인 필요``(출처 충돌은 ``보류``)다.
  ``확인됨`` 은 공식 출처로 검증됐고 회차까지 확인됐고 마지막 확인이 오래되지 않았고 일정 제안이 맞을 때만.
- 참여 제한·연기·좌표 없음·일정에 맞지 않는 행사는 카드로 만들지 않고 깔때기(탈락 사유)에 센다.
- 이동시간을 모르면 `time_cost_min` 은 검증기가 숫자를 요구해 0 이지만 ``time_cost_unknown: true`` 를 같이 쓴다
  (계약을 숫자|null 로 넓히자는 제안: docs/events-cards.proposal.md). ``null_unknown_time_cost=True`` 면 null.
- 출처 등급: 주최 홈페이지 A · 공식 API·보도자료 B · SNS·AI 추출 C · 제보·수기·데모 D. C·D 는 ``unverified: true``.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import date

__all__ = ["build_now_cards", "tier_of"]

_TIER = {"official_site": "A", "official_api": "B", "press": "B", "sns": "C", "ai_extracted": "C",
         "report": "D", "manual": "D", "demo": "D"}
_CHECK_LABEL = {
    "dates": ("날짜", "Dates"), "sessions": ("회차", "Sessions"), "hours": ("운영 시간", "Hours"),
    "price": ("요금", "Price"), "reservation": ("예약", "Reservation"), "eligibility": ("참여조건", "Eligibility"),
    "foreigner": ("외국인 참여 조건", "Foreigner eligibility"), "language": ("진행 언어", "Event language"),
    "venue": ("장소", "Venue"), "region": ("개최 지역", "Host district"),
}
_FIELD_LABEL = {"start_date": ("시작일", "Start date"), "end_date": ("종료일", "End date"),
                "venue_name": ("장소", "Venue"), "price_kind": ("요금", "Price"),
                "reservation_required": ("예약 필요 여부", "Reservation needed"),
                "sessions": ("회차", "Sessions"), "lifecycle": ("개최 상태", "Status")}


def tier_of(kind: str) -> str:
    return _TIER.get(kind, "D")


def _t(ko: str, en: str) -> dict:
    return {"ko": ko, "en": en}


def _sources(ev: Mapping) -> list[dict]:
    out = []
    for lk in ev["links"]:
        basis = lk["published_at"] or ev["collected_at"]
        tier = tier_of(lk["kind"])
        out.append({
            "id": "src_" + hashlib.sha1((lk["url"] or lk["quote"]).encode()).hexdigest()[:8],
            "tier": tier, "name": lk["source_name"],
            "locator": f"{basis} {'게시' if lk['published_at'] else '수집'}",
            "url": lk["url"], "published": lk["published_at"], "collected_at": ev["collected_at"],
            "quote": lk["quote"], "unverified": tier in ("C", "D"),
        })
    return out


def _badge(ev: Mapping, sug: Mapping | None) -> str:
    if ev["verification"] == "conflict":
        return "보류"
    ok = (ev["verification"] == "verified" and ev["availability"] == "session_match" and not ev["stale"]
          and (sug is None or sug["status"] == "fit"))
    return "확인됨" if ok else "확인 필요"


def _day_index(trip_from: str, d: str) -> int:
    return (date.fromisoformat(d) - date.fromisoformat(trip_from)).days + 1


def _first_date(ev: Mapping) -> dict | None:
    return next((d for d in ev["matching_dates"] if d["state"] == "yes"), None) or next(
        (d for d in ev["matching_dates"] if d["state"] == "unknown"), None)


def _best_suggestion(ev: Mapping, sugs: Sequence[Mapping]) -> Mapping | None:
    mine = [s for s in sugs if s["entry_id"] == ev["id"] and s["status"] != "no_fit"]
    return mine[0] if mine else None


def _checks(ev: Mapping, sug: Mapping | None) -> list[dict]:
    v = ev["verification"]
    out = [{"level": {"verified": "ok", "conflict": "bad"}.get(v, "warn"),
            "text": {"verified": _t("공식 출처로 확인됨", "Confirmed by an official source"),
                     "conflict": _t("출처 간 충돌 — 확인 필요", "Sources disagree — needs checking")}.get(
                v, _t("확인 필요", "Needs checking"))}]
    out.append({"level": "ok" if ev["availability"] == "session_match" else "warn",
                "text": _t("회차 확인됨", "Session confirmed") if ev["availability"] == "session_match"
                else _t("기간 안 — 회차·시간 확인 필요", "Within the run — sessions need checking")})
    out.append({"level": "warn" if ev["stale"] else "ok",
                "text": _t("마지막 확인이 오래됨", "Not re-confirmed for a while") if ev["stale"]
                else _t(f"마지막 확인 {ev['last_verified_at']}", f"Last verified {ev['last_verified_at']}")})
    p = ev["participation"]
    out.append({"level": "ok" if p["status"] == "stated_open" else "warn",
                "text": _t("출처가 '누구나'라고 적음", "Source says open to all") if p["status"] == "stated_open"
                else _t("참여조건 확인 필요", "Eligibility needs checking")})
    if p["foreigner"] == "unknown":
        out.append({"level": "warn", "text": _t("외국인 참여 조건 확인 필요", "Foreigner eligibility needs checking")})
    r = ev["reservation"]
    out.append({"level": {"closed": "bad", "full": "bad", "open": "ok", "not_required": "ok"}.get(r["status"], "warn"),
                "text": {"closed": _t("예약 마감", "Reservations closed"), "full": _t("정원 마감", "Fully booked"),
                         "open": _t("예약 가능", "Reservations open"),
                         "not_required": _t("예약 불필요(출처 표기)", "No reservation (per source)")}.get(
                    r["status"], _t("예약 여부 확인 필요", "Reservation status needs checking"))})
    if sug is None or sug["extra_minutes"] is None:  # 추가 이동시간을 계산하지 못했으면(회차 없음·경로 없음 포함) 알린다
        out.append({"level": "warn", "text": _t("이동시간 확인 필요", "Travel time needs checking")})
    return out


def _caveats(ev: Mapping, srcs: Sequence[Mapping]) -> list[dict]:
    out = [_t(f"{_CHECK_LABEL[k][0]} 확인 필요", f"{_CHECK_LABEL[k][1]} needs checking")
           for k in ev["needs_check"] if k in _CHECK_LABEL]
    if any(s["unverified"] for s in srcs):
        out.insert(0, _t("검색 수집 · 미확인", "Collected by search · unverified"))
    return out


def _why_fits(ev: Mapping, d: dict | None) -> list[dict]:
    out = []
    if d is not None:
        out.append(_t(f"여행 날짜({d['date']})에 열림" if d["state"] == "yes" else f"여행 기간 안({d['date']}) — 회차 확인 필요",
                      f"Open on your travel date ({d['date']})" if d["state"] == "yes"
                      else f"Within your trip ({d['date']}) — sessions need checking"))
    if ev["interest_match"]:
        out.append(_t("관심사와 일치: " + ", ".join(ev["interest_match"]), "Matches: " + ", ".join(ev["interest_match"])))
    if ev["participation"]["status"] == "stated_open":
        out.append(_t("출처가 누구나 참여할 수 있다고 적음", "The source says anyone can join"))
    return out


def _rejected(ev: Mapping) -> list[dict]:
    out = []
    for c in ev["conflicts"]:
        f = _FIELD_LABEL.get(c["field"], (c["field"], c["field"]))
        vals = " / ".join(str(v["value"]) for v in c["values"])
        out.append({"claim": _t(f"{f[0]}: {vals}", f"{f[1]}: {vals}"),
                    "reason": _t("더 최근 공식 공지를 채택" if c["resolved"] else "출처 충돌 — 값을 확정하지 않음",
                                 "Chose the newer official notice" if c["resolved"] else "Sources disagree — value not fixed")})
    return out


def _body(ev: Mapping) -> dict:
    s = ev["schedule"]
    rng = s["start_date"] or "날짜 확인 필요"
    rng_en = s["start_date"] or "Date needs checking"
    if s["end_date"] and s["end_date"] != s["start_date"]:
        rng += f" ~ {s['end_date']}"
        rng_en += f" ~ {s['end_date']}"
    return _t(f"{rng} · {ev['venue']['name'] or '장소 확인 필요'}", f"{rng_en} · {ev['venue']['name'] or 'Venue needs checking'}")


def build_now_cards(
    result: Mapping, request: Mapping, *, null_unknown_time_cost: bool = False, include_demo: bool = False
) -> dict:
    """``search_events`` 결과(+ 일정이 있으면 ``suggestions``) → ``{cards, rationale, funnel, skipped}``."""
    trip_from = request["trip"]["from"]
    sugs = result.get("suggestions") or []
    itinerary = {p["id"]: p for p in (request.get("itinerary") or [])}
    added = {p.get("entry_id") for p in itinerary.values() if p.get("source") == "catalog" and p.get("entry_id")}
    cards: list[dict] = []
    skipped: list[dict] = []
    reasons: dict[str, int] = {}

    def skip(ev: Mapping, why: str) -> None:
        skipped.append({"id": ev["id"], "title": ev["title"], "reason": why})
        reasons[why] = reasons.get(why, 0) + 1

    for ev in result["events"]:
        if ev["demo"] and not include_demo:
            continue
        has_sugs = any(s["entry_id"] == ev["id"] for s in sugs)
        sug = _best_suggestion(ev, sugs)
        if ev["participation"]["status"] == "restricted":
            skip(ev, "참여 제한")
        elif ev["availability"] == "postponed":
            skip(ev, "연기됨")
        elif ev["venue"]["lat"] is None or ev["venue"]["lng"] is None:
            skip(ev, "좌표 없음")
        elif has_sugs and sug is None and ev["id"] not in added:
            skip(ev, "일정에 맞지 않음")
        elif not ev["links"]:
            skip(ev, "출처 없음")
        else:
            d = _first_date(ev)
            srcs = _sources(ev)
            known = sug is not None and sug["extra_minutes"] is not None
            between = []
            if sug is not None:
                for k in ("after_item_id", "before_item_id"):
                    it = itinerary.get(sug[k]) if sug.get(k) else None
                    if it:
                        between.append(_t(it["title"], it["title"]))
            sess = (sug["session"]["start_time"] if sug else None) or (
                d["sessions"][0]["start_time"] if d and d["sessions"] else None)
            slot = {"day": _day_index(trip_from, sug["date"] if sug else (d["date"] if d else trip_from))}
            if sess:
                slot["at"] = sess
            if between:
                slot["between"] = between
            cards.append({
                "id": "card_now_" + ev["id"].removeprefix("ev:"),
                "kind": "now",
                "entry_id": ev["id"],
                "title": _t(ev["title"], ev["title_en"] or ev["title"]),
                "kind_label": _t(ev["event_type"] or "행사", ev["event_type"] or "Event"),
                "place": _t(ev["venue"]["name"], ev["venue"]["name"]),
                "geometry": {"type": "point", "coords": [[ev["venue"]["lat"], ev["venue"]["lng"]]],
                             "radius_m": None, "space": "geo",
                             "basis": _t(f"{srcs[0]['name']} 좌표", f"Coordinates from {srcs[0]['name']}")},
                "body": _body(ev),
                "badge": _badge(ev, sug),
                "sources": srcs,
                "slot": slot,
                "time_cost_min": sug["extra_minutes"] if known else (None if null_unknown_time_cost else 0),
                "time_cost_unknown": not known,
                "valid": {"from": ev["schedule"]["start_date"], "to": ev["schedule"]["end_date"],
                          "as_of": (ev["last_verified_at"] or ev["collected_at"])[:10]},
                "user_state": "added" if ev["id"] in added else "proposed",  # 일정에 넣은 행사는 화면이 보낸 일정으로 안다
                "why_fits": _why_fits(ev, d),
                "checks": _checks(ev, sug),
                "caveats": _caveats(ev, srcs),
                "rejected": _rejected(ev),
                "demo": bool(ev["demo"]),
            })
    cand = len(result["events"]) + len(result.get("excluded", []))
    for x in result.get("excluded", []):
        reasons[x["reason"]] = reasons.get(x["reason"], 0) + 1
    funnel = {"candidates": cand, "adopted": len(cards), "reasons": reasons}
    return {"cards": cards, "rationale": {c["id"]: _rationale(c, funnel, result) for c in cards},
            "funnel": funnel, "skipped": skipped}


def _rationale(card: Mapping, funnel: Mapping, result: Mapping) -> dict:
    ev = next(e for e in result["events"] if e["id"] == card["entry_id"])
    n_src = len({s["id"] for s in card["sources"]})
    detour = (_t("● 이동시간 확인 필요", "● Travel time needs checking") if card["time_cost_unknown"]
              else _t(f"● 동선 +{card['time_cost_min']}분", f"● +{card['time_cost_min']} min detour"))
    chips = [
        {"key": "funnel", "tone": "now", "label": _t(f"● 후보 {funnel['candidates']}건 중 채택 {funnel['adopted']}",
                                                     f"● {funnel['adopted']} of {funnel['candidates']} candidates adopted")},
        {"key": "date", "tone": "now",
         "label": _t("● 회차 확인됨", "● Session confirmed") if ev["availability"] == "session_match"
         else _t("● 기간 안 — 회차 확인 필요", "● Within the run — sessions unconfirmed")},
        {"key": "src", "tone": "now", "label": _t(f"● 출처 {n_src}건 · 독립 {ev['independent_sources']}건",
                                                  f"● {n_src} sources · {ev['independent_sources']} independent")},
        {"key": "detour", "tone": "now", "label": detour},
    ]
    if ev["interest_match"]:
        chips.insert(2, {"key": "fit", "tone": "now", "label": _t("● 관심사 일치", "● Matches interests")})
    if ev["conflicts"]:
        chips.append({"key": "conflict", "tone": "now", "label": _t("● 출처 충돌", "● Sources conflict")})
    items = {
        "funnel": {"title": _t(f"후보 {funnel['candidates']}건 중 채택 {funnel['adopted']}",
                               f"{funnel['adopted']} of {funnel['candidates']} candidates adopted"),
                   "text": _t("걸러 낸 이유는 아래와 같습니다.", "Reasons for dropping the rest are below."),
                   "rows": [{"k": _t("채택", "Adopted"), "v": str(funnel["adopted"])}]
                   + [{"k": _t(k, k), "v": str(v)} for k, v in sorted(funnel["reasons"].items())]},
        "date": {"title": chips[1]["label"],
                 "text": _t("날짜·회차·휴무는 코드가 계산했습니다(AI 가 계산하지 않음).",
                            "Dates, sessions and closures were computed by code, not by AI."),
                 "rows": [{"k": _t("마지막 확인", "Last verified"), "v": ev["last_verified_at"] or "—"}]},
        "src": {"title": next(c["label"] for c in chips if c["key"] == "src"),
                "text": _t("같은 원천에서 재배포된 자료는 독립 출처로 세지 않습니다.",
                           "Re-published copies of one origin do not count as independent."),
                "rows": [{"k": _t(f"[{s['tier']}] {s['name']}", f"[{s['tier']}] {s['name']}"), "v": s["locator"]}
                         for s in card["sources"]]},
        "detour": {"title": detour,
                   "text": _t("추가 이동시간 = 앞→행사 + 행사→뒤 − 앞→뒤. 경로 서비스 결과만 쓰고 직선거리로 대신하지 않습니다.",
                              "Extra travel = prev→event + event→next − prev→next, from a route service only (never straight-line)."),
                   "rows": []},
    }
    if ev["interest_match"]:
        items["fit"] = {"title": _t("관심사 일치", "Matches interests"),
                        "text": _t(", ".join(ev["interest_match"]), ", ".join(ev["interest_match"])), "rows": []}
    if ev["conflicts"]:
        items["conflict"] = {"title": _t("출처 충돌", "Sources conflict"),
                             "text": _t("서로 다른 출처가 다르게 적은 값입니다. 해결되지 않은 값은 확정하지 않았습니다.",
                                        "Different sources disagree. Unresolved values are not fixed."),
                             "rows": [{"k": r["claim"], "v": r["reason"]} for r in card["rejected"]]}
    return {"card_id": card["id"], "chips": chips, "items": items}
