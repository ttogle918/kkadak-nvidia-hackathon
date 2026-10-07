"""메시지가 '여행 일정 글' 같은지 규칙으로 판별하는 게이트. LLM 없음, 순수 함수.

오탐의 비용은 LLM 한 번(+파이프라인 최대 90초)이라 보수적으로 잡는다:
**시각 또는 날짜 표현 하나 + (일정 어휘 또는 장소 사전의 이름) 하나 이상** 이 함께 있어야 한다.
시각·날짜만 있거나 어휘·장소만 있으면 일반 챗봇으로 간다. 장소 이름은 데이터 파일(``backend/fixtures/chat_places.json``)
에서 읽는다 — backend 는 ``domains`` 를 import 하지 않는다(D3).
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

PLACES_FILE = Path(__file__).resolve().parent / "fixtures" / "chat_places.json"

_TIME = re.compile(
    r"(?<!\d)\d{1,2}\s*시(?![대간장민작내청도설스행점])(?:\s*\d{1,2}\s*분|\s*반)?"  # 10시, 2시 30분, 3시반
    r"|(?<!\d)\d{1,2}:\d{2}(?!\d)"  # 12:30
    r"|(?:오전|오후)\s*\d{1,2}"  # 오후 3
    r"|(?<![\w])\d{1,2}\s*(?:am|pm)\b",
    re.IGNORECASE,
)
_DATE = re.compile(
    r"(?<![\d/.:])\d{1,2}\s*/\s*\d{1,2}(?![\d/:])"  # 10/15
    r"|\d{1,2}\s*월\s*\d{1,2}\s*일"  # 10월 15일
    r"|(?<!\d)\d{1,2}\s*일\s*차"  # 1일차
    r"|\b20\d{2}-\d{2}-\d{2}\b",
)
_VOCAB = re.compile(
    r"갈\s*거|가려고|갈\s*예정|갈\s*계획|가볼\s*(?:거|예정|생각)|들를|들러|방문\s*(?:할|예정)|"
    r"일정|숙소|호텔|체크\s*인|체크\s*아웃|여행\s*계획|"
    r"\bitinerary\b|\bcheck-?in\b|\bcheck-?out\b|\bi(?:'ll| will)\s+(?:visit|go)\b|\bplan(?:ning)? to (?:visit|go)\b",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def _place_names() -> tuple[str, ...]:
    try:
        data = json.loads(PLACES_FILE.read_text(encoding="utf-8"))
        names = data["names"]
        return tuple(n for n in names if isinstance(n, str) and n.strip())
    except (OSError, ValueError, KeyError, TypeError):
        return ()  # 사전이 없으면 장소 신호만 빠지고 어휘 신호는 그대로 쓴다


def looks_like_schedule(text: str) -> bool:
    if not isinstance(text, str):
        return False
    when = bool(_TIME.search(text) or _DATE.search(text))
    if not when:
        return False
    if _VOCAB.search(text):
        return True
    low = text.casefold()
    return any(n.casefold() in low for n in _place_names())
