"""일정 이해 CLI — 실제 LLM 호출은 여기서만 조립한다(호스트 전용, D1·D5).

    python -m domains.kcontext.schedule --text-file F [--trip-from YYYY-MM-DD --trip-to YYYY-MM-DD]

키는 ``core.llm.envfile`` 의 허용 목록 로더로만 읽고, 모델은 env ``SCHEDULE_MODEL``(없으면
``CHAT_MODEL``, 그것도 없으면 deploy/llm.chat.yaml 의 chat 모델)로 정한다. 결과는 JSON 한 덩어리로 stdout.
종료 코드: 0 정상 · 2 실행 조건 미충족(파일·키·설정). 샌드박스 안에서는 쓰지 않는다.
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import os
import sys
import uuid
from collections.abc import Sequence
from pathlib import Path

from core.audit import AuditLog, MemorySink
from core.llm import (
    HttpxTransport,
    LlmClient,
    LlmConfig,
    LlmError,
    load_config,
    resolve_env,
)
from domains.kcontext.paths import repo_root

from .understand import MAX_TEXT_CHARS, CompleteUnavailable, understand

FEATURE = "schedule"  # yaml 에 없으면 chat 설정을 재사용한다(T308 이 schedule feature 를 더한다)
FALLBACK_FEATURE = "chat"
MAX_TOKENS = 4096  # reasoning 모델은 추론에 토큰을 쓰므로 넉넉히


def _fail(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 2


def _make_complete():
    root = repo_root()
    env = resolve_env(root / ".env")
    cfg = load_config(root / "deploy" / "llm.chat.yaml", env)
    feature = FEATURE if FEATURE in cfg.features else FALLBACK_FEATURE
    model = (os.environ.get("SCHEDULE_MODEL") or os.environ.get("CHAT_MODEL") or "").strip()
    if model:
        fc = cfg.features[feature]
        cfg = LlmConfig(
            providers=cfg.providers,
            features={**cfg.features, feature: dataclasses.replace(fc, model=model)},
        )
    run_id = f"schedule-{uuid.uuid4().hex[:8]}"
    audit = AuditLog(MemorySink(), run_id=run_id, actor="kcontext:schedule")
    client = LlmClient(cfg, HttpxTransport(max_tokens=MAX_TOKENS), audit, env=env)

    def complete(system: str, user: str) -> str:
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        return asyncio.run(client.complete(feature, msgs))

    complete.model = cfg.features[feature].model  # type: ignore[attr-defined]
    complete.key_wait_s = lambda: client.key_wait_s(feature)  # type: ignore[attr-defined]
    return complete


def make_lazy_complete(factory=None):
    """첫 호출 때 클라이언트를 만든다. 만들기 실패(키·설정)는 CompleteUnavailable 로 알린다."""
    state: dict = {}

    def complete(system: str, user: str) -> str:
        if "fn" not in state:
            if "err" in state:
                raise CompleteUnavailable(state["err"])
            try:
                state["fn"] = (factory or _make_complete)()
            except Exception as e:
                state["err"] = type(e).__name__
                raise CompleteUnavailable(state["err"]) from e
            complete.model = getattr(state["fn"], "model", None)  # type: ignore[attr-defined]
        return state["fn"](system, user)

    def key_wait_s() -> float:
        """클라이언트가 아직 없으면 쿨다운도 없다(0). 있으면 그 클라이언트의 값."""
        fn = getattr(state.get("fn"), "key_wait_s", None)
        return float(fn()) if callable(fn) else 0.0

    complete.model = None  # type: ignore[attr-defined]
    complete.key_wait_s = key_wait_s  # type: ignore[attr-defined]
    return complete


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m domains.kcontext.schedule")
    ap.add_argument("--text-file", type=Path, required=True)
    ap.add_argument("--trip-from")
    ap.add_argument("--trip-to")
    a = ap.parse_args(argv)
    try:
        text = a.text_file.read_text(encoding="utf-8")
    except (OSError, ValueError) as e:
        return _fail(f"{a.text_file.name}: 읽을 수 없다 ({type(e).__name__})")
    if len(text) > MAX_TEXT_CHARS:
        return _fail(f"글이 {MAX_TEXT_CHARS}자를 넘는다")
    try:
        complete = _make_complete()
    except (LlmError, KeyError) as e:
        return _fail(f"LLM 을 쓸 수 없다(키·설정 확인): {type(e).__name__}")
    out = understand(text, complete=complete, trip_from=a.trip_from, trip_to=a.trip_to)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
