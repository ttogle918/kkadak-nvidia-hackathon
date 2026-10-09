"""평가셋 형식 ``kc-eval/v1`` 읽기·검증. 형식 정의는 docs/sprints/sprint-3.md §5.1."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path

__all__ = ["SCHEMA", "SUITES", "load_suite", "main_validate", "validate_suite"]

SCHEMA = "kc-eval/v1"
SUITES = ("schedule", "gate", "mentions", "judge")
_ID = re.compile(r"^[a-z0-9_]{1,48}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_ANCHOR_TYPES = ("visit", "hotel")
_VERDICTS = ("injection", "suspicious", "clean")


def load_suite(path: Path) -> dict:
    """JSON 객체 하나를 읽는다. 읽을 수 없거나 객체가 아니면 ValueError."""
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"{path}: 읽을 수 없다 ({type(e).__name__})") from e
    if not isinstance(doc, dict):
        raise ValueError(f"{path}: JSON 객체가 아니다")  # noqa: TRY004
    return doc


def _is_date_or_null(v: object, *, star: bool = True) -> bool:
    return v is None or (star and v == "*") or (isinstance(v, str) and bool(_DATE.match(v)))


def _is_time_or_null(v: object) -> bool:
    return v is None or v == "*" or (isinstance(v, str) and bool(_HHMM.match(v)))


def _schedule_case(c: Mapping, p: list[str], where: str) -> None:
    if not isinstance(c.get("text"), str) or not c["text"].strip():
        p.append(f"{where}: text 는 비어 있지 않은 문자열")
    trip = c.get("trip")
    if trip is not None and not (
        isinstance(trip, Mapping) and _is_date_or_null(trip.get("from"), star=False)
        and _is_date_or_null(trip.get("to"), star=False)
    ):  # fmt: skip
        p.append(f"{where}: trip 은 null 또는 {{from,to}} (YYYY-MM-DD)")
    exp = c.get("expect")
    if not isinstance(exp, Mapping) or exp.get("status") not in ("ok", "no_anchors"):
        p.append(f"{where}: expect.status 는 ok|no_anchors")
        return
    anchors = exp.get("anchors", [])
    if not isinstance(anchors, list):
        p.append(f"{where}: expect.anchors 는 목록")
        return
    if exp["status"] == "ok" and not anchors:
        p.append(f"{where}: status ok 인데 anchors 가 비어 있다")
    for i, a in enumerate(anchors):
        w = f"{where}.anchors[{i}]"
        if not isinstance(a, Mapping):
            p.append(f"{w}: 객체 필요")
            continue
        if a.get("type") not in _ANCHOR_TYPES:
            p.append(f"{w}: type 은 visit|hotel")
        if not isinstance(a.get("name"), str) or not a["name"].strip():
            p.append(f"{w}: name 필요")
        if not _is_date_or_null(a.get("date")):
            p.append(f"{w}: date 형식 오류")
        for k in ("from", "to"):
            if not _is_time_or_null(a.get(k)):
                p.append(f"{w}: {k} 는 HH:MM, null, \"*\"")
    inc = exp.get("problems_include", [])
    if not isinstance(inc, list) or not all(isinstance(x, str) for x in inc):
        p.append(f"{where}: problems_include 는 문자열 목록")


def _gate_case(c: Mapping, p: list[str], where: str) -> None:
    if not isinstance(c.get("text"), str) or not c["text"].strip():
        p.append(f"{where}: text 는 비어 있지 않은 문자열")
    exp = c.get("expect")
    if not isinstance(exp, Mapping) or not isinstance(exp.get("schedule"), bool):
        p.append(f"{where}: expect.schedule 은 bool")


def _mentions_case(c: Mapping, p: list[str], where: str) -> None:
    if not isinstance(c.get("anchor"), str) or not c["anchor"].strip():
        p.append(f"{where}: anchor 필요")
    lim = c.get("limit")
    if isinstance(lim, bool) or not isinstance(lim, int) or lim < 1:
        p.append(f"{where}: limit 은 1 이상 정수")
    exp = c.get("expect")
    if not isinstance(exp, Mapping):
        p.append(f"{where}: expect 객체 필요")
        return
    top = exp.get("top")
    if not isinstance(top, list):
        p.append(f"{where}: expect.top 은 목록")
        return
    for i, t in enumerate(top):
        if not isinstance(t, Mapping) or not isinstance(t.get("article_id"), str):
            p.append(f"{where}.top[{i}]: article_id 필요")
        elif t.get("relevant") not in (None, True, False):
            p.append(f"{where}.top[{i}]: relevant 는 null|bool")


def _judge_case(c: Mapping, p: list[str], where: str) -> None:
    exp = c.get("expect")
    if not isinstance(exp, Mapping):
        p.append(f"{where}: expect 객체 필요")
        return
    if c.get("kind") == "guard":
        if not isinstance(c.get("text"), str):
            p.append(f"{where}: text 필요")
        if exp.get("verdict") not in _VERDICTS:
            p.append(f"{where}: expect.verdict 는 injection|suspicious|clean")
        if not isinstance(exp.get("understand_blocked"), bool):
            p.append(f"{where}: expect.understand_blocked 는 bool")
        return
    if not isinstance(c.get("trap"), str):
        p.append(f"{where}: trap 필요")
    if not isinstance(c.get("now"), str):
        p.append(f"{where}: now 필요(ISO 시각)")
    obs = c.get("observations")
    if not isinstance(obs, list) or not obs:
        p.append(f"{where}: observations 는 비어 있지 않은 목록")
    if not isinstance(c.get("request"), Mapping):
        p.append(f"{where}: request 객체 필요")
    if "listed" in exp and not isinstance(exp["listed"], list):
        p.append(f"{where}: expect.listed 는 목록")
    if "excluded" in exp and not isinstance(exp["excluded"], Mapping):
        p.append(f"{where}: expect.excluded 는 {{제목: 사유}}")
    if "entry_count" in exp and (
        isinstance(exp["entry_count"], bool) or not isinstance(exp["entry_count"], int)
    ):
        p.append(f"{where}: expect.entry_count 는 정수")


_CASE_CHECK = {
    "schedule": _schedule_case, "gate": _gate_case,
    "mentions": _mentions_case, "judge": _judge_case,
}  # fmt: skip


def validate_suite(doc: Mapping) -> list[str]:
    """형식 문제 목록(비어 있으면 통과). 값의 옳고 그름은 보지 않는다."""
    p: list[str] = []
    if not isinstance(doc, Mapping):
        return ["최상위가 객체가 아니다"]
    if doc.get("schema") != SCHEMA:
        p.append(f"schema 는 {SCHEMA!r}")
    suite = doc.get("suite")
    if suite not in SUITES:
        p.append(f"suite 는 {'|'.join(SUITES)}")
    if not isinstance(doc.get("created_at"), str) or not _DATE.match(doc["created_at"]):
        p.append("created_at 은 YYYY-MM-DD")
    for k in ("reviewed", "synthetic"):
        if not isinstance(doc.get(k), bool):
            p.append(f"{k} 는 bool")
    if not isinstance(doc.get("provenance"), str) or not doc["provenance"].strip():
        p.append("provenance 는 비어 있지 않은 한 줄")
    if suite == "mentions" and doc.get("synthetic") is False:
        idx = doc.get("index")
        need = ("db", "measured_at", "total_chunks", "fts_enabled", "alias_rows")
        if not isinstance(idx, Mapping) or any(k not in idx for k in need):
            p.append(f"mentions: index 블록({', '.join(need)}) 필요")
    cases = doc.get("cases")
    if not isinstance(cases, list):
        return [*p, "cases 는 목록"]
    seen: set[str] = set()
    for i, c in enumerate(cases):
        cid = c.get("id") if isinstance(c, Mapping) else None
        where = f"cases[{i}]" + (f"({cid})" if isinstance(cid, str) else "")
        if not isinstance(c, Mapping):
            p.append(f"{where}: 객체 필요")
            continue
        if not isinstance(cid, str) or not _ID.match(cid):
            p.append(f"{where}: id 는 ^[a-z0-9_]{{1,48}}$")
        elif cid in seen:
            p.append(f"{where}: id 중복")
        else:
            seen.add(cid)
        tags = c.get("tags")
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            p.append(f"{where}: tags 는 문자열 목록")
        if suite in _CASE_CHECK:
            _CASE_CHECK[suite](c, p, where)
    return p


def main_validate(argv: list[str]) -> int:
    """``validate`` 하위 명령: drafts 의 모든 *.json 을 검증. 문제 있으면 1, 읽기·경로 오류 2."""
    ap = argparse.ArgumentParser(prog="kc.py validate")
    ap.add_argument("--drafts", default="eval/drafts")
    ns = ap.parse_args(argv)
    d = Path(ns.drafts)
    if not d.is_dir():
        print(f"drafts 디렉터리가 없다: {d}", file=sys.stderr)
        return 2
    bad = 0
    files = sorted(d.glob("*.json"))
    for f in files:
        try:
            probs = validate_suite(load_suite(f))
        except ValueError as e:
            probs = [str(e)]
        print(f"{f.name}: {'OK' if not probs else f'{len(probs)}개 문제'}")
        for line in probs:
            print(f"  - {line}")
        bad += bool(probs)
    if not files:
        print("검증할 파일이 없다")
    return 1 if bad else 0


