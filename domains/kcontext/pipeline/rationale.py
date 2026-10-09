"""언급 카드 → 근거(``Rationale``). 고정 템플릿 + 데이터 값뿐이다 — LLM 없음, 새 문장 없음(지어내기 금지).

키 ``match``·``pick``·``src``·``scope``. 영어는 고정 번역이고, 데이터 값(이름·구절 위치·날짜 표기 등)은 그대로 둔다.
tone: ``old``(◆ 옛 기록에 관한 것: match·src) · ``now``(● 지금 검색에 관한 것: pick·scope).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from domains.kcontext.story import COVERAGE_NOTE

__all__ = ["COVERAGE_NOTE_EN", "mention_rationale"]

CAP = 300
COVERAGE_NOTE_EN = (
    "The index only holds Sillok articles with some region keywords; absence here does not mean the place "
    "is absent from the Sillok. Search matches characters in the Korean DB summary title (and aliases); "
    "articles lacking the name in the title are missed. The Sillok is original classical Chinese only."
)
_DASH = "—"


def _b(ko: Any, en: Any | None = None) -> dict[str, str]:
    k = str(ko)[:CAP]
    return {"ko": k, "en": (k if en is None else str(en)[:CAP])}


def _row(k: tuple[str, str], v: Any, v_en: Any | None = None) -> dict[str, dict[str, str]]:
    sv = str(v) if str(v) else _DASH
    return {"k": _b(*k), "v": _b(sv, sv if v_en is None else v_en)}


def _yn(flag: bool) -> tuple[str, str]:
    return ("예", "Yes") if flag else ("아니오", "No")


def mention_rationale(card_id: str, row: Mapping[str, Any], mention: Mapping[str, Any], excluded: int) -> dict[str, Any]:
    """``card_id`` 는 ``"mention:<카드 id>"`` 그대로 넣는다. ``row`` 는 앵커별 검색 결과, ``mention`` 은 그 안의 언급 하나."""
    term = str(mention.get("matched_term") or "")
    terms = [str(t) for t in (row.get("terms") or [])]
    in_title = mention.get("matched_in") == "title"
    is_alias = bool(term) and bool(terms) and term != terms[0]
    found = int(row.get("found_articles") or 0)
    trunc = bool(row.get("found_truncated"))
    src = mention.get("source") if isinstance(mention.get("source"), Mapping) else {}
    tier = str(mention.get("tier") or "")
    has_link = bool(mention.get("url"))
    sillok_orig = str(src.get("id") or "").startswith("sillok:") and mention.get("lang") == "orig"

    place_ko, place_en = ("한국사DB 한글 요약 제목", "Korean DB summary title") if in_title else ("원문 본문", "Original text body")
    alias_ko, alias_en = _yn(is_alias)
    trunc_ko, trunc_en = _yn(trunc)
    link_ko, link_en = ("있음", "Yes") if has_link else ("없음", "No")
    more_ko, more_en = (" 이상", "+") if trunc else ("", "")

    if sillok_orig:
        src_chip = (f"◆ 출처 등급 {tier} · 국역 없음", f"◆ Source grade {tier} · no Korean translation")
        src_title = (f"출처 등급 {tier} · 국역 없음", f"Source grade {tier} · no Korean translation")
        src_text = ("출처 구절은 한문 원문입니다. 번역하거나 고치지 않았습니다.",
                    "The source passage is the original classical Chinese, neither translated nor edited.")
    else:
        src_chip = (f"◆ 출처 등급 {tier}", f"◆ Source grade {tier}")
        src_title = (f"출처 등급 {tier}", f"Source grade {tier}")
        src_text = ("출처 구절은 색인에 저장된 글에서 잘라 온 것입니다.", "The source passage is cut from the text stored in the index.")

    chips = [
        {"key": "match", "tone": "old", "label": _b(f"◆ 검색어 일치: {term}", f"◆ Matched term: {term}")},
        {"key": "pick", "tone": "now",
         "label": _b(f"● 후보 {found}건{more_ko} 중 선택", f"● Picked from {found}{more_en} candidates")},
        {"key": "src", "tone": "old",
         "label": _b(*src_chip)},
        {"key": "scope", "tone": "now", "label": _b("● 검색 범위", "● Search scope")},
    ]
    items = {
        "match": {
            "title": _b(f"검색어 일치: {term}", f"Matched term: {term}"),
            "text": _b("글자가 같은 검색어로 찾았습니다. 뜻을 풀이해 찾은 것이 아닙니다.",
                       "Found by matching the characters of the search term, not by interpreting meaning."),
            "rows": [
                _row(("검색어", "Search terms"), ", ".join(terms)),
                _row(("일치 위치", "Matched in"), place_ko, place_en),
                _row(("별칭 여부", "Alias used"), alias_ko, alias_en),
            ],
        },
        "pick": {
            "title": _b(f"후보 {found}건{more_ko} 중 선택", f"Picked from {found}{more_en} candidates"),
            "text": _b("후보 기사 중 점수와 왕대 분포를 보고 골랐습니다. 주입 검사에서 걸린 기록은 뺐습니다.",
                       "Chosen from candidate articles by score and reign spread. Records flagged by the injection screen were left out."),
            "rows": [
                _row(("후보 수", "Candidates"), f"{found}{more_ko}", f"{found}{more_en}"),
                _row(("검색 상한 도달", "Search cap reached"), trunc_ko, trunc_en),
                _row(("주입 검사 제외", "Excluded by screen"), excluded),
            ],
        },
        "src": {
            "title": _b(*src_title),
            "text": _b(*src_text),
            "rows": [
                _row(("출처 이름", "Source name"), src.get("name") or ""),
                _row(("위치", "Locator"), src.get("locator") or mention.get("locator") or ""),
                _row(("날짜 표기", "Date label"), mention.get("date_label") or ""),
                _row(("링크", "Link"), link_ko, link_en),
                _row(("수집일", "Collected"), src.get("collected_at") or ""),
            ],
        },
        "scope": {
            "title": _b("검색 범위", "Search scope"),
            "text": _b(COVERAGE_NOTE, COVERAGE_NOTE_EN),
            "rows": [],
        },
    }
    return {"card_id": card_id, "chips": chips, "items": items}
