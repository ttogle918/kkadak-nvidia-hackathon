"""W9 — backend 와 catalog 의 출처 등급 표가 같다(두 곳에 복제돼 있다). 이 테스트만 둘 다 import 한다."""

from backend import chat_story
from domains.kcontext.catalog import cards


def test_tier_tables_are_identical():
    assert chat_story._TIER == cards._TIER
