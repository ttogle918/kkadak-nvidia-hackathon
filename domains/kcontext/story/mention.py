"""후보 → 언급 기록(mention) 출력 형식, 그리고 화면 카드로의 부분 변환.

- quote 는 청크 본문(한문 원문)의 한 구절이다. 고치거나 번역하지 않는다.
- title_summary 는 한국사DB 편집자의 한글 요약이지 원문이 아니다(title_is_summary).
- 색인 텍스트는 신뢰할 수 없는 입력(D8) — 출력으로 나갈 문자열은 judge.inject.screen 을 통과해야 한다.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from domains.kcontext.index import LocalIndex
from domains.kcontext.judge.inject import screen
from domains.kcontext.story.finder import (
    DEFAULT_LIMIT,
    AnchorResult,
    Candidate,
    check_limit,
    clean_name,
    find_candidates,
    select,
)

SCHEMA = "kc-mention/v1"
MAX_QUOTE = 300
SOURCE_URL_OK = ("https://", "http://")

COVERAGE_NOTE = (
    "색인은 일부 지역 키워드가 들어간 실록 기사만 담고 있다. 이 목록에 없다고 해서 실록에 그 장소가 없다는 뜻이 아니다. "
    "검색은 한국사DB 한글 요약 제목(과 사전에 있는 별칭)의 글자 일치로 하므로, 제목에 이름이 없는 기사는 찾지 못한다. "
    "실록은 국역 없이 한문 원문만 담았다."
)


def _body(c: Candidate) -> str:
    """청크 text 는 '제목\\n본문' 이다(제목이 있을 때). 제목 줄을 뗀다."""
    text = c.chunk.text
    if c.chunk.meta.get("title_is_summary") == "true" and "\n" in text:
        return text.split("\n", 1)[1]
    return text


def make_quote(body: str, terms: tuple[str, ...], *, limit: int = MAX_QUOTE) -> tuple[str, bool]:
    """(quote, 앵커 표기가 quote 안에 있는가). 표기가 있으면 그 둘레를, 없으면 본문 앞부분을 자른다."""
    body = body.strip()
    pos = -1
    term_len = 0
    for t in terms:
        i = body.find(t)
        if i != -1 and (pos == -1 or i < pos):
            pos, term_len = i, len(t)
    if len(body) <= limit:
        return body, pos != -1
    if pos == -1:
        return body[:limit], False
    start = max(0, min(pos - (limit - term_len) // 2, len(body) - limit))
    return body[start : start + limit], True


def _date_label(c: Candidate) -> str:
    loc, aid = c.chunk.locator, c.article_id
    marker = f" · {aid}"
    return loc.split(marker, 1)[0] if marker in loc else ""


def _strings(m: Mapping[str, Any]) -> list[str]:
    out = [m["title_summary"], m["quote"], m["date_label"], m["king"] or ""]
    s = m["source"]
    out += [s["name"], s["locator"], s["quote"], s["url"]]
    return [x for x in out if x]


def build_mention(c: Candidate, terms: tuple[str, ...]) -> dict[str, Any]:
    ch = c.chunk
    title = (
        ch.text.split("\n", 1)[0]
        if ch.meta.get("title_is_summary") == "true" and "\n" in ch.text
        else ""
    )
    quote, has_anchor = make_quote(_body(c), terms)
    in_title = c.matched_term in title
    url = ch.url if ch.url.startswith(SOURCE_URL_OK) else ""
    return {
        "article_id": c.article_id,
        "king": ch.meta.get("king"),
        "date_label": _date_label(c),  # '(음력)' 표기를 그대로 둔다 — 양력 변환 안 함
        "calendar": ch.meta.get("calendar", "unknown"),
        "title_summary": title,  # 한국사DB 한글 요약(원문 아님)
        "title_is_summary": ch.meta.get("title_is_summary") == "true",
        "quote": quote,  # 한문 원문 구절(번역·수정 없음)
        "quote_has_anchor": has_anchor,
        "lang": ch.meta.get("lang", "orig"),  # "orig" = 한문 원문, 국역 없음
        "matched_term": c.matched_term,
        "matched_in": "title" if in_title else "body",
        "locator": ch.locator,
        "url": url,
        "tier": ch.tier,
        "score": round(c.score, 4),
        "source": {
            "id": ch.source_id,
            "name": ch.name,
            "locator": ch.locator,
            "tier": ch.tier,
            "collected_at": ch.collected_at,
            "quote": quote,
            "url": url,
        },
    }


def _anchor_echo(a: Mapping[str, Any], name: str) -> dict[str, Any]:
    def num(v: object) -> float | None:
        return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    day = a.get("day")
    return {
        "name": name,
        "lat": num(a.get("lat")),
        "lng": num(a.get("lng")),
        "day": day if isinstance(day, int) and not isinstance(day, bool) else None,
    }


def build_mentions(
    index: LocalIndex,
    anchors: list[Mapping[str, Any]],
    *,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """앵커마다 언급 기록을 돌려준다. 없으면 빈 목록과 이유 코드(no_match · excluded_by_screen · invalid_name)."""
    check_limit(limit)
    results: list[dict[str, Any]] = []
    problems: list[dict[str, Any]] = []
    for a in anchors:
        raw_name = a.get("name") if isinstance(a, Mapping) else None
        name = clean_name(raw_name)
        if name is None:
            problems.append({"kind": "invalid_name", "anchor": None})
            results.append({"anchor": None, "mentions": [], "reason": "invalid_name", "terms": [],
                            "found_articles": 0, "found_truncated": False, "coverage_note": COVERAGE_NOTE})  # fmt: skip
            continue
        terms, cands, truncated = find_candidates(index, name)
        # 주입 판정을 통과한 기록만 후보로 남긴 뒤 고른다(제외된 기록 때문에 자리가 비지 않게)
        clean: list[Candidate] = []
        excluded = 0
        for c in cands:
            m = build_mention(c, terms)
            blocked = next((b for s in _strings(m) if (b := screen(s, c.chunk.source_id))), None)
            if blocked:
                excluded += 1
                problems.append({"kind": "excluded_by_screen", "anchor": name, "article_id": c.article_id,
                                 "verdict": blocked.verdict, "rules": list(blocked.rules)})  # fmt: skip
            else:
                clean.append(c)
        picked = select(clean, limit)
        mentions = [build_mention(c, terms) for c in picked]
        reason = None if mentions else ("excluded_by_screen" if excluded else "no_match")
        res = AnchorResult(name, terms, len(cands), truncated, tuple(picked))
        results.append({
            "anchor": _anchor_echo(a, name),
            "mentions": mentions,
            "reason": reason,
            "terms": list(res.terms),
            "found_articles": res.found_articles,
            "found_truncated": res.truncated,  # True 면 found_articles 는 '최소'다(검색 상한)
            "coverage_note": COVERAGE_NOTE,
        })  # fmt: skip
    return {"schema": SCHEMA, "anchors": results, "problems": problems}


def to_card(anchor: Mapping[str, Any], mention: Mapping[str, Any]) -> dict[str, Any]:
    """언급 기록 하나를 frontend story 카드 모양으로. 지어내지 않고, 채우지 못한 필드는 missing 에 적는다.

    narration(몰입 층)은 이야기 문장 작성(LLM) 단계의 몫이라 항상 비어 있다 → card_ready 는 이번 범위에서 항상 False.
    """
    name = clean_name(anchor.get("name")) or ""
    lat, lng = anchor.get("lat"), anchor.get("lng")
    has_geo = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (lat, lng))
    geometry = (
        {"type": "point", "coords": [[float(lat), float(lng)]], "basis": "일정 앵커 좌표(입력값)"}
        if has_geo
        else None
    )
    missing = ["narration"]
    if geometry is None:
        missing.append("geometry")
    card = {
        "id": f"story_{mention['article_id']}",
        "kind": "story",
        "title": name,
        "body": mention["title_summary"],  # 한국사DB 한글 요약(원문 아님)
        "geometry": geometry,
        "badge": "기록",  # 기존 딱지 중 가장 가까운 것 — 확정은 사람이 정한다(보고서 참고)
        "sources": [dict(mention["source"])],
        "user_state": "proposed",
        "why_fits": [],
        "caveats": [
            "국역 없음 — 출처 구절은 한문 원문이다",
            "본문 제목은 한국사DB 한글 요약이다(원문 아님)",
        ],
        "rejected": [],
        "narration": None,
    }
    return {"card_ready": False, "missing": missing, "card": card}
