"""httpx 기반 Transport — OpenAI 호환 `POST {base_url}/chat/completions`.

키·Authorization 헤더·응답 본문 전체는 예외 메시지와 반환값에 싣지 않는다(D5).
돌려주는 것은 상태 코드와 첫 choice 의 message.content 뿐이다.
reasoning 모델이 content 를 비우고 reasoning_content 만 채워도 그 추론 과정은 답으로 쓰지 않는다
(사용자에게 사고 과정을 노출하지 않기 위해). 이 경우 text 는 빈 문자열이고 호출자가 실패로 다룬다.
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlsplit

import httpx

from core.llm.client import Message, TransportResponse
from core.llm.config import ProviderConfig

_log = logging.getLogger(__name__)
_FINISH = re.compile(r"[A-Za-z_]{1,32}")

__all__ = ["HttpxTransport", "extract_content"]

DEFAULT_MAX_TOKENS = 2048
# 키가 평문으로 나가면 안 되므로 http 는 루프백·샌드박스 추론 호스트에만 허용한다.
_PLAIN_HTTP_HOSTS = {"localhost", "127.0.0.1", "::1", "inference.local"}


def extract_content(payload: Any) -> str:
    """첫 choice 의 message.content 문자열. 없거나 문자열이 아니면 빈 문자열. 형식 오류는 ValueError."""
    if not isinstance(payload, dict):
        raise ValueError("응답 형식 오류")  # noqa: TRY004
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise ValueError("응답 형식 오류")
    msg = choices[0].get("message")
    if not isinstance(msg, dict):
        raise ValueError("응답 형식 오류")  # noqa: TRY004
    content = msg.get("content")
    return content.strip() if isinstance(content, str) else ""


def _finish_reason(payload: Any) -> str:
    try:
        fr = payload["choices"][0].get("finish_reason")
    except (KeyError, IndexError, TypeError, AttributeError):
        return "?"
    return fr if isinstance(fr, str) and _FINISH.fullmatch(fr) else "?"


def _endpoint(base_url: str) -> str:
    parts = urlsplit(base_url)
    if parts.scheme == "https" or (
        parts.scheme == "http" and (parts.hostname or "") in _PLAIN_HTTP_HOSTS
    ):
        return base_url.rstrip("/") + "/chat/completions"
    raise ValueError("base_url 은 https 여야 한다(루프백·inference.local 만 http 허용)")


class HttpxTransport:
    def __init__(
        self,
        *,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        transport: httpx.AsyncBaseTransport | None = None,  # 테스트용 주입(MockTransport)
    ) -> None:
        self._max_tokens = max_tokens
        self._transport = transport

    async def send(
        self,
        *,
        provider: ProviderConfig,
        model: str,
        base_url: str,
        api_key: str | None,
        messages: Sequence[Message],
    ) -> TransportResponse:
        url = _endpoint(base_url)
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        body = {
            "model": model,
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
            "max_tokens": self._max_tokens,
            "stream": False,
        }
        # httpx timeout 은 읽기 간격 단위라 천천히 계속 보내는 응답은 못 막는다. 전체 시간 상한을 따로 둔다(W7).
        async with (
            asyncio.timeout(provider.timeout_s),
            httpx.AsyncClient(
                timeout=provider.timeout_s, transport=self._transport, follow_redirects=False
            ) as http,
        ):
            resp = await http.post(url, json=body, headers=headers)
        if not 200 <= resp.status_code < 300:
            return TransportResponse(resp.status_code)
        try:
            payload = resp.json()
        except ValueError:
            raise ValueError("응답 JSON 파싱 실패") from None
        text = extract_content(payload)
        if not text:
            # reasoning-only 등 빈 응답의 원인 파악용. finish_reason(짧은 영문 토큰)만 남기고 본문·키는 남기지 않는다(W9).
            _log.warning("LLM 빈 응답 finish_reason=%s", _finish_reason(payload))
        return TransportResponse(resp.status_code, text)
