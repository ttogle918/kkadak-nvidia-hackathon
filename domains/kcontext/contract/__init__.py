"""공통 계약 — 카드·경로·출처·판정·상황 검증기와 파이프라인 내부 레코드(AGENT_CONTEXT 3.3·6장).

검증기는 던지지 않고 문제 목록(list[str])을 돌려준다. 던지는 것은 ``ensure_valid`` 뿐이다.
"""

from .card import (
    GEOMETRY_TYPES,
    KINDS,
    NOW_BADGES,
    REJECT_REASONS,
    STORY_BADGES,
    USER_STATES,
    validate_card,
)
from .errors import ContractError, ensure_valid
from .records import (
    EVENT_CATEGORIES,
    Blocked,
    EventRecord,
    Evidence,
    Rejection,
    SourceRef,
    StoryClaim,
    StoryRecord,
    event_from_dict,
    story_from_dict,
)
from .route import ROUTE_BADGES, validate_route
from .situation import ANCHOR_TYPES, validate_situation
from .source import TIERS, source_tag, validate_source
from .text import Text, is_text, pick
from .verdict import CONFIDENCE, STANCES, VERDICTS, validate_verdict

__all__ = [
    "ANCHOR_TYPES",
    "CONFIDENCE",
    "EVENT_CATEGORIES",
    "GEOMETRY_TYPES",
    "KINDS",
    "NOW_BADGES",
    "REJECT_REASONS",
    "ROUTE_BADGES",
    "STANCES",
    "STORY_BADGES",
    "TIERS",
    "USER_STATES",
    "VERDICTS",
    "Blocked",
    "ContractError",
    "EventRecord",
    "Evidence",
    "Rejection",
    "SourceRef",
    "StoryClaim",
    "StoryRecord",
    "Text",
    "ensure_valid",
    "event_from_dict",
    "is_text",
    "pick",
    "source_tag",
    "story_from_dict",
    "validate_card",
    "validate_route",
    "validate_situation",
    "validate_source",
    "validate_verdict",
]
