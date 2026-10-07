"""CLI: python -m domains.kcontext.index stats|search --db PATH."""

from __future__ import annotations

import argparse
import sys

from domains.kcontext.index.store import LocalIndex


def _stats(db: str) -> int:
    with LocalIndex(db) as idx:
        conn = idx._conn
        print(f"total: {idx.count()}")
        print(f"fts_enabled: {idx.fts_enabled}")
        for tier, n in conn.execute(
            "SELECT tier, COUNT(*) FROM chunks GROUP BY tier ORDER BY tier"
        ):
            print(f"tier {tier}: {n}")
        for region, n in conn.execute(
            "SELECT region, COUNT(*) FROM chunk_regions GROUP BY region ORDER BY region"
        ):
            print(f"region {region}: {n}")
    return 0


def _search(db: str, q: str, region: str | None, limit: int) -> int:
    with LocalIndex(db) as idx:
        hits = idx.search(q, regions=[region] if region else None, limit=limit)
        for h in hits:
            quote = h.chunk.quote.replace("\n", " ")[:80]
            print(f"{h.score:.3f}\t{h.chunk.tier}\t{h.chunk.name}\t{h.chunk.locator}\t{quote}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m domains.kcontext.index")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stats")
    s.add_argument("--db", required=True)
    f = sub.add_parser("search")
    f.add_argument("--db", required=True)
    f.add_argument("--q", required=True)
    f.add_argument("--region")
    f.add_argument("--limit", type=int, default=20)
    a = p.parse_args(argv)
    try:
        if a.cmd == "stats":
            return _stats(a.db)
        return _search(a.db, a.q, a.region, a.limit)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
