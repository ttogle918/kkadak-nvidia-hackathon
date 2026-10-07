"""행사 카탈로그 CLI (호스트 전용 — 공공데이터 키는 호스트 env 에서만 읽는다).

    python -m domains.kcontext.catalog update --source seoul_openapi [--sample]   # 한 출처 수집
    python -m domains.kcontext.catalog due                                         # 주기가 된 출처만
    python -m domains.kcontext.catalog loop --interval-min 30                      # 주기적 수집(스케줄러)
    python -m domains.kcontext.catalog status                                      # 수집·검토 현황 JSON

``--sample`` 은 서울시 sample 키(5행)로 연결만 확인한다(키 없이 가능, 행사 전체가 아니다).
종료 코드: 0 정상(수집 실패는 기록하고 종료 코드 1) · 2 실행 조건 미충족.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from dotenv import dotenv_values

from domains.kcontext.paths import repo_root
from domains.kcontext.regions import load_regions

from .rules import KST
from .sources import SourceError, load_sources, make_fetcher
from .store import CatalogStore
from .updater import run_due, run_source

TARGET_REGION = os.environ.get("KC_TARGET_REGION", "jung")  # data/regions/<id>.json


def _env() -> dict[str, str]:
    """셸 env 우선, 없는 키만 레포 .env 에서 보충한다(os.environ 은 바꾸지 않는다)."""
    merged = dict(os.environ)
    for k, v in dotenv_values(repo_root() / ".env").items():
        if v and not merged.get(k):
            merged[k] = v
    return merged


def _setup(args: argparse.Namespace):
    regions = load_regions()
    region = regions.get(args.region)
    if region is None:
        raise SystemExit(f"지역 {args.region!r} 이 data/regions/ 에 없다")
    return CatalogStore(args.dir), region, _env()


def _fetchers(sources: list[dict], region, now: datetime, env, sample: bool = False) -> dict:
    out = {}
    for s in sources:
        try:
            out[s["id"]] = make_fetcher(s["id"], region=region, now=now, env=env, sample=sample)
        except SourceError:
            continue
    return out


def status(store: CatalogStore, sources: list[dict]) -> dict:
    runs, checks = store.load_runs(), store.load_link_checks()
    return {
        "built_at": store.entries_built_at(),
        "entries": len(store.load_entries()),
        "sources": [{**{k: s[k] for k in ("id", "name", "method", "status", "url")},
                     "run": runs.get(s["id"]), "link_check": checks.get(s["id"])} for s in sources],
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m domains.kcontext.catalog")
    ap.add_argument("--dir", type=Path, help="카탈로그 저장 폴더(기본 var/catalog 또는 KC_CATALOG_DIR)")
    ap.add_argument("--region", default=TARGET_REGION)
    sub = ap.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("update")
    u.add_argument("--source", required=True)
    u.add_argument("--sample", action="store_true")
    sub.add_parser("due")
    lp = sub.add_parser("loop")
    lp.add_argument("--interval-min", type=float, default=30.0)
    lp.add_argument("--max-rounds", type=int, default=0, help="0 이면 계속")
    sub.add_parser("status")
    a = ap.parse_args(list(sys.argv[1:] if argv is None else argv))

    store, region, env = _setup(a)
    sources = load_sources()
    now = datetime.now(KST)
    if a.cmd == "status":
        print(json.dumps(status(store, sources), ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "update":
        from .store import default_dir

        if a.sample and (not a.dir or a.dir.resolve() == default_dir().resolve()):
            print("--sample(5행 연결 확인)은 실제 카탈로그를 오염시키지 않도록 --dir <임시 폴더>(기본 카탈로그 경로가 아닌) 와 함께만 쓴다",
                  file=sys.stderr)
            return 2
        fetchers = _fetchers(sources, region, now, env, sample=a.sample)
        if a.source not in fetchers:
            print(f"{a.source}: 자동 수집이 구현돼 있지 않거나 알 수 없는 출처다 — status 로 확인", file=sys.stderr)
            return 2
        if not a.sample and a.source == "seoul_openapi" and not env.get("SEOUL_OPENAPI_KEY"):
            print("SEOUL_OPENAPI_KEY 가 설정되지 않았다 — --sample 로 연결만 확인할 수 있다", file=sys.stderr)
            return 2
        r = run_source(store, a.source, fetchers[a.source], now=now)
        print(json.dumps(r.__dict__, ensure_ascii=False))
        return 0 if r.ok else 1
    if a.cmd == "due":
        res = run_due(store, sources, _fetchers(sources, region, now, env), now=now)
        print(json.dumps([r.__dict__ for r in res], ensure_ascii=False))
        return 0 if all(r.ok for r in res) else 1
    rounds = 0
    while True:  # loop
        now = datetime.now(KST)
        res = run_due(store, sources, _fetchers(sources, region, now, env), now=now)
        print(json.dumps({"at": now.strftime("%Y-%m-%dT%H:%M"), "runs": [r.__dict__ for r in res]},
                         ensure_ascii=False), flush=True)
        rounds += 1
        if a.max_rounds and rounds >= a.max_rounds:
            return 0
        time.sleep(a.interval_min * 60)


if __name__ == "__main__":
    raise SystemExit(main())
