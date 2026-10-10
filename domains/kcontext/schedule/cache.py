"""일정 이해 결과 캐시(D15 ④) — quote 검증을 통과한 결과만, 앵커가 1개 이상일 때만 쓴다.

파일에는 이해 결과 dict 와 meta·생성 시각만 넣는다. 입력 전문은 넣지 않는다. 검증된 quote 조각(≤200자)·문제 메시지는
이해 결과에 포함된다. LLM 원문 응답·키는 넣지 않는다(규칙 1).
키는 해시 하나다: 정규화한 글·여행 기간·(여행 기간이 없거나 유효하지 않으면) 오늘(KST)·`LLM_BACKEND*` 값·
프롬프트 해시·LLM 설정 파일 바이트 해시·모델 덮어쓰기 env(`SCHEDULE_MODEL`·`CHAT_MODEL`).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from domains.kcontext.paths import repo_root, var_dir

from .understand import MAX_TRIP_DAYS, PROMPT_SHA, _iso_date, kst_today

__all__ = ["CACHE_ENV", "ScheduleCache", "cache_enabled", "default_root", "key_for"]

CACHE_ENV = "KC_SCHEDULE_CACHE"  # on(기본) | off
LLM_CONFIG = Path("deploy") / "llm.chat.yaml"
MAX_FILES_ENV = "KC_SCHEDULE_CACHE_MAX_FILES"  # 기본 500 (D27 ⑦)
MAX_BYTES_ENV = "KC_SCHEDULE_CACHE_MAX_BYTES"  # 기본 32MiB
DEFAULT_MAX_FILES = 500
DEFAULT_MAX_BYTES = 32 * 1024 * 1024
_KEY = re.compile(r"^[0-9a-f]{64}$")
_VERSION = 5  # 5: 키에 LLM_BACKEND*·잘못된 trip 의 today · 4: D22 ② 연도 추정(YEAR_ASSUMED) · 3: D21 시각·조사 · 1: 부분 결과(QUOTE_NOT_FOUND)가 들어 있을 수 있었다 · 2: D21 이전 시각 해석 — 없음으로 본다


def cache_enabled(env: dict[str, str] | None = None) -> bool:
    return (env if env is not None else os.environ).get(CACHE_ENV, "on").strip().lower() != "off"


def default_root() -> Path:
    return var_dir() / "cache" / "schedule"


def _trip_ok(trip: tuple[str, str] | None) -> bool:
    """understand 가 trip 을 쓰는 조건과 같다(형식·from ≤ to·기간 상한). 아니면 trip 없이 해석한다."""
    if not trip:
        return False
    f, t = _iso_date(trip[0] or ""), _iso_date(trip[1] or "")
    return f is not None and t is not None and f <= t and (t - f).days < MAX_TRIP_DAYS


def key_for(text: str, trip: tuple[str, str] | None, *, root: Path | None = None,
            today: date | None = None, env: dict[str, str] | None = None) -> str:
    """trip 이 없거나 쓸 수 없으면 오늘(KST)을 키에 넣는다 — 연도 추정(D22 ②)이 날짜에 따라 달라지기 때문.

    ``env``(None 이면 os.environ)의 ``LLM_BACKEND*`` 이름=값도 키에 넣는다(백엔드가 다르면 결과가 다를 수 있다).
    """
    src = env if env is not None else os.environ
    backend = sorted(f"{k}={v}" for k, v in src.items() if k.startswith("LLM_BACKEND"))
    valid = _trip_ok(trip)
    base = root if root is not None else repo_root()
    try:
        cfg_sha = hashlib.sha256((base / LLM_CONFIG).read_bytes()).hexdigest()
    except OSError:
        cfg_sha = ""
    model = (src.get("SCHEDULE_MODEL") or src.get("CHAT_MODEL") or "").strip()
    payload = {
        "text": unicodedata.normalize("NFKC", text),
        "trip": list(trip) if trip else None,
        "today": None if valid else (today or kst_today()).isoformat(),
        "llm_backend": backend,
        "prompt_sha": PROMPT_SHA,
        "llm_config_sha": cfg_sha,
        "model": model,
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _limit(name: str, default: int) -> int:
    try:
        n = int(os.environ.get(name, ""))
    except ValueError:
        return default
    return n if n > 0 else default


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
        self._prune(keep=dest)

    def _prune(self, *, keep: Path) -> None:
        """개수·바이트 상한을 넘으면 수정 시각이 오래된 것부터 지운다(``keep`` 은 남김). 의미는 그대로 —
        지워진 항목은 다음 조회에서 미적중일 뿐이다(D15 ④). 어떤 OSError 도 put 을 실패시키지 않는다."""
        max_files = _limit(MAX_FILES_ENV, DEFAULT_MAX_FILES)
        max_bytes = _limit(MAX_BYTES_ENV, DEFAULT_MAX_BYTES)
        items: list[tuple[float, str, Path, int]] = []
        try:
            for p in self.root.glob("*.json"):
                if p == keep or not _KEY.match(p.stem):
                    continue
                try:
                    st = p.stat()
                except OSError:
                    continue
                items.append((st.st_mtime, p.name, p, st.st_size))
            try:
                kept_size = keep.stat().st_size
            except OSError:
                kept_size = 0
        except OSError:
            return
        items.sort()  # 오래된 것이 앞
        count = len(items) + 1
        total = sum(i[3] for i in items) + kept_size
        for _, _, p, size in items:
            if count <= max_files and total <= max_bytes:
                break
            try:
                p.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                continue
            count -= 1
            total -= size
