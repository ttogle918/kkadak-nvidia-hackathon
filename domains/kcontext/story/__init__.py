"""앵커 주변 실록 찾기 — LLM 없이 동작하는 '언급 기록(mention)' 단계. 이야기 문장 작성은 이 패키지의 범위 밖이다."""

from domains.kcontext.story.finder import AnchorResult, Candidate, find_candidates, select
from domains.kcontext.story.mention import COVERAGE_NOTE, build_mentions, to_card

__all__ = [
    "COVERAGE_NOTE",
    "AnchorResult",
    "Candidate",
    "build_mentions",
    "find_candidates",
    "select",
    "to_card",
]
