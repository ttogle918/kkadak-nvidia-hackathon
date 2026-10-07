"""행사 수집 CLI (D7).

    python -m domains.kcontext.ingest.events --provider tourapi|seoul|manual --fixture PATH \\
        --from YYYY-MM-DD --to YYYY-MM-DD --out var/data/events/<provider>.jsonl \\
        [--db var/index/kcontext.db] --collected-at YYYY-MM-DD
    python -m domains.kcontext.ingest.events --provider web --source junggu --month 2026-10 ...
        (web 은 web_run 과 같은 옵션이다 — 구청 행사 검색 수집, D12)

종료 코드: 0 정상 · 2 실행 조건 미충족(field_map 없음 등) — 메시지에 대안을 적는다.
이번 범위의 tourapi·seoul 은 ``--fixture`` 로만 돈다(실호출은 T210-fetch).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from domains.kcontext.contract.records import EventRecord
from domains.kcontext.index.store import LocalIndex
from domains.kcontext.regions import load_regions

from .manual import load_manual
from .normalize import FieldMapMissing, NormalizeResult, load_field_map, normalize
from .store import to_chunks, write_jsonl


def _in_range(r: EventRecord, date_from: str | None, date_to: str | None) -> bool:
    """기간을 모르면 남긴다. 끝이 없으면 하루짜리로 본다."""
    start, end = r.start_date, r.end_date
    if start is None and end is None:
        return True
    lo, hi = start or end, end or start
    return not ((date_to and lo > date_to) or (date_from and hi < date_from))  # type: ignore[operator]


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--provider" in args and args[args.index("--provider") + 1 : args.index("--provider") + 2] == ["web"]:
        from .web_run import run as run_web

        i = args.index("--provider")
        return run_web(args[:i] + args[i + 2 :])

    ap = argparse.ArgumentParser(prog="python -m domains.kcontext.ingest.events")
    ap.add_argument("--provider", required=True, choices=["tourapi", "seoul", "manual", "web"])
    ap.add_argument("--fixture", type=Path, required=True)
    ap.add_argument("--from", dest="date_from")
    ap.add_argument("--to", dest="date_to")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--db", type=Path)
    ap.add_argument("--collected-at", required=True)
    ap.add_argument("--field-map-dir", type=Path)
    a = ap.parse_args(args)

    regions = load_regions()
    if a.provider == "manual":
        res: NormalizeResult = load_manual(a.fixture, regions=regions)
    else:
        try:
            fm = load_field_map(a.provider, a.field_map_dir)
        except FieldMapMissing:
            print("T205 field_map 이 없다 — `--provider manual` 로 실행할 수 있다", file=sys.stderr)
            return 2
        try:
            raw = json.loads(a.fixture.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"{a.fixture.name}: 읽을 수 없다 ({type(e).__name__})", file=sys.stderr)
            return 2
        res = normalize(raw, provider=a.provider, field_map=fm, collected_at=a.collected_at,
                        regions=regions)

    records = [r for r in res.records if _in_range(r, a.date_from, a.date_to)]
    out_of_range = len(res.records) - len(records)
    for p in res.problems:
        print(f"problem: {p}", file=sys.stderr)
    if a.out:
        write_jsonl(records, a.out)
    if a.db:
        a.db.parent.mkdir(parents=True, exist_ok=True)
        with LocalIndex(a.db) as idx:
            idx.add([c for r in records for c in to_chunks(r)])
    print(json.dumps({"records": len(records), "problems": len(res.problems),
                      "skipped_out_of_region": res.skipped_out_of_region,
                      "skipped_out_of_range": out_of_range}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
