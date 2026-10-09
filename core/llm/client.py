"""LlmClient — feature → provider·model 라우팅, provider 별 Semaphore, 키 풀, audit.

실제 HTTP 전송은 구현하지 않는다(Transport 프로토콜만). 게이트웨이 연결은 문서 확인 후(D5).
audit 에는 모델명·메시지 수·백엔드(api|local)·키의 env 변수 이름만 남기고 본문·키 값은 넣지 않는다.
"""

from __future__ import annotations

import asyncio
import os
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from core.audit import AuditLog
from core.llm.config import (
    LlmConfig,
    LlmError,
    ProviderConfig,
    UnknownFeature,
    resolve_backend,
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
        base_url: str,
        api_key: str | None,  # local 백엔드에 키가 없으면 None
        messages: Sequence[Message],
        params: Mapping[str, Any] | None = None,  # feature params 가 비어 있지 않을 때만 넘긴다
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
        # 백엔드는 생성 시점에 한 번 정한다(잘못된 값·local_base_url 누락은 여기서 실패).
        self._backends = {n: resolve_backend(n, src) for n in config.features}
        used: dict[str, set[str]] = {n: set() for n in config.providers}
        for fname, fc in config.features.items():
            used[fc.provider].add(self._backends[fname])
        # 키 풀은 (provider, backend) 별로 따로 둔다 — 쿨다운 상태를 공유하지 않는다.
        self._pools: dict[tuple[str, str], KeyPool | None] = {}
        # 세마포어도 (provider, backend) 별 — 느린 local 이 같은 provider 의 api 를 막지 않는다(D5).
        self._sems: dict[tuple[str, str], asyncio.Semaphore] = {}
        for name, p in config.providers.items():
            for backend in used[name] or {"api"}:
                keys = resolve_keys(p, src, backend)
                self._pools[(name, backend)] = (
                    KeyPool(
                        keys,
                        cooldown_s=p.cooldown_s,
                        timeout_s=p.timeout_s,
                        clock=clock,
                        sleep=sleep,
                    )
                    if keys
                    else None
                )
                self._sems[(name, backend)] = asyncio.Semaphore(p.concurrency_for(backend))

    def busy(self, feature: str) -> bool:
        """feature 의 provider 동시 호출 한도가 가득 찼는가(대기 없이 거절하려는 호출자용)."""
        fc = self._config.features.get(feature)
        if fc is None:
            raise UnknownFeature(f"알 수 없는 feature: {feature!r}")
        return self._sems[(fc.provider, self._backends[feature])].locked()

    def key_wait_s(self, feature: str) -> float:
        """feature 호출이 지금 키를 얻기까지 기다릴 초(쿨다운 중이면 >0). 키 풀이 없으면 0."""
        fc = self._config.features.get(feature)
        if fc is None:
            raise UnknownFeature(f"알 수 없는 feature: {feature!r}")
        pool = self._pools[(fc.provider, self._backends[feature])]
        return pool.wait_s() if pool else 0.0

    async def complete(self, feature: str, messages: Sequence[Message]) -> str:
        fc = self._config.features.get(feature)
        if fc is None:
            raise UnknownFeature(f"알 수 없는 feature: {feature!r}")
        _check_messages(messages)
        provider = self._config.providers[fc.provider]
        backend = self._backends[feature]
        pool = self._pools[(fc.provider, backend)]
        async with self._sems[(fc.provider, backend)]:
            args: dict[str, Any] = {
                "model": fc.model,
                "messages": len(messages),
                "backend": backend,
            }
            if fc.params:
                args["params"] = sorted(fc.params)  # 키 이름만(값은 남기지 않는다)
            call_id = self._audit.call(f"llm:{feature}", args)
            try:
                text = await self._call(provider, backend, pool, fc.model, messages, fc.params)
            except BaseException as exc:
                self._audit.error(call_id, exc)
                raise
            self._audit.result(call_id, {"chars": len(text)})
            return text

    async def _call(
        self,
        provider: ProviderConfig,
        backend: str,
        pool: KeyPool | None,
        model: str,
        messages: Sequence[Message],
        params: Mapping[str, Any],
    ) -> str:
        last = "응답 없음"
        base_url = provider.base_url_for(backend)
        # 키 수만큼만 시도한다(재시도 정책 고도화는 범위 밖). 키 없는 local 은 1번.
        for _ in range(len(provider.key_envs_for(backend)) or 1):
            lease: KeyLease | None = await pool.acquire() if pool else None
            kname = lease.name if lease else "없음"
            extra: dict[str, Any] = {"params": params} if params else {}
            try:
                resp = await self._transport.send(
                    provider=provider,
                    model=model,
                    base_url=base_url,
                    api_key=lease.value if lease else None,
                    messages=messages,
                    **extra,
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - transport 구현이 무엇을 던지든 같은 정책
                # 원 예외 메시지에 키가 섞일 수 있어 타입 이름만 쓴다.
                if pool and lease:
                    pool.cool_down(lease.name)
                raise LlmCallError(f"transport 오류 {type(exc).__name__} (키 {kname})") from None
            if 200 <= resp.status < 300:
                return resp.text
            if _cools_down(resp.status):
                if pool and lease:
                    pool.cool_down(lease.name)
                last = f"status {resp.status} (키 {kname})"
                continue
            raise LlmCallError(f"status {resp.status} (키 {kname})")
        raise LlmCallError(f"모든 키 시도 실패: {last}")
