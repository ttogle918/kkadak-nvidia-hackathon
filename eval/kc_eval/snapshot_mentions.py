"""실록 언급 평가셋 스냅샷(kc-eval/v1 mentions) — 로컬 색인을 조회한 실측 값만 쓴다.

앵커 목록은 data/regions/*.json 의 keywords 와 장소 사전의 이름(별칭 제외)이다. 코드에 이름을 두지 않는다.
색인은 읽기 전용: 임시 사본을 열어 조회하므로 원본 파일은 바뀌지 않는다. 원문 구절(quote)은 담지 않는다.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

from domains.kcontext.index.store import LocalIndex
from domains.kcontext.places import load_places
from domains.kcontext.regions import load_regions
from domains.kcontext.story.mention import build_mentions
from kc_eval.meta import temp_copy

SCHEMA = "kc-eval/v1"
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TOP_KEYS = ("article_id", "title_summary", "matched_in", "king", "date_label")


def _anchor_names() -> list[tuple[str, list[str]]]:
    """(이름, 태그) — 정렬·중복 제거."""
    tags: dict[str, set[str]] = {}
    for r in load_regions().values():
        for k in r.keywords:
            tags.setdefault(k, set()).add("region_keyword")
    for p in load_places().places:
        tags.setdefault(p.name, set()).add("verified_coord")
    return [(n, sorted(tags[n])) for n in sorted(tags)]


def _case_id(i: int) -> str:
    return f"men_{i:03d}"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="snapshot-mentions")
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--measured-at", required=True)
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--extra-aliases-label", default=None)
    args = ap.parse_args(argv)
    if not _DATE.match(args.measured_at):
        print("--measured-at 은 YYYY-MM-DD", file=sys.stderr)
        return 2
    db = Path(args.db)
    if not db.is_file():
        print(f"색인 파일이 없다: {db}", file=sys.stderr)
        return 2

    names = _anchor_names()
    with temp_copy(db) as copy:  # 원본은 열지 않는다
        with LocalIndex(copy) as idx:
            total, fts = idx.count(), idx.fts_enabled
            res = build_mentions(idx, [{"name": n} for n, _ in names], limit=args.limit)
        con = sqlite3.connect(f"file:{copy}?mode=ro", uri=True)
        try:
            alias_rows = int(con.execute("SELECT COUNT(*) FROM place_alias").fetchone()[0])
        finally:
            con.close()

    cases: list[dict[str, Any]] = []
    for i, ((name, tags), r) in enumerate(zip(names, res["anchors"], strict=True), 1):
        cases.append({
            "id": _case_id(i),
            "anchor": name,
            "limit": args.limit,
            "expect": {
                "reason": r["reason"],
                "terms": r["terms"],
                "found_articles": r["found_articles"],
                "found_truncated": r["found_truncated"],
                "top": [{**{k: m.get(k) for k in _TOP_KEYS}, "relevant": None}
                        for m in r["mentions"]],
            },
            "tags": [*tags, "no_match" if r["reason"] == "no_match" else "has_match"],
        })  # fmt: skip
    index: dict[str, Any] = {
        "db": args.db, "measured_at": args.measured_at, "total_chunks": total,
        "fts_enabled": fts, "alias_rows": alias_rows,
    }  # fmt: skip
    if args.extra_aliases_label:
        index["extra_aliases_label"] = args.extra_aliases_label
    doc = {
        "schema": SCHEMA, "suite": "mentions", "created_at": args.measured_at,
        "reviewed": False, "synthetic": False,
        "provenance": "로컬 색인 실측(build_mentions 결과). 기대 정답·relevant 는 사람 확인 전(H10)",
        "index": index, "cases": cases,
    }  # fmt: skip
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    nm = sum(1 for c in cases if c["expect"]["reason"] == "no_match")
    print(f"cases={len(cases)} no_match={nm} index={json.dumps(index, ensure_ascii=False)}")
    return 0
