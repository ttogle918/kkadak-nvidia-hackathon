"""backend 가 별도 프로세스로 부르는 JSON 진입점(D10: backend 는 domains 를 import 하지 않는다).

    echo '{"op": "search", "args": {...}, "actor": "..."}' | python -m domains.kcontext.catalog.api

표준 입력 한 건 → 표준 출력 JSON 한 건. 예상된 오류(검증 실패 등)는 ``{"error": {"code", "message"}}`` 로 돌려주고
종료 코드 0, 예상하지 못한 오류는 종료 코드 1 이다. 관리자 작업(op 이름이 ``admin_`` 으로 시작)은 ``actor`` 가
``agent:`` 로 시작하면 거부한다(D2) — 실제 권한 확인은 backend 가 한다.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from domains.kcontext.contract.errors import ContractError
from domains.kcontext.regions import load_regions

from . import reports as reports_mod
from .fit import FitConfig, add_to_itinerary, fit_event, remove_from_itinerary, validate_itinerary
from .query import search_events, summarize_entry
from .review import review_queue
from .routes import NullRouteProvider, RouteProvider
from .rules import KST, to_kst
from .sources import SourceError, load_sources, make_fetcher
from .store import CatalogStore
from .stories import link_stories, load_stories
from .updater import run_source

__all__ = ["ApiError", "handle", "main"]

ADMIN_OPS = {"admin_review_queue", "admin_reports", "admin_report_decide", "admin_refresh",
             "admin_link_check", "admin_sources"}
_STATUS_RANK = {"fit": 0, "check_needed": 1, "no_fit": 2}


class ApiError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _coverage(store: CatalogStore, sources: list[dict]) -> dict:
    runs = store.load_runs()
    return {
        "entries_built_at": store.entries_built_at(),
        "sources": [{"id": s["id"], "name": s["name"], "method": s["method"], "status": s["status"],
                     "url": s["url"], "last_success_at": (runs.get(s["id"]) or {}).get("last_success_at"),
                     "last_error": (runs.get(s["id"]) or {}).get("last_error")}
                    for s in sources],
    }


def _search(a: Mapping, store: CatalogStore, sources: list[dict], now: datetime,
            provider: RouteProvider) -> dict:
    entries = store.load_entries()
    res = search_events(entries, a, now=now, coverage=_coverage(store, sources))
    res["catalog_empty"] = not entries
    itin_raw = a.get("itinerary")
    if isinstance(itin_raw, list):
        itin, problems = validate_itinerary(itin_raw)
        res["problems"] = [*res["problems"], *problems]
        cfg = FitConfig(
            max_extra_minutes=int(a.get("max_extra_minutes", 30)),
            assumed_duration_min=int(a["assumed_duration_min"]) if a.get("assumed_duration_min") else None)
        sug: list[dict] = []
        for e in res["events"]:
            sug.extend(fit_event(e, itin, provider, cfg=cfg, origin=a.get("origin"),
                                 free_slots=a.get("free_slots") or ()))
        sug.sort(key=lambda s: (_STATUS_RANK[s["status"]],
                                s["extra_minutes"] if s["extra_minutes"] is not None else 10**6,
                                s["date"], s["session"]["start_time"]))
        res["suggestions"] = sug
    return res


def _changes_for(store: CatalogStore, ids: list[str], since: str | None) -> list[dict]:
    by: dict[str, dict] = {}
    titles = {e.id: e.title for e in store.load_entries()}
    for c in store.load_changes():
        if c["entry_id"] in ids and c["field"] != "__new__" and (not since or c["detected_at"] > since):
            slot = by.setdefault(c["entry_id"], {"entry_id": c["entry_id"],
                                                 "title": titles.get(c["entry_id"], c.get("title", "")),
                                                 "changes": [], "has_major": False})
            slot["changes"].append({k: c[k] for k in ("field", "old", "new", "detected_at", "importance")})
            slot["has_major"] = slot["has_major"] or c["importance"] == "major"
    return list(by.values())


def handle(
    op: str, args: Mapping, *, store: CatalogStore, now: datetime, actor: str | None = None,
    env: Mapping[str, str] | None = None, provider: RouteProvider | None = None,
    stories_dir: Path | None = None,
) -> dict:
    now = to_kst(now)
    sources = load_sources()
    provider = provider or NullRouteProvider()
    region_id = os.environ.get("KC_TARGET_REGION", "jung")
    region = load_regions()[region_id]
    if op in ADMIN_OPS:
        who = (actor or "").strip()
        if not who or who.casefold().startswith("agent:"):
            raise ApiError("forbidden", "관리자 작업은 사람 신원이 필요하다")
    if op == "search":
        return _search(args, store, sources, now, provider)
    if op == "detail":
        entry = next((e for e in store.load_entries() if e.id == args.get("entry_id")), None)
        if entry is None:
            raise ApiError("not_found", "행사를 찾을 수 없다")
        out = summarize_entry(entry, now)
        out["history"] = [c for c in store.load_changes() if c["entry_id"] == entry.id]
        out["stories"] = link_stories(entry, load_stories(stories_dir), lang=args.get("lang", "ko"),
                                      include_synthetic=bool(args.get("demo")))
        out["coverage"] = _coverage(store, sources)
        return out
    if op == "itinerary_add":
        for k in ("entry_id", "date", "start_time", "itinerary"):
            if k not in args:
                raise ApiError("bad_request", f"{k} 가 필요하다")
        res = _search({**args, "trip": {"from": args["date"], "to": args["date"]},
                       "include_demo": bool(args.get("demo"))}, store, sources, now, provider)
        ev = next((e for e in res["events"] if e["id"] == args["entry_id"]), None)
        sug = next((s for s in res.get("suggestions", []) if s["entry_id"] == args["entry_id"]
                    and s["date"] == args["date"] and s["session"]["start_time"] == args["start_time"]), None)
        if ev is None or sug is None:
            raise ApiError("not_found", "이 날짜·회차로 추가할 수 있는 행사가 아니다")
        if sug["status"] == "no_fit" and not args.get("force"):
            raise ApiError("conflict", "기존 일정과 맞지 않는다: " + "; ".join(r["ko"] for r in sug["reasons"]))
        try:
            return {"itinerary": add_to_itinerary(args["itinerary"], sug, ev), "suggestion": sug}
        except ValueError as e:
            raise ApiError("bad_request", str(e)) from None
    if op == "itinerary_remove":
        return {"itinerary": remove_from_itinerary(args.get("itinerary") or [], str(args.get("item_id", "")))}
    if op == "saved_changes":
        ids = [x for x in (args.get("ids") or []) if isinstance(x, str)]
        return {"saved": _changes_for(store, ids, args.get("since"))}
    if op == "report_submit":
        try:
            return {"report": reports_mod.submit(store, args, now=now)}
        except reports_mod.ReportError as e:
            raise ApiError("bad_request", str(e)) from None
    if op == "public_sources":
        return {"coverage": _coverage(store, sources)}
    if op == "admin_sources":
        return {"sources": sources, "runs": store.load_runs(), "link_checks": store.load_link_checks()}
    if op == "admin_review_queue":
        return review_queue(store, sources, now=now)
    if op == "admin_reports":
        return {"reports": reports_mod.list_reports(store, args.get("status"))}
    if op == "admin_report_decide":
        try:
            return {"report": reports_mod.decide(store, str(args.get("report_id", "")),
                                                 str(args.get("decision", "")), reviewer=actor or "", now=now,
                                                 region=region, note=str(args.get("note", "")))}
        except reports_mod.ReportError as e:
            raise ApiError("bad_request", str(e)) from None
    if op == "admin_link_check":
        sid = str(args.get("source_id", ""))
        if sid not in {s["id"] for s in sources}:
            raise ApiError("not_found", "알 수 없는 출처")
        with store.lock():
            checks = store.load_link_checks()
            checks[sid] = {"checked_at": now.strftime("%Y-%m-%dT%H:%M"), "checked_by": actor,
                           "note": str(args.get("note", ""))[:300]}
            store.save_link_checks(checks)
        return {"link_check": checks[sid]}
    if op == "admin_refresh":
        sid = str(args.get("source_id", ""))
        try:
            fetch = make_fetcher(sid, region=region, now=now, env=env)  # sample 키 수집은 CLI(--dir 지정) 전용
        except SourceError as e:
            raise ApiError("not_implemented", str(e)) from None
        return {"run": run_source(store, sid, fetch, now=now).__dict__}
    raise ApiError("bad_request", f"알 수 없는 op: {op}")


def main() -> int:
    def out_error(code: str, message: str) -> int:
        print(json.dumps({"error": {"code": code, "message": message}}, ensure_ascii=False))
        return 0

    try:
        req = json.loads(sys.stdin.read())
        if not isinstance(req, dict) or not isinstance(req.get("op"), str):
            raise ApiError("bad_request", "{op, args, actor} 형식이어야 한다")
        store = CatalogStore(Path(os.environ["KC_CATALOG_DIR"]) if os.environ.get("KC_CATALOG_DIR") else None)
        out = handle(req["op"], req.get("args") or {}, store=store, now=datetime.now(KST),
                     actor=req.get("actor"), env=dict(os.environ))  # .env 는 읽지 않는다 — 필요한 키 하나는 호출한 쪽이 env 로 준다
    except ApiError as e:
        return out_error(e.code, str(e))
    except ContractError:  # 저장된 파일이 손상됐다 — 요청 잘못이 아니라 서버 쪽 문제다
        return out_error("internal_error", "저장된 카탈로그를 읽을 수 없다")
    except (ValueError, KeyError, TypeError) as e:
        return out_error("bad_request", f"요청을 처리할 수 없다 ({type(e).__name__})")
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
