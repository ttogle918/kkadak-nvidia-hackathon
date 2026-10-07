"""외부 텍스트의 주입 차단. 새 규칙을 만들지 않고 ``core.guard.scan`` 결과를 그대로 옮긴다."""

from __future__ import annotations

from core.guard import Verdict, scan
from domains.kcontext.contract.records import Blocked

__all__ = ["InjectionBlocked", "screen"]


class InjectionBlocked(Exception):
    """주입으로 판정된 텍스트를 쓰려 할 때 던진다. 클래스 이름이 audit error_type 이 된다."""


def screen(text: str, source_id: str) -> Blocked | None:
    """CLEAN → None · SUSPICIOUS → Blocked("suspicious") · INJECTION → Blocked("injection").

    ``rules`` 는 걸린 규칙 id 를 발견 순서대로(중복 제거) 담는다. 본문은 담지 않는다.
    """
    result = scan(text)
    if result.verdict is Verdict.CLEAN:
        return None
    rules = tuple(dict.fromkeys(f.rule_id for f in result.findings))
    kind = "injection" if result.verdict is Verdict.INJECTION else "suspicious"
    return Blocked(source_id, kind, rules)
