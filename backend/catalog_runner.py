"""행사 카탈로그 계산을 별도 프로세스로 돌린다(D10). backend 는 ``domains`` 를 import 하지 않는다.

``python -m domains.kcontext.catalog.api`` 에 JSON 한 건을 보내고 JSON 한 건을 받는다. 자식 프로세스는
``APP_PROCESS_ROLE=agent`` 로 돌고, 공공데이터 키는 수동 재수집(``admin_refresh``)에만 넘긴다.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_BASE_ENV = ("PATH", "HOME", "LANG", "LC_ALL", "PYTHONPATH", "VIRTUAL_ENV", "KC_TARGET_REGION", "KC_DATA_DIR")
_KEY_ENV = ("SEOUL_OPENAPI_KEY", "DATA_GO_KR_SERVICE_KEY", "TAVILY_SEARCH_KEY")
TIMEOUTS = {"admin_refresh": 180}
DEFAULT_TIMEOUT = 60


class CatalogRunnerError(RuntimeError):
    """자식 프로세스가 죽었거나 JSON 이 아닌 응답을 줬다. 메시지에 출력 본문을 싣지 않는다."""


def run_catalog(catalog_dir: Path | None, op: str, args: dict, actor: str | None = None) -> dict:
    env = {k: os.environ[k] for k in _BASE_ENV if k in os.environ}
    env["APP_PROCESS_ROLE"] = "agent"
    if catalog_dir is not None:
        env["KC_CATALOG_DIR"] = str(catalog_dir)
    if op == "admin_refresh":
        env.update({k: os.environ[k] for k in _KEY_ENV if k in os.environ})
    try:
        p = subprocess.run(
            [sys.executable, "-m", "domains.kcontext.catalog.api"],
            input=json.dumps({"op": op, "args": args, "actor": actor}, ensure_ascii=False),
            text=True, capture_output=True, cwd=REPO_ROOT, env=env, check=False,
            timeout=TIMEOUTS.get(op, DEFAULT_TIMEOUT),
        )
    except subprocess.TimeoutExpired:
        raise CatalogRunnerError("카탈로그 처리 시간이 초과됐다") from None
    if p.returncode != 0:
        raise CatalogRunnerError(f"카탈로그 프로세스 오류 (종료 코드 {p.returncode})")
    try:
        out = json.loads(p.stdout)
    except ValueError:
        raise CatalogRunnerError("카탈로그 응답이 JSON 이 아니다") from None
    if not isinstance(out, dict):
        raise CatalogRunnerError("카탈로그 응답 형식 오류")
    return out
