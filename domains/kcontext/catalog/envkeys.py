"""호스트 수집기가 쓰는 키 로더. 셸 env 가 우선이고, 없으면 `.env` 에서 **허용 목록 이름만** 읽는다.

`.env` 에는 이 프로젝트와 무관한 비밀이 섞여 있을 수 있어 허용 밖 이름은 읽지도 보관하지도 않는다
(``core.llm.envfile.load_allowed_keys`` 를 그대로 쓴다). 샌드박스·에이전트 프로세스에서는 쓰지 않는다(D1·D13⑨).
"""

from __future__ import annotations

import os
from collections.abc import Collection, Mapping
from pathlib import Path

from core.llm.envfile import default_dotenv_path, load_allowed_keys
from domains.kcontext.paths import repo_root

__all__ = ["CATALOG_KEY_NAMES", "key_origin", "resolve_catalog_env"]

CATALOG_KEY_NAMES = ("SEOUL_OPENAPI_KEY", "DATA_GO_KR_SERVICE_KEY", "TAVILY_SEARCH_KEY")


def resolve_catalog_env(
    names: Collection[str] = CATALOG_KEY_NAMES,
    *,
    dotenv_path: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """``names`` 에 있는 키만 담은 env. 셸 우선, 없으면 `.env`. 다른 이름은 어느 쪽에서도 가져오지 않는다."""
    src = os.environ if environ is None else environ
    names = [n for n in names if n in CATALOG_KEY_NAMES]  # 호출자가 다른 이름을 넘겨도 카탈로그 키 밖은 찾지 않는다
    out = {n: src[n] for n in names if src.get(n, "").strip()}
    missing = [n for n in names if n not in out]
    if missing and src.get("APP_PROCESS_ROLE") != "agent":  # 에이전트 역할 프로세스는 .env 를 읽지 않는다(D13⑨)
        path = dotenv_path if dotenv_path is not None else default_dotenv_path(repo_root())
        out.update(load_allowed_keys(path, allowed=missing))
    return out


def key_origin(
    name: str, *, dotenv_path: str | Path | None = None, environ: Mapping[str, str] | None = None
) -> str:
    """키가 어디에 있는지 ``"shell" | "dotenv" | "missing"`` (값은 돌려주지 않는다)."""
    if name not in CATALOG_KEY_NAMES:
        return "missing"  # 이 로더는 카탈로그 키 밖의 이름을 찾지 않는다
    src = os.environ if environ is None else environ
    if src.get(name, "").strip():
        return "shell"
    if src.get("APP_PROCESS_ROLE") == "agent":
        return "missing"
    path = dotenv_path if dotenv_path is not None else default_dotenv_path(repo_root())
    return "dotenv" if name in load_allowed_keys(path, allowed=(name,)) else "missing"
