"""서울 API(culturalEventInfo) 전체 행 수 측정(T408). 행 원문·키는 저장·출력하지 않는다.

    uv run python scripts/measure_seoul_rows.py --today YYYY-MM-DD [--max-pages 60]            # 기본: 1행만 요청(호출 1회)
    uv run python scripts/measure_seoul_rows.py --today YYYY-MM-DD --full [--max-pages 60]     # 전체 쪽 수집 통계(호출 = 쪽 수)

기본(probe)은 ``list_total_count`` 와 쪽 상한(max_pages × 1000) 비교만 낸다. ``--full`` 은 ``seoul.fetch_rows`` 로 전부
가져와 구별·끝나지 않은 행·좌표 통계를 낸다(실호출이 늘어난다 — 호출 상한이 있는 측정에서는 쓰지 않는다).
키 이름은 ``SEOUL_OPENAPI_KEY`` 하나만, ``core.llm.envfile`` 허용 목록 로더로 읽는다. 키가 없으면 종료 2.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from core.llm.envfile import default_dotenv_path, load_allowed_keys
from domains.kcontext.catalog.seoul import KEY_ENV, PAGE, SeoulApiError, fetch_rows


def _key() -> str:
    v = os.environ.get(KEY_ENV, "").strip()
    return v or load_allowed_keys(default_dotenv_path(REPO_ROOT), allowed=(KEY_ENV,)).get(KEY_ENV, "")


def _stats(rows: list[dict], today: str) -> dict:
    by_gu = Counter(str(r.get("GUNAME") or "").strip() for r in rows)
    no_gu = by_gu.pop("", 0)
    ll = [r for r in rows if _f(r.get("LAT")) and _f(r.get("LOT"))]
    places = {(str(r.get("PLACE") or "").strip(), str(r.get("GUNAME") or "").strip()) for r in ll}
    return {
        "by_guname": dict(by_gu.most_common()),
        "no_guname": no_gu,
        "not_ended_by_end_date": sum(1 for r in rows if str(r.get("END_DATE") or "")[:10] >= today),
        "with_latlng": len(ll),
        "distinct_place_with_latlng": len(places),
    }


def _f(v: object) -> float:
    try:
        return float(str(v))
    except (TypeError, ValueError):
        return 0.0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", required=True)
    ap.add_argument("--max-pages", type=int, default=60)
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args(argv)
    key = _key()
    if not key:
        print(f"{KEY_ENV} 가 없다", file=sys.stderr)
        return 2
    try:
        if not a.full:
            rows, total = fetch_rows(key, page_size=1, max_pages=1)
            out = {"list_total_count": total, "fetched": len(rows), "pages": 1,
                   "truncated": total > a.max_pages * PAGE, "max_rows": a.max_pages * PAGE,
                   "mode": "probe(1행)"}
        else:
            rows, total = fetch_rows(key, max_pages=a.max_pages)
            out = {"list_total_count": total, "fetched": len(rows), "pages": -(-len(rows) // PAGE),
                   "truncated": len(rows) < total, **_stats(rows, a.today)}
    except SeoulApiError as e:
        print(f"서울 API 오류: {e}", file=sys.stderr)  # 메시지에 키·주소는 없다
        return 1
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
