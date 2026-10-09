"""일정 이해 결과 캐시(D15 ④) — quote 검증을 통과한 결과만, 앵커가 1개 이상일 때만 쓴다.

파일에는 이해 결과 dict 와 meta·생성 시각만 넣는다. 입력 전문은 넣지 않는다. 검증된 quote 조각(≤200자)·문제 메시지는
이해 결과에 포함된다. LLM 원문 응답·키는 넣지 않는다(규칙 1).
키는 해시 하나다: 정규화한 글·여행 기간·프롬프트 해시·LLM 설정 파일 바이트 해시·모델 덮어쓰기 env.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from domains.kcontext.paths import repo_root, var_dir

from .understand import PROMPT_SHA

__all__ = ["CACHE_ENV", "ScheduleCache", "cache_enabled", "default_root", "key_for"]

CACHE_ENV = "KC_SCHEDULE_CACHE"  # on(기본) | off
LLM_CONFIG = Path("deploy") / "llm.chat.yaml"
_KEY = re.compile(r"^[0-9a-f]{64}$")
_VERSION = 2  # 1: 부분 결과(QUOTE_NOT_FOUND)가 들어 있을 수 있었다 — 없음으로 본다


def cache_enabled(env: dict[str, str] | None = None) -> bool:
    return (env if env is not None else os.environ).get(CACHE_ENV, "on").strip().lower() != "off"


def default_root() -> Path:
    return var_dir() / "cache" / "schedule"


def key_for(text: str, trip: tuple[str, str] | None, *, root: Path | None = None) -> str:
    base = root if root is not None else repo_root()
    try:
        cfg_sha = hashlib.sha256((base / LLM_CONFIG).read_bytes()).hexdigest()
    except OSError:
        cfg_sha = ""
    model = (os.environ.get("SCHEDULE_MODEL") or os.environ.get("CHAT_MODEL") or "").strip()
    payload = {
        "text": unicodedata.normalize("NFKC", text),
        "trip": list(trip) if trip else None,
        "prompt_sha": PROMPT_SHA,
        "llm_config_sha": cfg_sha,
        "model": model,
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class ScheduleCache:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else default_root()

    def _path(self, key: str) -> Path:
        if not _KEY.match(key):
            raise ValueError("캐시 키가 올바르지 않다")
        return self.root / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        """``{"result", "meta", "created_at"}``. 없거나 손상이면 None."""
        try:
            raw = json.loads(self._path(key).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(raw, dict) or raw.get("v") != _VERSION:
            return None
        res, meta, at = raw.get("result"), raw.get("meta"), raw.get("created_at")
        if (
            not isinstance(res, dict)
            or not isinstance(res.get("anchors"), list)
            or not isinstance(res.get("free_slots"), list)
            or not isinstance(res.get("problems"), list)
            or not isinstance(meta, dict)
            or not isinstance(at, str)
        ):
            return None
        return {"result": res, "meta": meta, "created_at": at}

    def put(self, key: str, result: dict[str, Any], meta: dict[str, Any]) -> None:
        """임시 파일 + os.replace. 실패하면 OSError."""
        dest = self._path(key)
        self.root.mkdir(parents=True, exist_ok=True)
        body = {
            "v": _VERSION,
            "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "meta": meta,
            "result": result,
        }
        tmp = self.root / f".{key}.{uuid.uuid4().hex[:8]}.tmp"
        try:
            tmp.write_text(json.dumps(body, ensure_ascii=False) + "\n", encoding="utf-8")
            os.replace(tmp, dest)
        finally:
            tmp.unlink(missing_ok=True)
