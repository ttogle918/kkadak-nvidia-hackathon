"""텍스트 청크 분할과 청크 ID 생성 (표준 라이브러리만)."""

from __future__ import annotations

import hashlib
import re

_PARAGRAPH = re.compile(r"\n\s*\n")
_SENTENCE = re.compile(r"(?<=[.?!。])\s+")


def make_chunk_id(source_id: str, locator: str, text: str) -> str:
    """source_id·locator·text 로 만든 안정적인 16자 16진 ID."""
    raw = f"{source_id}\x00{locator}\x00{text}".encode()
    return hashlib.sha1(raw).hexdigest()[:16]


def _hard_cut(piece: str, max_chars: int) -> list[str]:
    return [piece[i : i + max_chars] for i in range(0, len(piece), max_chars)]


def _split_paragraph(paragraph: str, max_chars: int) -> list[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]
    out: list[str] = []
    current = ""
    for sentence in _SENTENCE.split(paragraph):
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                out.append(current)
                current = ""
            out.extend(_hard_cut(sentence, max_chars))
            continue
        candidate = f"{current} {sentence}" if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
        else:
            out.append(current)
            current = sentence
    if current:
        out.append(current)
    return out


def chunk_text(text: str, *, max_chars: int = 800) -> list[str]:
    """빈 줄 단위 문단 -> 문장 경계 -> 강제 절단 순으로 나눈다. 순서 보존, 빈 청크 없음."""
    if max_chars < 1:
        raise ValueError("max_chars must be >= 1")
    chunks: list[str] = []
    for paragraph in _PARAGRAPH.split(text):
        paragraph = paragraph.strip()
        if paragraph:
            chunks.extend(c for c in _split_paragraph(paragraph, max_chars) if c.strip())
    return chunks
