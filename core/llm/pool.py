"""provider 별 키 풀 — 라운드로빈 + 429/5xx 쿨다운. 표준 라이브러리만 쓴다.

시간(clock)·대기(sleep)는 주입한다. 키 값은 KeyLease 안에만 있고 repr 에 나오지 않는다.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field

from core.llm.config import LlmUnavailable

__all__ = ["KeyLease", "KeyPool"]


@dataclass(frozen=True)
class KeyLease:
    name: str  # env 변수 이름 — 로그·audit 에 써도 되는 식별자
    value: str = field(repr=False)


class KeyPool:
    def __init__(
        self,
        keys: Sequence[tuple[str, str]],
        *,
        cooldown_s: float,
        timeout_s: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if not keys:
            raise ValueError("keys 가 비어 있다")
        names = [n for n, _ in keys]
        if len(set(names)) != len(names):
            raise ValueError("키 이름이 중복이다")
        self._keys = list(keys)
        self._cooldown_s = cooldown_s
        self._timeout_s = timeout_s
        self._clock = clock
        self._sleep = sleep
        self._cursor = 0
        self._until: dict[str, float] = {}

    def cool_down(self, name: str, seconds: float | None = None) -> None:
        """name 키를 쉬게 한다. 이미 더 늦게 풀리면 유지한다."""
        if name not in {n for n, _ in self._keys}:
            raise KeyError(name)
        until = self._clock() + (self._cooldown_s if seconds is None else seconds)
        self._until[name] = max(self._until.get(name, 0.0), until)

    def _pick(self, now: float) -> KeyLease | None:
        n = len(self._keys)
        for i in range(n):
            idx = (self._cursor + i) % n
            name, value = self._keys[idx]
            if self._until.get(name, 0.0) <= now:
                self._cursor = (idx + 1) % n
                return KeyLease(name, value)
        return None

    def wait_s(self) -> float:
        """지금 acquire() 하면 키를 얻기까지 기다릴 초. 쓸 수 있는 키가 있으면 0."""
        now = self._clock()
        if any(self._until.get(n, 0.0) <= now for n, _ in self._keys):
            return 0.0
        return max(min(self._until[n] for n, _ in self._keys) - now, 0.0)

    async def acquire(self) -> KeyLease:
        """다음 사용 가능한 키. 전부 쉬는 중이면 가장 빨리 풀리는 때까지 기다린다.

        그 시각이 timeout_s 를 넘으면 LlmUnavailable.
        """
        deadline = self._clock() + self._timeout_s
        while True:
            now = self._clock()
            lease = self._pick(now)
            if lease is not None:
                return lease
            earliest = min(self._until[n] for n, _ in self._keys)
            if earliest > deadline:
                raise LlmUnavailable(f"모든 키가 쉬는 중이다(키 {len(self._keys)}개, 시간 초과)")
            await self._sleep(max(earliest - now, 0.0))
