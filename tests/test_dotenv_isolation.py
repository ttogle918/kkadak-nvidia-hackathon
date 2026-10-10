"""pytest 중에는 어떤 기본 경로도 레포의 진짜 `.env` 를 읽지 않는다."""

from __future__ import annotations

import os
from pathlib import Path

from backend.settings import REPO_ROOT
from core.llm.envfile import DOTENV_PATH_ENV, default_dotenv_path, resolve_env
from domains.kcontext.catalog.envkeys import key_origin, resolve_catalog_env


def test_default_dotenv_path_is_redirected_away_from_repo():
    p = default_dotenv_path(REPO_ROOT)
    assert p != REPO_ROOT / ".env"
    assert not p.exists()
    assert Path(os.environ[DOTENV_PATH_ENV]) == p


def test_default_path_readers_get_no_keys(monkeypatch):
    for n in ("SEOUL_OPENAPI_KEY", "DATA_GO_KR_SERVICE_KEY", "TAVILY_SEARCH_KEY", "NVIDIA_API_KEY"):
        monkeypatch.delenv(n, raising=False)
    assert resolve_catalog_env() == {}
    assert key_origin("SEOUL_OPENAPI_KEY") == "missing"
    assert "NVIDIA_API_KEY" not in resolve_env(default_dotenv_path(REPO_ROOT))


def test_without_override_the_repo_dotenv_is_the_default(monkeypatch):
    monkeypatch.delenv(DOTENV_PATH_ENV, raising=False)  # 덮어쓰기가 정말 없을 때(경로만 계산, 읽지 않음)
    assert default_dotenv_path(REPO_ROOT, environ={}) == REPO_ROOT / ".env"


def test_partial_environ_mapping_still_honors_process_override():
    """호출자가 APP_DOTENV_PATH 없는 매핑을 넘겨도 프로세스 env 의 덮어쓰기를 따른다(레포 .env 로 새지 않음)."""
    p = default_dotenv_path(REPO_ROOT, environ={})
    assert p != REPO_ROOT / ".env" and not p.exists()
