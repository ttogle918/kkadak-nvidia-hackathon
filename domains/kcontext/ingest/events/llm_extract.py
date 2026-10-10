"""검색 후보 본문 → 행사 JSON 을 뽑는 LLM 추출기 조립 (D12, T223). 호스트 전용(D1·D5).

``extract_events`` 가 요구하는 ``Extractor``(본문 → 항목 목록)만 만든다. quote 검증·날짜 규칙·주입 차단은
``extract.py`` 가 한다 — 여기서 우회하지 않는다. 모델 출력은 신뢰하지 않는 입력이고, 형식이 틀리면 예외를 던져
그 후보만 버려진다. 모델은 deploy/llm.chat.yaml 의 ``chat`` 설정을 재사용한다(env ``CHAT_MODEL`` 로 덮어쓴다).
키는 ``core.llm.envfile`` 의 허용 목록 로더로만 읽는다.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path

from core.audit import AuditLog, MemorySink
from core.llm import (
    FeatureConfig,
    HttpxTransport,
    LlmClient,
    LlmConfig,
    default_dotenv_path,
    load_config,
    resolve_env,
)
from domains.kcontext.paths import repo_root

from .extract import Extractor, build_messages, parse_extraction
from .web import Candidate

__all__ = ["make_extractor_factory"]

FEATURE = "chat"  # 전용 feature 를 config 에 더하지 않고 chat 설정을 재사용한다
MAX_TOKENS = 8192  # reasoning 모델은 추론에 토큰을 쓰고, 행사가 여럿이면 JSON 도 길다
RETRIES = 1  # 형식 오류(빈 응답·JSON 아님)만 한 번 더. 호출 오류는 재시도하지 않는다


def _parse(text: str) -> list[dict]:
    """코드 울타리는 parse_extraction 이 벗긴다. 앞뒤에 설명이 붙은 경우만 첫 '[' ~ 마지막 ']' 로 한 번 더 본다."""
    try:
        return parse_extraction(text)
    except ValueError:
        i, j = text.find("["), text.rfind("]")
        if 0 <= i < j:
            return parse_extraction(text[i : j + 1])
        raise


def make_extractor_factory(
    *,
    client: LlmClient | None = None,
    config_path: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Callable[[Candidate], Extractor]:
    """``extractor_for(candidate)`` 를 만든다. 설정·키 문제는 여기서(첫 호출 전에) 예외로 드러난다."""
    if client is None:
        root = repo_root()
        env = resolve_env(default_dotenv_path(root, environ=environ), environ=environ)
        cfg = load_config(config_path or root / "deploy" / "llm.chat.yaml", env)
        model = ((environ if environ is not None else os.environ).get("CHAT_MODEL") or "").strip()
        if model:
            fc = cfg.features[FEATURE]
            cfg = LlmConfig(
                providers=cfg.providers,
                features={**cfg.features, FEATURE: FeatureConfig(FEATURE, fc.provider, model)},
            )
        audit = AuditLog(MemorySink(), run_id=f"web-extract-{uuid.uuid4().hex[:8]}",
                         actor="kcontext:web-extract")
        client = LlmClient(cfg, HttpxTransport(max_tokens=MAX_TOKENS), audit, env=env)
    llm = client

    def extractor_for(_c: Candidate) -> Extractor:
        def extract(content: str) -> list[dict]:
            msgs = build_messages(content)
            last: Exception | None = None
            for _ in range(RETRIES + 1):
                text = asyncio.run(llm.complete(FEATURE, msgs))
                try:
                    return _parse(text)
                except ValueError as e:  # JSON 아님·배열 아님·빈 응답
                    last = e
            raise ValueError("모델 응답 형식 오류") from last

        return extract

    return extractor_for
