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

from core.llm.envfile import default_dotenv_path, load_allowed_keys

REPO_ROOT = Path(__file__).resolve().parents[1]
_BASE_ENV = ("PATH", "HOME", "LANG", "LC_ALL", "PYTHONPATH", "VIRTUAL_ENV", "KC_TARGET_REGION", "KC_DATA_DIR",
             "KC_ROUTE_PROVIDER", "KC_OSM_ROUTER_URL")  # 마지막 둘은 비밀이 아닌 경로 설정
# 수동 재수집에는 그 출처가 쓰는 키 하나만 넘긴다(다른 출처의 키·추론 키는 넘기지 않는다, D13 ⑨).
# web_source 출처(junggu_site·gangnam_site 등)의 카탈로그 반영은 로컬 JSONL 만 읽고 검색·LLM 을 부르지 않으므로
# 키를 넘기지 않는다 — 검색 수집기(web_run)는 호스트에서 사람이 따로 돌린다.
_SOURCE_KEYS = {
    "seoul_openapi": ("SEOUL_OPENAPI_KEY",),
    "tourapi_kto": ("DATA_GO_KR_SERVICE_KEY",),
}
TIMEOUTS = {"admin_refresh": 180}
DEFAULT_TIMEOUT = 60


class CatalogRunnerError(RuntimeError):
    """자식 프로세스가 죽었거나 JSON 이 아닌 응답을 줬다. 메시지에 출력 본문을 싣지 않는다."""


def run_catalog(catalog_dir: Path | None, op: str, args: dict, actor: str | None = None,
                *, timeout_s: float | None = None) -> dict:
    """``timeout_s`` 가 있으면 기본 한도보다 짧게만 줄인다(채팅 시간 예산용)."""
    env = {k: os.environ[k] for k in _BASE_ENV if k in os.environ}
    env["APP_PROCESS_ROLE"] = "agent"
    if catalog_dir is not None:
        env["KC_CATALOG_DIR"] = str(catalog_dir)
    if op == "admin_refresh":
        # 그 출처의 키 하나만, 이 프로세스(backend)가 셸 env 에서 — 없으면 `.env` 의 허용 목록 이름에서 — 골라 넘긴다.
        # 자식(APP_PROCESS_ROLE=agent)은 `.env` 를 읽지 않는다. 허용 밖 이름은 읽지도 않는다.
        wanted = _SOURCE_KEYS.get(str(args.get("source_id")), ())
        missing = [k for k in wanted if not os.environ.get(k, "").strip()]
        dotenv = load_allowed_keys(default_dotenv_path(REPO_ROOT), allowed=missing) if missing else {}
        for k in wanted:
            v = os.environ.get(k, "").strip() and os.environ[k] or dotenv.get(k)
            if v:
                env[k] = v
    try:
        p = subprocess.run(
            [sys.executable, "-m", "domains.kcontext.catalog.api"],
            input=json.dumps({"op": op, "args": args, "actor": actor}, ensure_ascii=False),
            text=True, capture_output=True, cwd=REPO_ROOT, env=env, check=False,
            timeout=min(TIMEOUTS.get(op, DEFAULT_TIMEOUT), timeout_s) if timeout_s else TIMEOUTS.get(op, DEFAULT_TIMEOUT),
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
