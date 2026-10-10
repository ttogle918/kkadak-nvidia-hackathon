"""행사 검색 1회의 구간별 시간 프로파일(T407). 카탈로그 폴더는 읽기만 한다 — 제품 코드·데이터를 바꾸지 않는다.

    uv run python scripts/profile_catalog_search.py --catalog var/catalog \
        --trip 2026-10-15..2026-10-15 --trip 2026-10-15..2026-10-18 [--runs 3]

구간은 ``CatalogStore.load_entries`` 와 ``api._search`` 의 순서를 스크립트 안에서 그대로 재현한 것이다(재현 경로).
일정(itinerary)이 없는 요청이라 ``fit_event`` 구간은 없다. 실호출 없음. 출력: trip 마다 JSON 한 건.
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
_BASE_ENV = ("PATH", "HOME", "LANG", "LC_ALL", "PYTHONPATH", "VIRTUAL_ENV")
_CHILD = [sys.executable, "-m", "domains.kcontext.catalog.api"]


def _ms(t0: float) -> float:
    return (time.perf_counter() - t0) * 1000


def _child_env(catalog: Path) -> dict[str, str]:
    env = {k: os.environ[k] for k in _BASE_ENV if k in os.environ}
    env["APP_PROCESS_ROLE"] = "agent"
    env["KC_CATALOG_DIR"] = str(catalog)
    return env


def _timed_child(cmd: list[str], env: dict[str, str], stdin: str = "") -> tuple[float, str]:
    t0 = time.perf_counter()
    p = subprocess.run(cmd, input=stdin, text=True, capture_output=True, cwd=REPO_ROOT,
                       env=env, check=False)
    ms = _ms(t0)
    if p.returncode != 0:
        raise SystemExit(f"자식 프로세스 오류 (종료 코드 {p.returncode})")
    return ms, p.stdout


def _in_process(catalog: Path, trip: dict) -> dict:
    """한 번의 검색을 구간별로. load_entries 는 read_text → json.loads → entry_from_dict, 그 뒤 _coverage 의
    entries_built_at 이 entries.json 을 한 번 더 읽는다(extra_entries_parse 로 따로 잰다)."""
    from domains.kcontext.catalog.model import entry_from_dict
    from domains.kcontext.catalog.query import search_events
    from domains.kcontext.catalog.rules import KST
    from domains.kcontext.catalog.store import CatalogStore

    store = CatalogStore(catalog)
    t = time.perf_counter()
    text = (catalog / "entries.json").read_text(encoding="utf-8")
    read_file = _ms(t)
    t = time.perf_counter()
    raw = json.loads(text)
    json_parse = _ms(t)
    t = time.perf_counter()
    entries = [entry_from_dict(e) for e in raw.get("entries", [])]
    entry_from = _ms(t)
    t = time.perf_counter()
    store.entries_built_at()
    store.load_runs()
    coverage_extra = _ms(t)
    t = time.perf_counter()
    res = search_events(entries, {"trip": trip}, now=datetime.now(KST),
                        coverage={"entries_built_at": None, "sources": []})
    search = _ms(t)
    t = time.perf_counter()
    out = json.dumps(res, ensure_ascii=False)
    dumps = _ms(t)
    t = time.perf_counter()
    ex = json.dumps(res["excluded"], ensure_ascii=False)
    ex_dumps = _ms(t)
    t = time.perf_counter()
    json.loads((catalog / "observations.json").read_text(encoding="utf-8"))
    obs = _ms(t)
    return {"read_file": read_file, "json_parse": json_parse, "entry_from_dict": entry_from,
            "coverage_extra_parse": coverage_extra, "search_events": search, "result_dumps": dumps,
            "excluded_dumps": ex_dumps, "observations_parse_info": obs,
            "n_entries": len(entries), "events": len(res["events"]), "excluded": len(res["excluded"]),
            "result_bytes": len(out.encode()), "excluded_bytes": len(ex.encode())}


def _med(rows: list[dict], key: str) -> float:
    return round(statistics.median(r[key] for r in rows), 1)


def profile(catalog: Path, trip_s: str, runs: int) -> dict:
    a, _, b = trip_s.partition("..")
    trip = {"from": a, "to": b or a}
    env = _child_env(catalog)
    req = json.dumps({"op": "search", "args": {"trip": trip}, "actor": None}, ensure_ascii=False)
    inproc = [_in_process(catalog, trip) for _ in range(runs)]
    base, imp, tot, parse_ms = [], [], [], []
    for _ in range(runs):
        base.append(_timed_child([sys.executable, "-c", "pass"], env)[0])
        imp.append(_timed_child([sys.executable, "-c", "import domains.kcontext.catalog.api"], env)[0])
        ms, stdout = _timed_child(_CHILD, env, req)
        tot.append(ms)
        t = time.perf_counter()
        json.loads(stdout)  # 부모 쪽 파싱(run_catalog 와 같은 일)
        parse_ms.append(_ms(t))
    r0 = inproc[0]
    stages = {k: _med(inproc, k) for k in ("read_file", "json_parse", "entry_from_dict",
                                          "coverage_extra_parse", "search_events", "result_dumps")}
    stages["interpreter_start"] = round(statistics.median(base), 1)
    stages["interpreter_plus_imports"] = round(statistics.median(imp), 1)
    stages["parent_json_parse"] = round(statistics.median(parse_ms), 1)
    stages["subprocess_total"] = round(statistics.median(tot), 1)
    accounted = sum(stages[k] for k in ("interpreter_plus_imports", "read_file", "json_parse",
                                       "entry_from_dict", "coverage_extra_parse", "search_events",
                                       "result_dumps", "parent_json_parse"))
    stages["unaccounted_pipe_gc_other"] = round(stages["subprocess_total"] - accounted, 1)
    return {"trip": trip_s, "runs": runs, "entries": r0["n_entries"], "stages_ms": stages,
            "excluded_dumps_ms": _med(inproc, "excluded_dumps"),
            "observations_parse_info_ms": _med(inproc, "observations_parse_info"),
            "result_bytes": r0["result_bytes"], "excluded_bytes": r0["excluded_bytes"],
            "events": r0["events"], "excluded": r0["excluded"],
            "dumps_share_of_total": round(stages["result_dumps"] / stages["subprocess_total"], 3),
            "excluded_dumps_share_of_total": round(_med(inproc, "excluded_dumps")
                                                   / stages["subprocess_total"], 3),
            "max_rss_kb": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--catalog", type=Path, default=Path("var/catalog"))
    ap.add_argument("--trip", action="append", required=True, help="YYYY-MM-DD..YYYY-MM-DD (반복 가능)")
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()
    if not (args.catalog / "entries.json").is_file():
        print("카탈로그가 없다 — 스냅샷 복원: scripts/snapshot_catalog.py 의 복원 경로를 본다", file=sys.stderr)
        return 2
    for t in args.trip:
        print(json.dumps(profile(args.catalog, t, args.runs), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
