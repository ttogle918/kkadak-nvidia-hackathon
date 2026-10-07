"""python -m domains.kcontext.story --db PATH --anchor 이름 [--anchor 이름 ...] [--limit N] → JSON"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from domains.kcontext.index import LocalIndex
from domains.kcontext.story.mention import build_mentions


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m domains.kcontext.story")
    p.add_argument("--db", required=True)
    p.add_argument("--anchor", action="append", required=True)
    p.add_argument("--limit", type=int, default=3)
    a = p.parse_args(argv)
    if not Path(a.db).is_file():  # LocalIndex 는 없는 파일을 새로 만든다 — 읽기 전용 도구라 막는다
        print("error: 색인 파일이 없다", file=sys.stderr)
        return 2
    try:
        with LocalIndex(a.db) as idx:
            out = build_mentions(idx, [{"name": n} for n in a.anchor], limit=a.limit)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
