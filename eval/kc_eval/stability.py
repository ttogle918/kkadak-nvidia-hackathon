"""안정성 측정기 — ``kc.py stability``. 같은 일정 문장을 여러 번 돌려 흔들림을 숫자로 잡는다.

층: ``pipeline`` 은 backend 가 쓰는 것과 같은 명령으로 파이프라인을 별도 프로세스로 돌리고,
``api`` 는 떠 있는 backend 의 ``POST /messages`` 를 순차 호출한다. 이 모듈이 LLM 을 직접 부르지 않는다.
실행 기록에는 앵커 요약·문제 코드·지연·좌표 수만 남긴다 — LLM 원문·묶음 전체·reply 는 저장하지 않는다.
앵커 비교 규칙은 ``kc_eval.match`` 하나다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from kc_eval.match import match_anchors
from kc_eval.meta import git_head
from kc_eval.schema import load_suite, validate_suite

__all__ = [
    "CHILD_ENV_ALLOW",
    "LLM_FAIL_CODES",
    "OUTCOMES",
    "SCHEDULE_UNAVAILABLE_REPLY",
    "classify_api",
    "classify_pipeline",
    "main",
    "percentile",
    "summarize",
]

RESULT_SCHEMA = "kc-eval-stability/v1"
OUTCOMES = ("ok", "no_anchors_expected", "fallback_llm", "fallback_unverified", "fallback_chat",
            "schedule_unavailable", "timeout", "error")  # fmt: skip
LLM_FAIL_CODES = ("LLM_FAILED", "LLM_EMPTY", "LLM_BAD_JSON", "LLM_UNEXPECTED_SHAPE",
                  "LLM_UNAVAILABLE")  # fmt: skip
# 폴백으로 세는 결과(기대 ok 케이스에서). 두 층의 이름을 합친 목록이다.
FALLBACK_OUTCOMES = ("fallback_llm", "fallback_unverified", "fallback_chat", "schedule_unavailable",
                     "timeout", "error")  # fmt: skip
# D15 ⑤ 의 고정 문구. backend 상수(T310 이 만든다)와 같은 값이어야 한다 — T310 머지 뒤 일치를 테스트한다.
SCHEDULE_UNAVAILABLE_REPLY = {"ko": "일정을 지금 정리하지 못했어요. 잠시 뒤 다시 보내 주세요."}

# backend/story_runner.py 의 _ENV_ALLOW 사본(D7 ③ — 셸 env 를 통째로 넘기지 않는다). 테스트가 일치를 확인한다.
CHILD_ENV_ALLOW = (
    "PATH", "HOME", "LANG", "LC_ALL", "PYTHONPATH", "VIRTUAL_ENV",
    "NVIDIA_API_KEY", "NVIDIA_API_KEY_A", "NVIDIA_API_KEY_B", "CHAT_MODEL", "SCHEDULE_MODEL",
    "KC_TARGET_REGION", "KC_DATA_DIR",
)  # fmt: skip

REPO_ROOT = Path(__file__).resolve().parents[2]
LLM_CONFIG = REPO_ROOT / "deploy" / "llm.chat.yaml"
API_TIMEOUT_S = 110
_LABEL = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
_CALLS_PER_RUN = {"pipeline": 2, "api": 3}  # 첫 시도 + 재시도 / + 일반 챗봇


# ------------------------------------------------------------------ 순수 함수
def percentile(values: Sequence[float], p: float) -> float | None:
    """nearest-rank 백분위. 값이 없으면 None."""
    if not values:
        return None
    xs = sorted(values)
    rank = max(1, math.ceil(p / 100 * len(xs)))
    return xs[min(rank, len(xs)) - 1]


def _anchors_of(bundle: Any) -> list[dict] | None:
    if not isinstance(bundle, Mapping):
        return None
    it = bundle.get("itinerary")
    anchors = it.get("anchors") if isinstance(it, Mapping) else None
    if not isinstance(anchors, list):
        return None
    return [a for a in anchors if isinstance(a, Mapping)]  # type: ignore[misc]


def _codes_of(bundle: Any) -> list[str]:
    probs = bundle.get("problems") if isinstance(bundle, Mapping) else None
    if not isinstance(probs, list):
        return []
    return [str(p["code"]) for p in probs if isinstance(p, Mapping) and isinstance(p.get("code"), str)]


def classify_pipeline(exit_code: int | None, bundle: Mapping | None, expect_status: str) -> str:
    """exit_code None 은 시간 초과. 묶음을 못 읽은 정상 종료는 error."""
    if exit_code is None:
        return "timeout"
    if exit_code != 0:
        return "error"
    anchors = _anchors_of(bundle)
    if anchors is None:
        return "error"
    if anchors:
        return "ok"
    if any(c in LLM_FAIL_CODES for c in _codes_of(bundle)):
        return "fallback_llm"
    if expect_status == "no_anchors":
        return "no_anchors_expected"
    return "fallback_unverified"


def _reply_ko(body: Mapping) -> str:
    reply = body.get("reply")
    text = reply.get("text") if isinstance(reply, Mapping) else None
    if isinstance(text, Mapping):
        text = text.get("ko")
    return text if isinstance(text, str) else ""


def classify_api(status: int | None, body: Mapping | None, expect_status: str) -> str:
    """status None 은 클라이언트 시간 초과."""
    if status is None:
        return "timeout"
    if status != 200 or not isinstance(body, Mapping):
        return "error"
    bundle = body.get("bundle")
    if isinstance(bundle, Mapping) and bundle.get("status") == "ok":
        return "ok"
    if not isinstance(bundle, Mapping) and SCHEDULE_UNAVAILABLE_REPLY["ko"] in _reply_ko(body):
        return "schedule_unavailable"
    return "no_anchors_expected" if expect_status == "no_anchors" else "fallback_chat"


def _compare(case: Mapping, anchors: list[dict] | None) -> dict:
    """저장할 요약만 만든다(앵커 이름·시각·좌표 유무). 원문은 남기지 않는다."""
    if anchors is None:
        return {"n_anchors": None}
    expect = (case.get("expect") or {}).get("anchors") or []
    m = match_anchors(expect, anchors)
    return {
        "n_anchors": len(anchors),
        "anchors": [{"type": a.get("type"), "name": a.get("name"),
                     "from": a.get("from"), "to": a.get("to")} for a in anchors],
        "coords": sum(1 for a in anchors if a.get("lat") is not None and a.get("lng") is not None),
        "pairs": len(m["pairs"]), "expected": len(expect), "missing": len(m["missing"]),
        "extra": len(m["extra"]), "field_fail": m["field_fail"], "exact": m["exact"],
    }  # fmt: skip


def _ratio(a: int, b: int) -> float | None:
    return round(a / b, 4) if b else None


def summarize(case_runs: Sequence[Mapping], cases: Sequence[Mapping]) -> dict:
    """§6.1 지표. 폴백·변동·일치·재현율/정밀도는 기대 ``ok`` 케이스의 실행만으로 계산한다."""
    status = {c["id"]: (c.get("expect") or {}).get("status", "ok") for c in cases}
    ok_runs = [r for r in case_runs if status.get(r["id"], "ok") == "ok"]
    outcomes = Counter(r["outcome"] for r in case_runs)
    fallbacks = sum(1 for r in ok_runs if r["outcome"] in FALLBACK_OUTCOMES)

    by_case: dict[str, list[int]] = {}
    for r in ok_runs:
        if isinstance(r.get("n_anchors"), int):
            by_case.setdefault(r["id"], []).append(r["n_anchors"])
    varying = sum(1 for v in by_case.values() if len(set(v)) > 1)
    rates = [1 - Counter(v).most_common(1)[0][1] / len(v) for v in by_case.values()]

    exact = sum(1 for r in ok_runs if r.get("exact") is True)
    pairs = sum(r.get("pairs") or 0 for r in ok_runs)
    expected = sum(r.get("expected") or 0 for r in ok_runs if r.get("pairs") is not None)
    actual = sum(r.get("n_anchors") or 0 for r in ok_runs)
    anchors_total = sum(r.get("n_anchors") or 0 for r in case_runs)
    coords = sum(r.get("coords") or 0 for r in case_runs)
    codes = Counter(c for r in case_runs for c in r.get("problem_codes", []))

    ms_all = [r["ms"] for r in case_runs if isinstance(r.get("ms"), (int, float))]
    ms_ok = [r["ms"] for r in case_runs
             if r["outcome"] == "ok" and isinstance(r.get("ms"), (int, float))]  # fmt: skip
    return {
        "runs_total": len(case_runs),
        "expected_ok_runs": len(ok_runs),
        "outcomes": {k: outcomes[k] for k in OUTCOMES if outcomes[k]},
        "fallback_count": fallbacks,
        "fallback_rate": _ratio(fallbacks, len(ok_runs)),
        "varying_cases": varying,
        "cases_measured": len(by_case),
        "count_variation_rate": round(sum(rates) / len(rates), 4) if rates else None,
        "exact_count": exact,
        "exact_rate": _ratio(exact, len(ok_runs)),
        "anchor_recall": _ratio(pairs, expected),
        "anchor_precision": _ratio(pairs, actual),
        "latency_ms": {"p50": percentile(ms_all, 50), "p95": percentile(ms_all, 95),
                       "ok_p50": percentile(ms_ok, 50), "ok_p95": percentile(ms_ok, 95)},
        "problem_codes": dict(sorted(codes.items())),
        "coord_attach_rate": _ratio(coords, anchors_total),
    }


def estimate_calls(n_cases: int, runs: int, layer: str) -> int:
    """예상 최대 LLM 호출 = 실행 수 × (pipeline 2 | api 3)."""
    return n_cases * runs * _CALLS_PER_RUN[layer]


# ------------------------------------------------------------------ 실행
def child_env(cache: str) -> dict[str, str]:
    """자식 프로세스 env — 허용 목록 + LLM_BACKEND* 만. backend._child_env() 와 같은 방식."""
    env = {k: os.environ[k] for k in CHILD_ENV_ALLOW if k in os.environ}
    env.update({k: v for k, v in os.environ.items() if k.startswith("LLM_BACKEND")})
    env["APP_PROCESS_ROLE"] = "agent"
    env["KC_SCHEDULE_CACHE"] = cache
    return env


def _pipeline_cmd(src: Path, db: Path, out: Path, trip: Mapping | None) -> list[str]:
    # backend/story_runner.py 와 같은 명령(+ --force). 자식은 호스트 에이전트 프로세스 역할이다.
    cmd = [sys.executable, "-m", "domains.kcontext.pipeline", "--text-file", str(src),
           "--db", str(db), "--out", str(out), "--force"]  # fmt: skip
    if trip:
        cmd += ["--trip-from", trip["from"], "--trip-to", trip["to"]]
    return cmd


def run_pipeline_once(case: Mapping, db: Path, timeout_s: int, cache: str) -> dict:
    expect_status = (case.get("expect") or {}).get("status", "ok")
    env = child_env(cache)
    bundle: dict | None = None
    code: int | None
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="kc_stab_") as td:
        tmp = Path(td)
        src = tmp / "text.txt"
        src.write_text(case["text"], encoding="utf-8")
        cmd = _pipeline_cmd(src, db, tmp / "out", case.get("trip"))
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT, env=env,
                               check=False, timeout=timeout_s)  # fmt: skip
            code = p.returncode
        except subprocess.TimeoutExpired:
            code = None
        except OSError:
            code = 1
        ms = round((time.monotonic() - t0) * 1000)
        if code == 0:
            try:
                raw = json.loads((tmp / "out" / "bundle.json").read_text(encoding="utf-8"))
                bundle = raw if isinstance(raw, dict) else None
            except (OSError, ValueError):
                bundle = None
    outcome = classify_pipeline(code, bundle, expect_status)
    rec = {"outcome": outcome, "ms": ms, "problem_codes": _codes_of(bundle)}
    rec.update(_compare(case, _anchors_of(bundle)))
    return rec


def run_api_once(case: Mapping, base: str) -> dict:
    expect_status = (case.get("expect") or {}).get("status", "ok")
    ctx: dict[str, Any] = {"schema": "chat-context/v1", "lang": case.get("lang", "ko")}
    if case.get("trip"):
        ctx["trip"] = {"from": case["trip"]["from"], "to": case["trip"]["to"]}
    t0 = time.monotonic()
    status: int | None
    body: Any = None
    try:
        resp = httpx.post(f"{base.rstrip('/')}/messages", json={"text": case["text"], "context": ctx},
                          timeout=API_TIMEOUT_S)  # fmt: skip
        status = resp.status_code
        try:
            body = resp.json()
        except ValueError:
            body = None
    except httpx.TimeoutException:
        status = None
    ms = round((time.monotonic() - t0) * 1000)
    bundle = body.get("bundle") if isinstance(body, Mapping) else None
    rec = {"outcome": classify_api(status, body, expect_status), "ms": ms,
           "http_status": status, "problem_codes": _codes_of(bundle)}  # fmt: skip
    rec.update(_compare(case, _anchors_of(bundle)))
    return rec


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _select(doc: Mapping, ids: str | None) -> list[dict]:
    cases = [c for c in doc.get("cases", []) if isinstance(c, dict)]
    if not ids:
        return [c for c in cases if (c.get("expect") or {}).get("status") == "ok"]
    want = [s.strip() for s in ids.split(",") if s.strip()]
    by_id = {c["id"]: c for c in cases}
    unknown = [i for i in want if i not in by_id]
    if unknown:
        raise ValueError(f"세트에 없는 케이스: {', '.join(unknown)}")
    return [by_id[i] for i in want]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="kc.py stability", description="같은 일정 문장을 반복 실행해 흔들림을 잰다")
    ap.add_argument("--suite", default="eval/drafts/schedule.json")
    ap.add_argument("--layer", choices=("pipeline", "api"), required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--cases", help="쉼표로 구분한 케이스 id (기본: 기대 ok 케이스 전부)")
    ap.add_argument("--db", default="var/index/kcontext.db")
    ap.add_argument("--timeout-s", type=int, default=90)
    ap.add_argument("--base", default="http://localhost:8000/api")
    ap.add_argument("--out", default="eval/results")
    ap.add_argument("--label", default="baseline")
    ap.add_argument("--cache", choices=("off", "on"), default="off")
    ap.add_argument("--max-calls", type=int, default=210)
    ap.add_argument("--yes", action="store_true", help="예상 호출 수가 --max-calls 를 넘어도 시작")
    ns = ap.parse_args(argv)

    if not _LABEL.match(ns.label):
        print("--label 은 영문·숫자·_- 40자 이하", file=sys.stderr)
        return 2
    if ns.runs < 1 or ns.timeout_s < 1:
        print("--runs·--timeout-s 는 1 이상", file=sys.stderr)
        return 2
    try:
        doc = load_suite(Path(ns.suite))
        probs = validate_suite(doc)
        if probs or doc.get("suite") != "schedule":
            raise ValueError(probs[0] if probs else "schedule 세트가 아니다")
        cases = _select(doc, ns.cases)
    except (ValueError, OSError) as e:
        print(f"세트를 읽을 수 없다: {e}", file=sys.stderr)
        return 2
    if not cases:
        print("실행할 케이스가 없다", file=sys.stderr)
        return 2
    db = Path(ns.db)
    if ns.layer == "pipeline" and not db.is_file():
        print(f"색인 파일이 없다: {ns.db}", file=sys.stderr)
        return 2

    est = estimate_calls(len(cases), ns.runs, ns.layer)
    print(f"케이스 {len(cases)} × {ns.runs}회 = {len(cases) * ns.runs} 실행, 예상 최대 LLM 호출 {est}")
    if est > ns.max_calls and not ns.yes:
        print(f"예상 호출 {est} > --max-calls {ns.max_calls} — 계속하려면 --yes", file=sys.stderr)
        return 2

    started = datetime.now(UTC)
    case_runs: list[dict] = []
    interrupted = False
    try:
        for run in range(1, ns.runs + 1):
            for c in cases:
                if ns.layer == "pipeline":
                    rec = run_pipeline_once(c, db, ns.timeout_s, ns.cache)
                else:
                    try:
                        rec = run_api_once(c, ns.base)
                    except httpx.TransportError:
                        if not case_runs:
                            print("backend 에 연결할 수 없다 — backend 를 먼저 띄운다", file=sys.stderr)
                            return 2
                        rec = {"outcome": "error", "ms": None, "http_status": None, "problem_codes": [],
                               "n_anchors": None}  # fmt: skip
                case_runs.append({"id": c["id"], "run": run, **rec})
                print(f"[{run}/{ns.runs}] {c['id']}: {rec['outcome']} ({rec['ms']} ms)")
    except KeyboardInterrupt:
        interrupted = True
        print("중단됨 — 지금까지의 결과를 저장한다", file=sys.stderr)

    finished = datetime.now(UTC)
    result = {
        "schema": RESULT_SCHEMA, "label": ns.label, "layer": ns.layer, "runs": ns.runs,
        "cache": ns.cache, "git_head": git_head(REPO_ROOT),
        "llm_config_sha256": _sha256(LLM_CONFIG),
        "child_env_names": sorted(child_env(ns.cache)) if ns.layer == "pipeline" else None,
        "model_env": {k: os.environ.get(k) or None for k in ("CHAT_MODEL", "SCHEDULE_MODEL")},
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "finished_at": finished.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "interrupted": interrupted, "est_calls": est,
        "case_runs": case_runs, "summary": summarize(case_runs, cases),
    }  # fmt: skip
    out_dir = Path(ns.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{ns.label}-{ns.layer}-{started.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    s = result["summary"]
    print(f"결과: {path}\n폴백 {s['fallback_count']}/{s['expected_ok_runs']} · 변동 케이스 "
          f"{s['varying_cases']}/{s['cases_measured']} · 정답 일치 {s['exact_count']}")  # fmt: skip
    return 130 if interrupted else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
