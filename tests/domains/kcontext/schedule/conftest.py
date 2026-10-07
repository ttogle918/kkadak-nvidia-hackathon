import json

import pytest


class FakeLlm:
    """가짜 complete — 고정 응답을 돌려주고 호출을 기록한다. 네트워크·키 없음."""

    def __init__(self, reply):
        self.reply = reply
        self.calls: list[tuple[str, str]] = []

    def __call__(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if isinstance(self.reply, Exception):
            raise self.reply
        if self.reply is None or isinstance(self.reply, str):
            return self.reply
        return json.dumps(self.reply, ensure_ascii=False)


@pytest.fixture
def fake():
    return FakeLlm
