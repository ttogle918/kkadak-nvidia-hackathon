"""규칙 기반 프롬프트 주입 판정.

한계: 규칙 기반이라 키릴 등 동형문자 치환·의역은 잡지 못한다(범위 밖).

guard 는 **판정만 한다**. 차단·거부·사람 검토 요청은 호출자가 정한다.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

MAX_SCAN_CHARS = 100_000
_EXCERPT_MAX = 80
_EXCERPT_PAD = 20

_HIDDEN_CLASS = "[\u200b-\u200d\u2060\ufeff\u202a-\u202e\u2066-\u2069]"
_HIDDEN_RE = re.compile(_HIDDEN_CLASS)
_INLINE_WS = re.compile(r"[ \t\r\f\v]+")
_NEWLINES = re.compile(r"\n+")

Severity = Literal["high", "medium"]


class Verdict(StrEnum):
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    INJECTION = "injection"


@dataclass(frozen=True)
class Rule:
    id: str
    pattern: re.Pattern[str]
    severity: Severity
    description: str


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: Severity
    excerpt: str  # 정규화 텍스트에서 일치 부분과 앞뒤, 최대 80자


@dataclass(frozen=True)
class ScanResult:
    verdict: Verdict
    findings: tuple[Finding, ...]


def _r(rule_id: str, severity: Severity, pattern: str, description: str, extra: int = 0) -> Rule:
    return Rule(rule_id, re.compile(pattern, re.IGNORECASE | extra), severity, description)


RULES: tuple[Rule, ...] = (
    _r(
        "ignore_previous_en",
        "high",
        r"\b(ignore|disregard|forget)\b.{0,20}\b(previous|prior|above|earlier|all)\b.{0,20}"
        r"\b(instructions?|prompts?|rules?|messages?)\b",
        "이전 지시를 무시하라는 영어 표현",
    ),
    _r(
        "ignore_previous_ko",
        "high",
        r"(이전|위의?|앞의?|기존)\s*(의\s*)?(모든\s*)?(지시|명령|지침|규칙|프롬프트)\S*\s*(을|를)?"
        r"\s*(무시|잊)",
        "이전 지시를 무시하라는 한국어 표현",
    ),
    _r(
        "role_token",
        "high",
        r"<\|?(im_start|im_end|system|endoftext)\|?>|\[/?inst\]",
        "모델 역할 구분 토큰",
    ),
    _r(
        "role_line_prefix",
        "medium",
        r"(^|\n)\s*(#{1,3}\s*)?(system|assistant)\s*:",
        "줄 머리의 system:/assistant: 접두",
        re.MULTILINE,
    ),
    _r("boundary_break", "high", r"</?\s*untrusted", "신뢰 경계 태그 위조"),
    _r(
        "reveal_secrets",
        "high",
        r"\b(reveal|print|show|repeat|leak)\b.{0,30}\b(system prompt|instructions|api key|password)\b"
        r"|(시스템\s*프롬프트|api\s*키|비밀번호).{0,20}(보여|출력|알려|말해)",
        "시스템 프롬프트·비밀 노출 요구",
    ),
    _r(
        "persona_override",
        "medium",
        r"\b(you are now|from now on,? you|act as|pretend to be)\b|너는 이제|지금부터 너는|역할을 바꿔",
        "역할 재지정 시도",
    ),
    _r(
        "tool_steering",
        "medium",
        r"\b(call|invoke|run|execute)\b.{0,20}\b(the )?(tool|function|command)\b"
        r"|(도구|함수|명령)\S*\s*(을|를)?\s*(호출|실행)",
        "도구 호출 유도",
    ),
    _r(
        "approval_steering",
        "medium",
        r"\b(approve|confirm|finali[sz]e)\b.{0,30}\b(draft|request|this)\b"
        r"|(승인|확정)\s*(해|하라|하세요|해라|처리)",
        "사람 승인 게이트를 우회하려는 시도",
    ),
    _r(
        "exfiltration",
        "medium",
        r"\b(send|post|upload|forward)\b.{0,40}(https?://|\bcurl\b|\bwget\b)"
        r"|(전송|보내).{0,40}https?://",
        "외부로 내보내기 유도",
    ),
)


def normalize(text: str) -> str:
    """NFKC → zero-width·bidi 제거 → casefold → 공백 정리(개행은 유지)."""
    t = unicodedata.normalize("NFKC", text)
    t = _HIDDEN_RE.sub("", t)
    t = t.casefold()
    t = _INLINE_WS.sub(" ", t)
    return _NEWLINES.sub("\n", t)


def _excerpt(text: str, start: int, end: int) -> str:
    s = max(0, start - _EXCERPT_PAD)
    e = min(len(text), end + _EXCERPT_PAD)
    return text[s:e][:_EXCERPT_MAX]


def scan(text: str) -> ScanResult:
    findings: list[Finding] = []
    if _HIDDEN_RE.search(text):
        findings.append(Finding("hidden_chars", "medium", "숨은 제어 문자(zero-width·bidi)"))
    if len(text) > MAX_SCAN_CHARS:
        findings.append(Finding("oversize", "medium", f"len>{MAX_SCAN_CHARS}"))
        text = text[:MAX_SCAN_CHARS]
    norm = normalize(text)
    flat = norm.replace("\n", " ")  # 줄바꿈으로 `.{0,N}` 규칙을 피하는 우회 방지
    for rule in RULES:
        m = rule.pattern.search(norm)
        if not m and not (rule.pattern.flags & re.MULTILINE):
            m = rule.pattern.search(flat)
            if m:
                findings.append(Finding(rule.id, rule.severity, _excerpt(flat, m.start(), m.end())))
                continue
        if m:
            findings.append(Finding(rule.id, rule.severity, _excerpt(norm, m.start(), m.end())))
    if any(f.severity == "high" for f in findings):
        verdict = Verdict.INJECTION
    elif findings:
        verdict = Verdict.SUSPICIOUS
    else:
        verdict = Verdict.CLEAN
    return ScanResult(verdict, tuple(findings))
