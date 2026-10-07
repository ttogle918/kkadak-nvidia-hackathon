"""출처(sources[]) 검증과 화면 태그. 태그는 ``[등급] 출처 이름 · 위치`` (AGENT_CONTEXT 3.3)."""

from __future__ import annotations

from collections.abc import Mapping

from .text import is_date, is_nonempty_str, is_text, pick

TIERS = ("S", "A", "B", "C", "D")

__all__ = ["TIERS", "source_tag", "validate_source"]


def validate_source(s: Mapping, at: str = "source") -> list[str]:
    if not isinstance(s, Mapping):
        return [f"{at}: 객체가 아님"]
    p: list[str] = []
    for k in ("id", "name", "locator", "collected_at", "quote"):
        if not is_nonempty_str(s.get(k)):
            p.append(f"{at}.{k}: 문자열 필요")
    if s.get("tier") not in TIERS:
        p.append(f"{at}.tier: {'/'.join(TIERS)} 중 하나")
    if is_nonempty_str(s.get("collected_at")) and not is_date(s.get("collected_at")):
        p.append(f"{at}.collected_at: YYYY-MM-DD 형식")
    if not isinstance(s.get("url"), str):
        p.append(f"{at}.url: 문자열 필요(빈 문자열 허용)")
    pub = s.get("published")
    if pub is not None and not isinstance(pub, str):
        p.append(f"{at}.published: 문자열 또는 null")
    bib = s.get("bib")
    if bib is not None and not is_text(bib):
        p.append(f"{at}.bib: 문자열 또는 null")
    return p


def source_tag(s: Mapping, lang: str = "ko") -> str:
    """``[S] 조선왕조실록 · ○○ ○년 ○월 ○일`` 형태. name 이 Text 면 lang 으로 고른다."""
    name = s["name"]
    loc = s["locator"]
    name = pick(name, lang) if not isinstance(name, str) else name
    loc = pick(loc, lang) if not isinstance(loc, str) else loc
    return f"[{s['tier']}] {name} · {loc}"
