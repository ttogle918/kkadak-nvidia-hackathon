"""보안 로그 항목(AuditEntry, sprint-2 §5.1)을 만드는 순수 함수. I/O 없음."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
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
    """aware(UTC) 로 정규화한다. naive 는 UTC 로 본다. 실패하면 ValueError."""
    if not isinstance(ts, str):
        raise TypeError("ts 가 문자열이 아니다")
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None or dt.utcoffset() is None:
        dt = dt.replace(tzinfo=UTC)
    try:
        return dt.astimezone(UTC)
    except OverflowError:
        raise ValueError("ts 범위 초과") from None


def _hms(ts: str) -> str:
    try:
        return _parse(ts).astimezone(_SEOUL).strftime("%H:%M:%S")
    except OverflowError:
        raise ValueError("ts 범위 초과") from None


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
    return _safe_events(events, run_id)[0]


def _safe_events(
    events: Iterable[AuditEvent], run_id: str
) -> tuple[list[dict[str, Any]], int]:
    """변환에 실패한 이벤트(깨진 ts 등)는 건너뛰고 개수를 센다."""
    out: list[dict[str, Any]] = []
    skipped = 0
    for e in events:
        try:
            x = _event_entry(e, run_id)
        except (ValueError, TypeError, AttributeError, OverflowError):
            skipped += 1
            continue
        if x is not None:
            out.append(x)
    return out, skipped


def build_entries_counted(
    drafts: Iterable[Draft], events_by_run: Mapping[str, list[AuditEvent]]
) -> tuple[list[dict[str, Any]], int]:
    """(정렬된 항목, 건너뛴 이벤트·초안 수). 시각이 섞여도 정렬이 터지지 않는다."""
    entries: list[dict[str, Any]] = []
    skipped = 0
    for d in drafts:
        if d.kind not in SECURITY_DRAFT_KINDS:
            continue
        try:
            entries.append(entry_from_draft(d))
        except (ValueError, TypeError, OverflowError):
            skipped += 1
    for run_id, events in events_by_run.items():
        got, n = _safe_events(events, run_id)
        entries.extend(got)
        skipped += n
    entries.sort(key=lambda x: (_parse(x["at"]), x["id"]))
    return entries, skipped


def build_entries(
    drafts: Iterable[Draft], events_by_run: Mapping[str, list[AuditEvent]]
) -> list[dict[str, Any]]:
    return build_entries_counted(drafts, events_by_run)[0]
