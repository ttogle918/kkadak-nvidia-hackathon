"""런타임 자원(RSS)·시간 기준선 측정(T408). 제품 코드·`var/` 는 읽기만 한다. 서울 API·NVIDIA 를 부르지 않는다.

    uv run python scripts/measure_runtime.py --catalog var/catalog --index var/index/kcontext.db [--with-llm]

- 카탈로그 검색 자식: 3회 시간·``ru_maxrss``(wait4) + ``import`` 만 한 자식의 RSS(고정분)
- 파이프라인 자식: 임시 ``KC_VAR_DIR`` 에 캐시를 심어 적중시킨다(LLM 0회). ``--with-llm`` 은 이 1차에서는 지원하지 않는다(종료 2).
- backend: 임시 hitl·audit·output 경로로 uvicorn 을 띄워 유휴 RSS, 검색 1건/동시 2건 처리 중 합계 RSS(자식 포함) 최대값.
  LLM 키는 자식에게 넘기지 않고 ``.env`` 도 읽지 못하게 한다. 끝나면 띄운 프로세스를 정리한다.
출력: JSON 한 건. 단위 MB = 1024 KiB 기준(RSS 는 KiB → MiB).
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
REGIONS = "jung,jongno,mapo,gangnam"
TRIP = {"from": "2026-10-15", "to": "2026-10-18"}
TEXT = "창덕궁 10시, 익선동 2시, 종로3가 (측정용 합성 문장)"
_BASE = ("PATH", "HOME", "LANG", "LC_ALL", "PYTHONPATH", "VIRTUAL_ENV")
MIB = 1024.0


def _env(**extra: str) -> dict[str, str]:
    e = {k: os.environ[k] for k in _BASE if k in os.environ}
    e["APP_PROCESS_ROLE"] = "agent"
    e["APP_DOTENV_PATH"] = "/nonexistent/.env"  # .env 를 읽지 못하게 — 키가 자식에 전달되지 않는다
    e.update(extra)
    return e


def _mib(kib: float) -> float:
    return round(kib / MIB, 1)


def _status_kb(pid: int, field: str) -> int:
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith(field + ":"):
                return int(line.split()[1])
    except (OSError, ValueError):
        pass
    return 0


def _children(pid: int) -> list[int]:
    out = []
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        try:
            stat = (p / "stat").read_text()
            if int(stat.rsplit(")", 1)[1].split()[1]) == pid:
                out.append(int(p.name))
        except (OSError, ValueError, IndexError):
            continue
    return out


def _spawn_measure(cmd: list[str], env: dict[str, str], stdin_text: str = "") -> tuple[float, float, str]:
    """(초, 최대 RSS MiB, stdout). 최대 RSS = /proc/PID/status 의 VmHWM 을 10ms 마다 표본한 최대값.

    wait4 의 ``ru_maxrss`` 는 fork 시점 부모의 RSS 를 바닥으로 물려받을 수 있어(이 스크립트 약 34MiB) 작은 자식에서는
    부정확하다. 둘 중 부모 바닥보다 큰 쪽이 아니라 VmHWM 표본을 쓰고, ru_maxrss 는 참고로 ``_LAST_RU`` 에 둔다.
    """
    t0 = time.perf_counter()
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         cwd=REPO_ROOT, env=env)
    assert p.stdin is not None and p.stdout is not None
    peak = [0]
    done = threading.Event()

    def watch() -> None:
        while not done.is_set():
            peak[0] = max(peak[0], _status_kb(p.pid, "VmHWM"))
            time.sleep(0.01)

    th = threading.Thread(target=watch, daemon=True)
    th.start()
    p.stdin.write(stdin_text.encode())
    p.stdin.close()
    out = p.stdout.read().decode()
    _, status, ru = os.wait4(p.pid, 0)
    done.set()
    th.join()
    if status != 0:
        raise SystemExit(f"자식 오류 (상태 {status})")
    _LAST_RU[0] = _mib(ru.ru_maxrss)
    return time.perf_counter() - t0, _mib(peak[0]), out


_LAST_RU = [0.0]


def search_children(catalog: Path, runs: int) -> dict:
    req = json.dumps({"op": "search", "args": {"trip": TRIP}, "actor": None})
    env = _env(KC_CATALOG_DIR=str(catalog), KC_TARGET_REGION=REGIONS)
    cmd = [sys.executable, "-m", "domains.kcontext.catalog.api"]
    rows = [_spawn_measure(cmd, env, req) for _ in range(runs)]
    base = _spawn_measure([sys.executable, "-c", "import domains.kcontext.catalog.api"], env)
    return {"runs": runs, "secs": [round(r[0], 2) for r in rows], "secs_median": round(statistics.median(r[0] for r in rows), 2),
            "maxrss_mib": [r[1] for r in rows], "maxrss_mib_max": max(r[1] for r in rows),
            "import_only_maxrss_mib": base[1], "import_only_secs": round(base[0], 2)}


def pipeline_child(index: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="kc_measure_") as td:
        tmp = Path(td)
        var = tmp / "var"
        env = _env(KC_VAR_DIR=str(var), KC_SCHEDULE_CACHE="on", KC_TARGET_REGION=REGIONS)
        seed_src = sorted((REPO_ROOT / "var" / "cache" / "schedule").glob("*.json"))
        if not seed_src:
            raise SystemExit("var/cache/schedule 에 심을 원본 캐시가 없다")
        seed = json.loads(seed_src[0].read_text(encoding="utf-8"))
        plant = (
            "import json,sys\nfrom pathlib import Path\n"
            "from domains.kcontext.schedule import ScheduleCache, key_for\n"
            "from domains.kcontext.schedule.cache import default_root\n"
            "seed=json.loads(sys.stdin.read())\n"
            f"k=key_for({TEXT!r}, ({TRIP['from']!r}, {TRIP['to']!r}))\n"
            "ScheduleCache(default_root()).put(k, seed['result'], seed['meta'])\n"
        )
        subprocess.run([sys.executable, "-c", plant], input=json.dumps(seed), text=True, cwd=REPO_ROOT,
                       env=env, check=True, capture_output=True)
        text_file = tmp / "t.txt"
        text_file.write_text(TEXT, encoding="utf-8")
        out = tmp / "out"
        cmd = [sys.executable, "-m", "domains.kcontext.pipeline", "--text-file", str(text_file),
               "--trip-from", TRIP["from"], "--trip-to", TRIP["to"], "--db", str(index), "--out", str(out),
               "--llm-budget-s", "1"]
        secs, rss, stdout = _spawn_measure(cmd, env)
        bundle = json.loads((out / "bundle.json").read_text(encoding="utf-8"))
        source = (bundle.get("schedule") or {}).get("source")
        return {"secs": round(secs, 2), "maxrss_mib": rss, "ru_maxrss_mib_ref": _LAST_RU[0], "schedule_source": source,
                "cache_hit": source == "cache", "bundle_bytes": (out / "bundle.json").stat().st_size,
                "summary": json.loads(stdout.strip().splitlines()[-1]) if stdout.strip() else None}


class _Sampler(threading.Thread):
    """backend 와 그 자식들의 RSS 합계 최대값·자식별 VmHWM 최대값을 20ms 간격으로 표본."""

    def __init__(self, pid: int) -> None:
        super().__init__(daemon=True)
        self.pid, self.stop = pid, threading.Event()
        self.max_total = 0
        self.max_kids = 0
        self.max_nkids = 0
        self.child_hwm: dict[int, int] = {}

    def run(self) -> None:
        while not self.stop.is_set():
            kids = _children(self.pid)
            krss = 0
            for k in kids:
                krss += _status_kb(k, "VmRSS")
                self.child_hwm[k] = max(self.child_hwm.get(k, 0), _status_kb(k, "VmHWM"))
            self.max_kids = max(self.max_kids, krss)
            self.max_nkids = max(self.max_nkids, len(kids))
            self.max_total = max(self.max_total, _status_kb(self.pid, "VmRSS") + krss)
            time.sleep(0.02)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def backend(catalog: Path, index: Path) -> dict:
    port = _free_port()
    with tempfile.TemporaryDirectory(prefix="kc_measure_be_") as td:
        t = Path(td)
        env = _env(KC_HITL_DB=str(t / "hitl.db"), KC_AUDIT_DIR=str(t / "audit"), KC_OUTPUT_DIR=str(t / "output"),
                   KC_CATALOG_DIR=str(catalog), KC_INDEX_DB=str(index), KC_TARGET_REGION=REGIONS,
                   KC_VAR_DIR=str(t / "var"))
        env["APP_PROCESS_ROLE"] = "host"
        proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1",
                                 "--port", str(port), "--log-level", "warning"],
                                cwd=REPO_ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        base = f"http://127.0.0.1:{port}"
        try:
            for _ in range(100):
                try:
                    if httpx.get(f"{base}/openapi.json", timeout=2).status_code == 200:
                        break
                except httpx.HTTPError:
                    time.sleep(0.2)
            else:
                raise SystemExit("backend 가 뜨지 않았다")
            time.sleep(1.0)
            idle = _status_kb(proc.pid, "VmRSS")
            body = {"trip": TRIP}

            def one(res: list) -> None:
                t0 = time.perf_counter()
                r = httpx.post(f"{base}/api/events/search", json=body, timeout=120)
                res.append((r.status_code, round(time.perf_counter() - t0, 2), len(r.content)))

            def phase(n: int) -> dict:
                sm = _Sampler(proc.pid)
                sm.start()
                res: list = []
                ths = [threading.Thread(target=one, args=(res,)) for _ in range(n)]
                for th in ths:
                    th.start()
                for th in ths:
                    th.join()
                sm.stop.set()
                sm.join()
                return {"requests": n, "responses(status,secs,bytes)": res,
                        "max_children_seen": sm.max_nkids, "children_rss_sum_max_mib": _mib(sm.max_kids),
                        "child_vmhwm_max_mib": _mib(max(sm.child_hwm.values(), default=0)),
                        "total_rss_max_mib(backend+children)": _mib(sm.max_total)}

            one1 = phase(1)
            two = phase(2)
            return {"idle_rss_mib": _mib(idle), "during_1_search": one1, "during_2_concurrent_searches": two,
                    "backend_vmhwm_mib_after": _mib(_status_kb(proc.pid, "VmHWM"))}
        finally:
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


def _du(p: Path) -> int:
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) if p.exists() else 0


def _size_mib(p: Path) -> float:
    return round(_du(p) / 1048576, 1)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--index", type=Path, required=True)
    ap.add_argument("--with-llm", action="store_true")
    a = ap.parse_args(argv)
    if a.with_llm:
        print("--with-llm 은 1차 측정에서 지원하지 않는다(NVIDIA 호출 0회 규칙)", file=sys.stderr)
        return 2
    catalog, index = a.catalog.resolve(), a.index.resolve()
    if not (catalog / "entries.json").is_file() or not index.is_file():
        print("카탈로그 또는 색인이 없다", file=sys.stderr)
        return 2
    sizes = {f"{p.name}_mib": _size_mib(p) for p in (catalog / "entries.json", catalog / "observations.json", index)}
    sizes.update({f"var_{n}_mib": _size_mib(REPO_ROOT / "var" / n) for n in ("hitl.db", "audit", "cache", "output")})
    out = {"sizes": sizes,
           "search_child": search_children(catalog, 3),
           "pipeline_child_cache_hit": pipeline_child(index),
           "backend": backend(catalog, index)}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
