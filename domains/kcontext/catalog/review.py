"""관리자 검토 목록: 신규·변경 행사, 정보 충돌과 누락, 수집 오류, 참여조건 확인 필요, 제보, 수동 확인 링크."""

from __future__ import annotations

from datetime import datetime, timedelta

from .query import participation
from .rules import to_kst
from .store import CatalogStore

__all__ = ["review_queue"]

CORE_MISSING = ("dates", "sessions", "venue", "region", "hours")


def _item(e) -> dict:
    return {"id": e.id, "title": e.title, "verification": e.verification,
            "last_verified_at": e.last_verified_at,
            "links": [ev.url for ev in e.evidence if ev.url][:3]}


def review_queue(store: CatalogStore, sources: list[dict], *, now: datetime, recent_days: int = 7) -> dict:
    now = to_kst(now)
    entries = [e for e in store.load_entries() if not e.demo]
    since = (now - timedelta(days=recent_days)).strftime("%Y-%m-%dT%H:%M")
    recent = [c for c in store.load_changes() if c["detected_at"] >= since]
    by_id = {e.id: e for e in entries}
    changed: dict[str, dict] = {}
    for c in recent:
        if c["entry_id"] in by_id:
            slot = changed.setdefault(c["entry_id"], {**_item(by_id[c["entry_id"]]), "changes": []})
            slot["changes"].append({k: c[k] for k in ("field", "old", "new", "detected_at", "importance")})
    runs, checks = store.load_runs(), store.load_link_checks()
    errors, stale, manual = [], [], []
    for s in sources:
        r = runs.get(s["id"])
        if r and (r.get("last_error") or r.get("consecutive_failures")):
            errors.append({"source_id": s["id"], "name": s["name"], "error": r.get("last_error"),
                           "consecutive_failures": r.get("consecutive_failures", 0),
                           "next_retry_at": r.get("next_retry_at"), "last_success_at": r.get("last_success_at")})
        if s["status"] == "manual_only":
            chk = checks.get(s["id"])
            due = not chk or chk["checked_at"] < (now - timedelta(hours=s["cadence_hours"])).strftime("%Y-%m-%dT%H:%M")
            manual.append({"source_id": s["id"], "name": s["name"], "links": s.get("links") or [{"url": s["url"]}],
                           "notes": s["notes"], "last_check": chk, "due": due})
        elif s["status"] == "implemented" and r and r.get("last_success_at"):
            limit = (now - timedelta(hours=s["cadence_hours"] * 2)).strftime("%Y-%m-%dT%H:%M")
            if r["last_success_at"] < limit:
                stale.append({"source_id": s["id"], "last_success_at": r["last_success_at"]})
    return {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M"),
        "new_or_changed": sorted(changed.values(), key=lambda x: x["changes"][-1]["detected_at"], reverse=True),
        "conflicts": [{**_item(e), "conflicts": [dict(c) for c in e.conflicts if not c["resolved"]]}
                      for e in entries if e.verification == "conflict"],
        "missing_info": [{**_item(e), "missing": [k for k in e.needs_check if k in CORE_MISSING]}
                         for e in entries if any(k in CORE_MISSING for k in e.needs_check)],
        "eligibility_check": [{**_item(e), "reasons": participation(e)["reasons"]}
                              for e in entries if participation(e)["status"] == "unverified"
                              or participation(e)["needs_check"]],
        "collection_errors": errors,
        "stale_sources": stale,
        "reports_pending": [r for r in store.load_reports() if r["status"] == "pending"],
        "manual_links": manual,
    }
