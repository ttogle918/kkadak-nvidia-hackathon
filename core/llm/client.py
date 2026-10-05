"""LlmClient — feature → provider·model 라우팅, provider 별 Semaphore, 키 풀, audit.

실제 HTTP 전송은 구현하지 않는다(Transport 프로토콜만). 게이트웨이 연결은 문서 확인 후(D5).
audit 에는 모델명·메시지 수·키의 env 변수 이름만 남기고 본문·키 값은 넣지 않는다.
"""

from __future__ import annotations

import asyncio
import os
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from core.audit import AuditLog
from core.llm.config import (
    LlmConfig,
    LlmError,
    ProviderConfig,
    UnknownFeature,
    resolve_keys,
)
from core.llm.pool import KeyLease, KeyPool

__all__ = ["LlmCallError", "LlmClient", "Message", "Transport", "TransportResponse"]

Message = Mapping[str, str]


class LlmCallError(LlmError):
    pass


@dataclass(frozen=True)
class TransportResponse:
    status: int
    text: str = ""


class Transport(Protocol):
    async def send(
        self,
        *,
        provider: ProviderConfig,
        model: str,
        api_key: str,
        messages: Sequence[Message],
    ) -> TransportResponse: ...


def _cools_down(status: int) -> bool:
    return status == 429 or 500 <= status <= 599


def _check_messages(messages: Sequence[Message]) -> None:
    if isinstance(messages, (str, bytes)) or not isinstance(messages, Sequence) or not messages:
        raise ValueError("messages 는 비어 있지 않은 목록이어야 한다")
    for m in messages:
        if not isinstance(m, Mapping) or not isinstance(m.get("role"), str):
            raise ValueError("각 message 는 role(str)이 있는 매핑이어야 한다")  # noqa: TRY004
        if not isinstance(m.get("content"), str):
            raise ValueError("각 message 는 content(str)가 있어야 한다")  # noqa: TRY004


class LlmClient:
    def __init__(
        self,
        config: LlmConfig,
        transport: Transport,
        audit: AuditLog,
        *,
        env: Mapping[str, str] | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._config = config
        self._transport = transport
        self._audit = audit
        src = os.environ if env is None else env
        self._pools: dict[str, KeyPool] = {}
        self._sems: dict[str, asyncio.Semaphore] = {}
        for name, p in config.providers.items():
            self._pools[name] = KeyPool(
                resolve_keys(p, src),
                cooldown_s=p.cooldown_s,
                timeout_s=p.timeout_s,
                clock=clock,
                sleep=sleep,
            )
            self._sems[name] = asyncio.Semaphore(p.max_concurrency)

    async def complete(self, feature: str, messages: Sequence[Message]) -> str:
        fc = self._config.features.get(feature)
        if fc is None:
            raise UnknownFeature(f"알 수 없는 feature: {feature!r}")
        _check_messages(messages)
        provider = self._config.providers[fc.provider]
        pool = self._pools[fc.provider]
        async with self._sems[fc.provider]:
            call_id = self._audit.call(
                f"llm:{feature}", {"model": fc.model, "messages": len(messages)}
            )
            try:
                text = await self._call(provider, pool, fc.model, messages)
            except BaseException as exc:
                self._audit.error(call_id, exc)
                raise
            self._audit.result(call_id, {"chars": len(text)})
            return text

    async def _call(
        self,
        provider: ProviderConfig,
        pool: KeyPool,
        model: str,
        messages: Sequence[Message],
    ) -> str:
        last = "응답 없음"
        for _ in provider.api_key_envs:  # 키 수만큼만 시도한다(재시도 정책 고도화는 범위 밖)
            lease: KeyLease = await pool.acquire()
            try:
                resp = await self._transport.send(
                    provider=provider, model=model, api_key=lease.value, messages=messages
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - transport 구현이 무엇을 던지든 같은 정책
                # 원 예외 메시지에 키가 섞일 수 있어 타입 이름만 쓴다.
                pool.cool_down(lease.name)
                raise LlmCallError(f"transport 오류 {type(exc).__name__} (키 {lease.name})") from None
            if 200 <= resp.status < 300:
                return resp.text
            if _cools_down(resp.status):
                pool.cool_down(lease.name)
                last = f"status {resp.status} (키 {lease.name})"
                continue
            raise LlmCallError(f"status {resp.status} (키 {lease.name})")
        raise LlmCallError(f"모든 키 시도 실패: {last}")
