"""일정 글 → 앵커별 실록 언급 → OUT/bundle.json. 호스트 에이전트 프로세스 전용(D1·D10).

    python -m domains.kcontext.pipeline --text-file F [--trip-from YYYY-MM-DD --trip-to YYYY-MM-DD] \
        --db PATH --out DIR [--limit N] [--force] [--llm-budget-s 75] [--require-llm]

env: KC_SCHEDULE_CACHE=on|off(기본 on) · KC_SCHEDULE_RETRY_UNVERIFIED=on|off(기본 off) · KC_SCHEDULE_RETRY_PARTIAL=on|off(기본 on) · KC_VAR_DIR.

표준출력은 요약 한 줄 JSON 뿐. 종료 코드: 0 묶음을 썼다(앵커가 0개면 status=no_anchors) · 2 실행 조건 미충족.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from core import llm as core_llm
from core.llm import LlmError
from domains.kcontext.paths import repo_root
from domains.kcontext.places import PlacesConfigError, load_places
from domains.kcontext.schedule import ScheduleCache, key_for
from domains.kcontext.schedule.__main__ import (
    FALLBACK_FEATURE,
    FEATURE,
    _make_complete,
    make_lazy_complete,
)
from domains.kcontext.schedule.cache import cache_enabled, default_root
from domains.kcontext.schedule.understand import MAX_TEXT_CHARS
from domains.kcontext.story.finder import DEFAULT_LIMIT

from .run import BundleExistsError, run_story_pipeline, summarize, write_bundle


def _fail(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 2


DEFAULT_ATTEMPT_TIMEOUT_S = 45.0  # §6.4 기본 T_llm — 설정을 못 읽으면 이 값으로 판단한다(fail-closed)


def _attempt_timeout_s() -> float:
    """schedule(없으면 chat) feature provider 의 timeout_s. 읽을 수 없으면 기본 45초."""
    try:
        cfg = core_llm.load_config(repo_root() / "deploy" / "llm.chat.yaml", None, check_keys=False)
        fc = cfg.features.get(FEATURE) or cfg.features[FALLBACK_FEATURE]
        return float(cfg.providers[fc.provider].timeout_s)
    except Exception:  # noqa: BLE001 - 설정 문제는 보수적인 기본값으로
        return DEFAULT_ATTEMPT_TIMEOUT_S


def _key_wait_of(complete):
    """complete 가 노출한 키 쿨다운 대기 함수(없으면 None = 대기 없음으로 본다). 파이프라인에는 명시 인자로 넘긴다."""
    fn = getattr(complete, "key_wait_s", None)
    return fn if callable(fn) else None


def _on(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("on", "1", "true", "yes")


def _env_off(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("off", "0", "false", "no")


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m domains.kcontext.pipeline")
    ap.add_argument("--text-file", type=Path, required=True)
    ap.add_argument("--trip-from")
    ap.add_argument("--trip-to")
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    ap.add_argument("--force", action="store_true", help="OUT/bundle.json 이 있으면 교체")
    ap.add_argument("--llm-budget-s", type=float, default=75.0, help="일정 이해 LLM 총 예산(초)")
    ap.add_argument("--require-llm", action="store_true", help="키·설정이 없으면 시작 때 종료 2")
    a = ap.parse_args(argv)
    if bool(a.trip_from) != bool(a.trip_to):
        return _fail("--trip-from 과 --trip-to 는 함께 줘야 한다")
    try:
        text = a.text_file.read_text(encoding="utf-8")
    except (OSError, ValueError) as e:
        return _fail(f"{a.text_file.name}: 읽을 수 없다 ({type(e).__name__})")
    if len(text) > MAX_TEXT_CHARS:
        return _fail(f"글이 {MAX_TEXT_CHARS}자를 넘는다")
    if not a.db.is_file():  # LocalIndex 는 없는 파일을 새로 만든다 — 막는다
        return _fail("색인 파일이 없다")
    if not a.force and (a.out / "bundle.json").exists():
        return _fail("OUT/bundle.json 이 이미 있다 (--force 로 교체)")
    try:
        book = load_places()
        complete = _make_complete() if a.require_llm else make_lazy_complete(lambda: _make_complete())
    except PlacesConfigError as e:
        return _fail(f"장소 사전 오류: {e}")
    except (LlmError, KeyError) as e:
        return _fail(f"LLM 을 쓸 수 없다(키·설정 확인): {type(e).__name__}")
    trip = (a.trip_from, a.trip_to) if a.trip_from else None
    cache = ScheduleCache(default_root()) if cache_enabled() else None
    try:
        bundle = run_story_pipeline(
            text,
            complete=complete,
            db=a.db,
            trip=trip,
            limit=a.limit,
            places=book,
            budget_s=a.llm_budget_s,
            attempt_timeout_s=_attempt_timeout_s(),
            key_wait=_key_wait_of(complete),
            retry_unverified=_on("KC_SCHEDULE_RETRY_UNVERIFIED"),
            retry_partial=not _env_off("KC_SCHEDULE_RETRY_PARTIAL"),
            cache=cache,
            cache_key=key_for(text, trip) if cache is not None else None,
        )
        write_bundle(bundle, a.out, force=a.force)
    except BundleExistsError as e:
        return _fail(str(e))
    except (ValueError, OSError) as e:
        return _fail(f"실패: {type(e).__name__}: {e}")
    print(json.dumps(summarize(bundle), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
