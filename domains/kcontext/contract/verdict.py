"""판정 객체(AGENT_CONTEXT 6장 "판정 단계의 내부 데이터 형식") 검증기."""

from __future__ import annotations

from collections.abc import Mapping

from .source import TIERS
from .text import is_nonempty_str

VERDICTS = ("accepted", "rejected", "disputed", "unverified")
CONFIDENCE = ("high", "medium", "low")
STANCES = ("support", "contradict")

__all__ = ["CONFIDENCE", "STANCES", "VERDICTS", "validate_verdict"]


def validate_verdict(v: Mapping) -> list[str]:
    if not isinstance(v, Mapping):
        return ["verdict: 객체가 아님"]
    p: list[str] = []
    if not is_nonempty_str(v.get("claim")):
        p.append("verdict.claim: 문자열 필요")
    srcs = v.get("sources")
    if not isinstance(srcs, list):
        p.append("verdict.sources: 배열")
    else:
        for i, s in enumerate(srcs):
            sa = f"verdict.sources[{i}]"
            if not isinstance(s, Mapping):
                p.append(f"{sa}: 객체가 아님")
                continue
            if not is_nonempty_str(s.get("id")):
                p.append(f"{sa}.id")
            if s.get("tier") not in TIERS:
                p.append(f"{sa}.tier: {'/'.join(TIERS)} 중 하나")
            if s.get("date") is not None and not isinstance(s["date"], str):
                p.append(f"{sa}.date: 문자열 또는 null")
            if s.get("stance") not in STANCES:
                p.append(f"{sa}.stance: {'|'.join(STANCES)}")
            if "says" in s and s["says"] is not None and not isinstance(s["says"], str):
                p.append(f"{sa}.says: 문자열")
    if v.get("verdict") not in VERDICTS:
        p.append(f"verdict.verdict: {'|'.join(VERDICTS)}")
    if not is_nonempty_str(v.get("reason")):
        p.append("verdict.reason: 문자열 필요")
    if v.get("confidence") not in CONFIDENCE:
        p.append(f"verdict.confidence: {'|'.join(CONFIDENCE)}")
    return p
