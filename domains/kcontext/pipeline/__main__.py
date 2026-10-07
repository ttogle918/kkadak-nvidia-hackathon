"""일정 글 → 앵커별 실록 언급 → OUT/bundle.json. 호스트 에이전트 프로세스 전용(D1·D10).

    python -m domains.kcontext.pipeline --text-file F [--trip-from YYYY-MM-DD --trip-to YYYY-MM-DD] \
        --db PATH --out DIR [--limit N] [--force]

표준출력은 요약 한 줄 JSON 뿐. 종료 코드: 0 묶음을 썼다(앵커가 0개면 status=no_anchors) · 2 실행 조건 미충족.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from core.llm import LlmError
from domains.kcontext.places import PlacesConfigError, load_places
from domains.kcontext.schedule.__main__ import _make_complete
from domains.kcontext.schedule.understand import MAX_TEXT_CHARS
from domains.kcontext.story.finder import DEFAULT_LIMIT

from .run import BundleExistsError, run_story_pipeline, summarize, write_bundle


def _fail(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m domains.kcontext.pipeline")
    ap.add_argument("--text-file", type=Path, required=True)
    ap.add_argument("--trip-from")
    ap.add_argument("--trip-to")
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    ap.add_argument("--force", action="store_true", help="OUT/bundle.json 이 있으면 교체")
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
        complete = _make_complete()
    except PlacesConfigError as e:
        return _fail(f"장소 사전 오류: {e}")
    except (LlmError, KeyError) as e:
        return _fail(f"LLM 을 쓸 수 없다(키·설정 확인): {type(e).__name__}")
    try:
        bundle = run_story_pipeline(
            text,
            complete=complete,
            db=a.db,
            trip=(a.trip_from, a.trip_to) if a.trip_from else None,
            limit=a.limit,
            places=book,
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
