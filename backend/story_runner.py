"""일정 → 실록 언급 파이프라인을 별도 프로세스로 돌린다(D10). backend 는 ``domains`` 를 import 하지 않는다.

``python -m domains.kcontext.pipeline`` 은 호스트 에이전트 프로세스(``APP_PROCESS_ROLE=agent``)로 돌고
OUT/bundle.json 한 파일만 쓴다. 이 모듈은 그 파일을 크기 상한 안에서 읽고 schema 를 확인해 돌려준다.
실패하면 ``StoryRunnerError(kind)`` 하나만 올린다 — 자식의 출력·경로·본문은 메시지에 싣지 않는다.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_SCHEMA = "kc-chat-bundle/v1"
TIMEOUT_S = 90
MAX_BUNDLE_BYTES = 1024 * 1024
# 자식에게 넘기는 env 허용 목록. 나머지(관리자 토큰·다른 키 등)는 넘기지 않는다.
# LLM 키는 이 이름들만. .env 는 자식이 core.llm 허용 목록 로더로 직접 읽는다.
_ENV_ALLOW = (
    "PATH", "HOME", "LANG", "LC_ALL", "PYTHONPATH", "VIRTUAL_ENV",
    "NVIDIA_API_KEY", "NVIDIA_API_KEY_A", "NVIDIA_API_KEY_B", "CHAT_MODEL", "SCHEDULE_MODEL",
    "KC_TARGET_REGION", "KC_DATA_DIR",
)


def _base_cmd() -> list[str]:
    return [sys.executable, "-m", "domains.kcontext.pipeline"]


class StoryRunnerError(RuntimeError):
    """kind 만 담는다: timeout · exit · no_output · too_large · bad_json · bad_schema · spawn."""

    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        self.kind = kind


def _child_env() -> dict[str, str]:
    env = {k: os.environ[k] for k in _ENV_ALLOW if k in os.environ}
    env.update({k: v for k, v in os.environ.items() if k.startswith("LLM_BACKEND")})
    env["APP_PROCESS_ROLE"] = "agent"
    return env


def run_story(text: str, trip: tuple[str, str] | None, db: Path, *, timeout: int = TIMEOUT_S) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="kc_story_"))
    try:
        src = tmp / "text.txt"
        src.write_text(text, encoding="utf-8")
        out = tmp / "out"
        cmd = [*_base_cmd(), "--text-file", str(src), "--db", str(db), "--out", str(out)]
        if trip:
            cmd += ["--trip-from", trip[0], "--trip-to", trip[1]]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, env=_child_env(),
                               check=False, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise StoryRunnerError("timeout") from None
        except OSError:
            raise StoryRunnerError("spawn") from None
        if p.returncode != 0:
            raise StoryRunnerError("exit")
        f = out / "bundle.json"
        try:
            if f.is_symlink() or not f.is_file():
                raise StoryRunnerError("no_output")
            if f.stat().st_size > MAX_BUNDLE_BYTES:
                raise StoryRunnerError("too_large")
            raw = f.read_bytes()[: MAX_BUNDLE_BYTES + 1]
        except OSError:
            raise StoryRunnerError("no_output") from None
        if len(raw) > MAX_BUNDLE_BYTES:
            raise StoryRunnerError("too_large")
        try:
            bundle = json.loads(raw)
        except ValueError:
            raise StoryRunnerError("bad_json") from None
        if not isinstance(bundle, dict) or bundle.get("schema") != BUNDLE_SCHEMA:
            raise StoryRunnerError("bad_schema")
        return bundle
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
