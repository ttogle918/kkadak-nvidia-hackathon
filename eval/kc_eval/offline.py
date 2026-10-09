"""결정적(LLM·네트워크 없음) 평가 실행기 — ``kc.py run``.

suite: gate(일정 게이트) · mentions(실록 언급 스냅샷) · judge(행사 판정) · guard(주입 차단).
결과 파일에는 케이스 id·통과 여부·짧은 비교 값만 담는다(키·LLM 원문 없음 — 이 실행기는 LLM 을 부르지 않는다).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.schedule_gate import looks_like_schedule
from domains.kcontext.catalog.merge import build_entries
from domains.kcontext.catalog.model import observation_from_dict
from domains.kcontext.catalog.query import search_events
from domains.kcontext.index import LocalIndex
from domains.kcontext.judge.inject import screen
from domains.kcontext.schedule.understand import understand
from domains.kcontext.story.mention import build_mentions
from kc_eval.meta import git_head, temp_copy
from kc_eval.schema import load_suite, validate_suite

__all__ = ["main", "run_gate", "run_guard", "run_judge", "run_mentions"]

RESULT_SCHEMA = "kc-eval-result/v1"
RUNNABLE = ("gate", "mentions", "judge", "guard")
_KNOWN = re.compile(r"`known-failure:\s*([a-z]+)/([a-z0-9_]+)`")
_LABEL = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
_DEFAULT_LIMIT = 3


def _ratio(a: int, b: int) -> float | None:
    return round(a / b, 4) if b else None


def _suite(name: str, cases: list[dict], metrics: dict | None = None) -> dict:
    passed = sum(1 for c in cases if c["pass"])
    return {"suite": name, "status": "ok", "total": len(cases), "passed": passed,
            "failed": len(cases) - passed, "metrics": metrics or {}, "cases": cases}  # fmt: skip


def _skipped(name: str, reason: str) -> dict:
    return {"suite": name, "status": "skipped", "reason": reason, "total": 0, "passed": 0,
            "failed": 0, "metrics": {}, "cases": []}  # fmt: skip


def _case(cid: str, ok: bool, detail: dict | None = None) -> dict:
    return {"id": cid, "pass": bool(ok), "detail": detail or {}}


def _err(cid: str, e: Exception) -> dict:
    return _case(cid, False, {"error": type(e).__name__})  # 타입 이름만


# ------------------------------------------------------------------ gate
def run_gate(doc: Mapping) -> dict:
    cases: list[dict] = []
    tp = fp = fn = tn = 0
    for c in doc.get("cases", []):
        cid = c["id"]
        try:
            want = bool(c["expect"]["schedule"])
            got = looks_like_schedule(c["text"])
        except Exception as e:  # noqa: BLE001 - 케이스 예외는 그 케이스 실패
            cases.append(_err(cid, e))
            continue
        tp += want and got
        fp += (not want) and got
        fn += want and (not got)
        tn += (not want) and (not got)
        cases.append(_case(cid, want == got, {"expected": want, "actual": got}))
    return _suite("gate", cases, {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
                                  "precision": _ratio(tp, tp + fp), "recall": _ratio(tp, tp + fn)})  # fmt: skip


# -------------------------------------------------------------- mentions
def _mention_cases(index: LocalIndex, doc: Mapping) -> tuple[list[dict], dict]:
    cases: list[dict] = []
    n_nomatch = n_trunc = labeled = relevant = 0
    for c in doc.get("cases", []):
        cid = c["id"]
        try:
            limit = c.get("limit", _DEFAULT_LIMIT)
            res = build_mentions(index, [{"name": c["anchor"]}], limit=limit)["anchors"][0]
            got = [m["article_id"] for m in res["mentions"]]
            exp = c["expect"]
            want = [t["article_id"] for t in exp["top"]]
            n_nomatch += res["reason"] == "no_match"
            n_trunc += bool(res["found_truncated"])
            marks = {t["article_id"]: t.get("relevant") for t in exp["top"]}
            for a in got[:3]:
                if marks.get(a) is not None:
                    labeled += 1
                    relevant += bool(marks[a])
            ok = res["reason"] == exp.get("reason") and got == want
            cases.append(_case(cid, ok, {"reason": [exp.get("reason"), res["reason"]],
                                         "top": [want, got]}))  # fmt: skip
        except Exception as e:  # noqa: BLE001
            cases.append(_err(cid, e))
    passed = sum(1 for c in cases if c["pass"])
    return cases, {"snapshot_match": passed, "no_match": n_nomatch, "truncated": n_trunc,
                   "labeled": labeled, "precision_at_3": _ratio(relevant, labeled)}  # fmt: skip


def run_mentions(doc: Mapping, db: Path | None) -> dict:
    if db is None or not Path(db).is_file():
        return _skipped("mentions", "색인 파일 없음 — --db 확인")
    try:
        # 원본은 열지 않는다: LocalIndex 는 스키마 생성·commit 을 하므로 임시 사본만 연다.
        with temp_copy(Path(db)) as copy, LocalIndex(copy) as index:
            cases, metrics = _mention_cases(index, doc)
    except Exception as e:  # noqa: BLE001
        return _skipped("mentions", f"색인을 열 수 없음 ({type(e).__name__})")
    return _suite("mentions", cases, metrics)


# ----------------------------------------------------------------- judge
def _unresolved(entries: list) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for e in entries:
        fields = sorted({x["field"] for x in e.conflicts if not x.get("resolved")})
        if fields:
            out.setdefault(e.title, []).extend(fields)
    return {t: sorted(set(f)) for t, f in out.items()}


def _judge_one(c: Mapping) -> dict:
    cid = c["id"]
    now = datetime.fromisoformat(c["now"])
    obs = [observation_from_dict(o) for o in c["observations"]]
    entries = build_entries(obs, now=now)
    res = search_events(entries, c.get("request") or {}, now=now)
    exp = c["expect"]
    bad: dict[str, Any] = {}
    if "listed" in exp:
        got = sorted(e["title"] for e in res["events"])
        if got != sorted(exp["listed"]):
            bad["listed"] = [sorted(exp["listed"]), got]
    if "excluded" in exp:
        got_x = {x["title"]: x["reason"] for x in res["excluded"]}
        want_x = dict(exp["excluded"])
        if set(got_x) != set(want_x) or any(
            not got_x[t].startswith(str(r)) for t, r in want_x.items() if t in got_x
        ):
            bad["excluded"] = [want_x, got_x]
    if "unresolved_conflict_fields" in exp:
        want_u = {t: sorted(set([f] if isinstance(f, str) else f))
                  for t, f in dict(exp["unresolved_conflict_fields"]).items()}  # fmt: skip
        got_u = _unresolved(entries)
        if want_u != got_u:
            bad["unresolved_conflict_fields"] = [want_u, got_u]
    if "entry_count" in exp and exp["entry_count"] != len(entries):
        bad["entry_count"] = [exp["entry_count"], len(entries)]
    return _case(cid, not bad, bad)


def run_judge(doc: Mapping) -> dict:
    cases: list[dict] = []
    traps: dict[str, list[int]] = {}
    for c in doc.get("cases", []):
        if c.get("kind") == "guard":  # guard suite 가 맡는다
            continue
        try:
            r = _judge_one(c)
        except Exception as e:  # noqa: BLE001
            r = _err(c["id"], e)
        cases.append(r)
        t = traps.setdefault(str(c.get("trap", "")), [0, 0])
        t[1] += 1
        t[0] += r["pass"]
    return _suite("judge", cases, {"by_trap": {k: {"passed": v[0], "total": v[1]}
                                               for k, v in sorted(traps.items())}})  # fmt: skip


# ----------------------------------------------------------------- guard
def _boom(system: str, user: str) -> str:  # understand 가 막지 못하면 불린다
    raise AssertionError("LLM 이 불렸다")


def _probe(text: str) -> tuple[str, bool]:
    """(screen 판정, understand 가 LLM 호출 전에 막았는가)."""
    blocked = screen(text, "eval")
    verdict = "clean" if blocked is None else blocked.verdict
    called = False

    def complete(system: str, user: str) -> str:
        nonlocal called
        called = True
        return _boom(system, user)

    out = understand(text, complete=complete)
    codes = {p["code"] for p in out["problems"]}
    return verdict, ("INJECTION_BLOCKED" in codes) and not called


def run_guard(schedule_doc: Mapping | None, judge_doc: Mapping | None) -> dict:
    if schedule_doc is None and judge_doc is None:
        return _skipped("guard", "schedule·judge 세트 없음")
    cases: list[dict] = []
    for c in (judge_doc or {}).get("cases", []):
        if c.get("kind") != "guard":
            continue
        try:
            verdict, blocked = _probe(c["text"])
            e = c["expect"]
            ok = verdict == e["verdict"] and blocked == e["understand_blocked"]
            cases.append(_case(c["id"], ok, {"verdict": [e["verdict"], verdict],
                                             "understand_blocked": [e["understand_blocked"], blocked]}))  # fmt: skip
        except Exception as ex:  # noqa: BLE001
            cases.append(_err(c["id"], ex))
    for c in (schedule_doc or {}).get("cases", []):
        inc = (c.get("expect") or {}).get("problems_include") or []
        if "INJECTION_BLOCKED" not in inc:
            continue
        try:
            _, blocked = _probe(c["text"])
            cases.append(_case(c["id"], blocked, {"understand_blocked": [True, blocked]}))
        except Exception as ex:  # noqa: BLE001
            cases.append(_err(c["id"], ex))
    return _suite("guard", cases)


# ------------------------------------------------------------------ main
def _known_failures(path: Path | None) -> set[tuple[str, str]]:
    if path is None:
        return set()
    return {(m.group(1), m.group(2)) for m in _KNOWN.finditer(path.read_text(encoding="utf-8"))}


def _load_docs(ns: argparse.Namespace) -> tuple[dict[str, dict], bool]:
    """(suite → 문서, reviewed). 문제 있으면 ValueError."""
    docs: dict[str, dict] = {}
    if ns.set:
        whole = load_suite(Path(ns.set))
        suites = whole.get("suites")
        if not isinstance(suites, Mapping):
            raise ValueError("--set 파일에 suites 객체가 없다")
        reviewed = whole.get("reviewed") is True
        raw = {k: v for k, v in suites.items() if isinstance(k, str)}
        label = ns.set
    else:
        reviewed = False
        raw = {}
        for name in ("schedule", "gate", "mentions", "judge"):
            f = Path(ns.drafts) / f"{name}.json"
            if f.is_file():
                raw[name] = load_suite(f)
        label = ns.drafts
        print("경고: 검수되지 않은 drafts 로 실행한다 (reviewed: false)", file=sys.stderr)
    for name, doc in raw.items():
        probs = validate_suite(doc)
        if probs:
            raise ValueError(f"{label}/{name}: 형식 문제 {len(probs)}개 — {probs[0]}")
        docs[name] = doc
    return docs, reviewed


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="kc.py run")
    ap.add_argument("--set")
    ap.add_argument("--drafts", default="eval/drafts")
    ap.add_argument("--suites", default=",".join(RUNNABLE))
    ap.add_argument("--db", default="var/index/kcontext.db")
    ap.add_argument("--out", default="eval/results")
    ap.add_argument("--label", default="offline")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--known-failures")
    ns = ap.parse_args(argv)

    names = [s.strip() for s in ns.suites.split(",") if s.strip()]
    unknown = [s for s in names if s not in RUNNABLE]
    if unknown or not names:
        print(f"모르는 suite: {unknown or ns.suites} (가능: {', '.join(RUNNABLE)})", file=sys.stderr)
        return 2
    if not _LABEL.match(ns.label):
        print("--label 은 영문·숫자·_- 40자 이하", file=sys.stderr)
        return 2
    try:
        docs, reviewed = _load_docs(ns)
        known = _known_failures(Path(ns.known_failures) if ns.known_failures else None)
    except (ValueError, OSError) as e:
        print(f"세트를 읽을 수 없다: {e}", file=sys.stderr)
        return 2

    results: list[dict] = []
    for name in names:
        if name == "gate":
            r = run_gate(docs["gate"]) if "gate" in docs else _skipped(name, "gate 세트 없음")
        elif name == "judge":
            r = run_judge(docs["judge"]) if "judge" in docs else _skipped(name, "judge 세트 없음")
        elif name == "mentions":
            r = (run_mentions(docs["mentions"], Path(ns.db)) if "mentions" in docs
                 else _skipped(name, "mentions 세트 없음"))  # fmt: skip
        else:
            r = run_guard(docs.get("schedule"), docs.get("judge"))
        results.append(r)

    root = Path(__file__).resolve().parents[2]
    out_dir = Path(ns.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    path = out_dir / f"{ns.label}-{stamp}.json"
    doc = {"schema": RESULT_SCHEMA, "reviewed": reviewed, "git_head": git_head(root),
           "suites": results}  # fmt: skip
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    failures = 0
    for r in results:
        if r["status"] == "skipped":
            print(f"{r['suite']}: skipped ({r['reason']})")
            continue
        fails = [c["id"] for c in r["cases"] if not c["pass"]]
        new = [i for i in fails if (r["suite"], i) not in known]
        failures += len(new)
        print(f"{r['suite']}: {r['passed']}/{r['total']} 통과"
              + (f" · 실패 {', '.join(fails)}" if fails else ""))  # fmt: skip
    print(f"결과: {path}")
    return 1 if ns.check and failures else 0
