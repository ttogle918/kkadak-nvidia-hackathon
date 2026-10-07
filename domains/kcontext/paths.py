"""실행 경로. 환경 변수로 바꿀 수 있고, 이 모듈은 디렉터리를 만들지 않는다."""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["data_dir", "repo_root", "var_dir"]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    """env KC_DATA_DIR, 기본 <레포>/domains/kcontext/data."""
    env = os.environ.get("KC_DATA_DIR")
    return Path(env) if env else repo_root() / "domains" / "kcontext" / "data"


def var_dir() -> Path:
    """env KC_VAR_DIR, 기본 <레포>/var (만들지 않는다)."""
    env = os.environ.get("KC_VAR_DIR")
    return Path(env) if env else repo_root() / "var"
