"""호스트 전용 키 로더. 셸 env 가 우선, 없으면 `.env` 에서 허용 목록 이름만 읽는다.

`.env` 에는 이 프로젝트와 무관한 비밀이 섞여 있을 수 있어 허용 밖 이름은 값을 보관하지 않고
os.environ 에도 올리지 않는다. 파서는 `KEY=VALUE`·따옴표·주석·빈 줄만 다루는 최소판이다.
샌드박스 안에서는 쓰지 않는다(D1) — 거기서는 inference.local 만 부른다.
"""

from __future__ import annotations

import os
from collections.abc import Collection, Mapping
from pathlib import Path

__all__ = ["ALLOWED_KEY_NAMES", "DOTENV_PATH_ENV", "default_dotenv_path", "load_allowed_keys", "resolve_env"]

DOTENV_PATH_ENV = "APP_DOTENV_PATH"  # 기본 `.env` 경로를 바꾼다(경로라 비밀이 아니다). 테스트는 존재하지 않는 경로로 돌린다.

ALLOWED_KEY_NAMES = ("NVIDIA_API_KEY", "NVIDIA_API_KEY_A", "NVIDIA_API_KEY_B")


def default_dotenv_path(repo_root: str | Path, *, environ: Mapping[str, str] | None = None) -> Path:
    """기본 `.env` 경로. env ``APP_DOTENV_PATH`` 가 있으면 그것, 없으면 ``<repo_root>/.env``.

    ``environ`` 에 없으면 프로세스 env 도 본다 — 호출자가 일부만 담은 매핑을 넘겨도 덮어쓰기(테스트 격리)가 빠지지 않게.
    """
    override = ((environ or {}).get(DOTENV_PATH_ENV, "") or os.environ.get(DOTENV_PATH_ENV, "")).strip()
    return Path(override) if override else Path(repo_root) / ".env"


def _unquote(raw: str) -> str:
    v = raw.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    i = v.find(" #")  # 따옴표 없는 값의 줄 끝 주석
    return (v[:i] if i >= 0 else v).strip()


def load_allowed_keys(path: str | Path, allowed: Collection[str] = ALLOWED_KEY_NAMES) -> dict[str, str]:
    """`.env` 에서 allowed 이름의 비어 있지 않은 값만. 파일이 없거나 못 읽으면 빈 dict."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return {}
    out: dict[str, str] = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("export "):
            s = s[len("export ") :].lstrip()
        name, sep, rest = s.partition("=")
        name = name.strip()
        if not sep or name not in allowed:
            continue  # 허용 밖 이름의 값은 쓰지 않고 버린다
        value = _unquote(rest)
        if value:
            out[name] = value
    return out


def resolve_env(
    dotenv_path: str | Path,
    *,
    environ: Mapping[str, str] | None = None,
    allowed: Collection[str] = ALLOWED_KEY_NAMES,
) -> dict[str, str]:
    """LlmClient 에 넘길 env. 허용 키(셸 우선, 없으면 .env) + LLM_BACKEND* 스위치만 담는다."""
    src = os.environ if environ is None else environ
    env = {k: v for k, v in src.items() if k.startswith("LLM_BACKEND")}
    file_keys: dict[str, str] | None = None
    for name in allowed:
        if src.get(name, "").strip():
            env[name] = src[name]
            continue
        if file_keys is None:
            file_keys = load_allowed_keys(dotenv_path, allowed)
        if name in file_keys:
            env[name] = file_keys[name]
    return env
