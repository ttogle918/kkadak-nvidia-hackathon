"""일정 이해 모듈 — 자유형 일정 글 → anchors·free_slots·problems (순수 함수, LLM 은 주입)."""

from .understand import MAX_TEXT_CHARS, understand

__all__ = ["MAX_TEXT_CHARS", "understand"]
