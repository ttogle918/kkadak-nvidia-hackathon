"""보안 로그 항목(AuditEntry, sprint-2 §5.1)을 만드는 순수 함수. I/O 없음."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from core.audit import AuditEvent
from core.hitl import Draft, DraftState

SECURITY_DRAFT_KINDS = ("source_request", "policy_proposal")
DENY_ERROR_TYPES = ("InjectionBlocked", "PathDenied", "SourceNotAllowed")

_SEOUL = ZoneInfo("Asia/Seoul")
_DRAFT_KIND = {
    DraftState.DRAFT: "pend",
    DraftState.APPROVED: "approved",
    DraftState.REJECTED: "rejected",
}


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def _hms(ts: str) -> str:
    return _parse(ts).astimezone(_SEOUL).strftime("%H:%M:%S")


def _count(v: Any) -> int:
    if isinstance(v, bool):
        return 0
    if isinstance(v, int):
        return max(v, 0)
    if isinstance(v, (list, tuple, dict)):
        return len(v)
    return 0


def _draft_text(d: Draft) -> dict[str, str]:
    p = d.payload if isinstance(d.payload, dict) else {}
    if d.kind == "source_request" and isinstance(p.get("host"), str) and p["host"].strip():
        host = p["host"].strip()
        return {"ko": f"{host} · 허용 목록에 없음", "en": f"{host} · not on the allow list"}
    if d.kind == "policy_proposal":
        s = p.get("summary")
        s = s if isinstance(s, dict) else {}
        n, m = _count(s.get("network")), _count(s.get("files"))
        return {
            "ko": f"정책 초안 · 네트워크 {n} · 파일 {m}",
            "en": f"Policy draft · network {n} · files {m}",
        }
    return {"ko": f"{d.kind} 요청", "en": f"{d.kind} request"}


def entry_from_draft(d: Draft) -> dict[str, Any]:
    return {
        "id": f"draft:{d.id}",
        "time": _hms(d.created_at),
        "at": d.created_at,
        "kind": _DRAFT_KIND[d.state],
        "text": _draft_text(d),
        "decided_by": d.decided_by,
        "decided_at": d.decided_at,
        "origin": "hitl",
    }


def _event_entry(e: AuditEvent, run_id: str) -> dict[str, Any] | None:
    kind: str
    text: dict[str, str]
    if e.phase == "error" and e.kind == "tool":
        if e.data.get("error_type") not in DENY_ERROR_TYPES:
            return None
        msg = str(e.data.get("message", ""))
        kind, text = "deny", {"ko": msg, "en": msg}
    elif e.phase == "observe" and e.kind == "net":
        hp = f"{e.data.get('host')}:{e.data.get('port')}"
        if e.data.get("decision") == "denied":
            kind, text = "deny", {"ko": f"{hp} 차단", "en": f"{hp} blocked"}
        elif e.data.get("decision") == "allowed":
            kind, text = "ok", {"ko": f"{hp} 허용", "en": f"{hp} allowed"}
        else:
            return None
    elif e.phase == "result" and e.kind == "tool" and e.name.startswith("kc_"):
        kind, text = "ok", {"ko": f"{e.name} 실행", "en": f"{e.name} ran"}
    else:
        return None
    return {
        "id": f"audit:{run_id}:{e.seq}",
        "time": _hms(e.ts),
        "at": e.ts,
        "kind": kind,
        "text": text,
        "decided_by": None,
        "decided_at": None,
        "origin": "audit",
    }


def entries_from_events(events: Iterable[AuditEvent], *, run_id: str) -> list[dict[str, Any]]:
    out = (_event_entry(e, run_id) for e in events)
    return [x for x in out if x is not None]


def build_entries(
    drafts: Iterable[Draft], events_by_run: Mapping[str, list[AuditEvent]]
) -> list[dict[str, Any]]:
    entries = [entry_from_draft(d) for d in drafts if d.kind in SECURITY_DRAFT_KINDS]
    for run_id, events in events_by_run.items():
        entries.extend(entries_from_events(events, run_id=run_id))
    entries.sort(key=lambda x: (_parse(x["at"]), x["id"]))
    return entries
