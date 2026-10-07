"""제보·수정 요청. 공식 링크와 사유를 받아 **검토 대기**로만 저장한다 — 제출 즉시 공개 행사가 되지 않는다.

- 제출 내용은 신뢰할 수 없는 입력이다: 길이를 제한하고 제어문자를 지우며 ``core.guard`` 로 주입 문구를 거른다.
- 검토(승인·반려)는 사람만 한다. 신원은 호출한 쪽(backend)이 주입하고, ``agent:`` 로 시작하는 신원은 거부한다(D2).
- 승인된 새 행사 제보만 ``report`` 출처의 관찰값이 되고, 그래도 공식 출처가 아니므로 항목의 검증 상태는
  ``needs_check`` 다(공식으로 확인되면 다른 출처와 합쳐져 검증된다).
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from datetime import datetime
from urllib.parse import urlsplit

from core.guard import Verdict, scan
from domains.kcontext.contract.text import is_date, is_hhmm
from domains.kcontext.regions import Region

from .model import Evidence, Observation, Schedule
from .rules import classify_venue, norm_text, to_kst
from .store import CatalogStore
from .updater import rebuild

__all__ = ["ReportError", "decide", "list_reports", "submit"]

KINDS = ("new_event", "correction", "cancel_notice", "other")
DECISIONS = ("approve", "reject")
_CTRL = re.compile("[\x00-\x08\x0b-\x1f\x7f\u200b-\u200d\u2060\ufeff]")
MAX_REASON = 1000
MAX_FIELD = 200


class ReportError(ValueError):
    pass


def _clean(v: object, limit: int) -> str:
    return norm_text(_CTRL.sub("", v if isinstance(v, str) else ""))[:limit]


def _link(v: object) -> str:
    s = _clean(v, 500)
    p = urlsplit(s)
    if p.scheme not in ("http", "https") or not p.hostname or "." not in p.hostname:
        raise ReportError("공식 링크(http·https 주소)가 필요하다")
    return s


def submit(store: CatalogStore, payload: Mapping, *, now: datetime) -> dict:
    kind = payload.get("kind", "other")
    if kind not in KINDS:
        raise ReportError(f"kind 는 {'|'.join(KINDS)}")
    link = _link(payload.get("official_link"))
    reason = _clean(payload.get("reason"), MAX_REASON)
    if len(reason) < 5:
        raise ReportError("제보 사유를 5자 이상 적어야 한다")
    fields_in = payload.get("fields") if isinstance(payload.get("fields"), Mapping) else {}
    fields = {k: _clean(fields_in.get(k), MAX_FIELD) for k in
              ("title", "start_date", "end_date", "start_time", "venue_name", "venue_address", "note")
              if fields_in.get(k)}
    for k in ("start_date", "end_date"):
        if k in fields and not is_date(fields[k]):
            raise ReportError(f"{k} 는 YYYY-MM-DD")
    if "start_time" in fields and not is_hhmm(fields["start_time"]):
        raise ReportError("start_time 은 HH:MM")
    entry_id = _clean(payload.get("entry_id"), 40)
    if kind in ("correction", "cancel_notice") and not entry_id:
        raise ReportError("수정·취소 제보에는 entry_id 가 필요하다")
    if kind == "new_event" and not fields.get("title"):
        raise ReportError("새 행사 제보에는 행사명(fields.title)이 필요하다")
    blob = "\n".join([reason, *fields.values()])
    if scan(blob).verdict is Verdict.INJECTION:
        raise ReportError("지시문으로 보이는 내용이 들어 있어 받을 수 없다")
    stamp = to_kst(now).strftime("%Y-%m-%dT%H:%M")
    rid = "rpt_" + hashlib.sha1(f"{stamp}|{link}|{reason}".encode()).hexdigest()[:10]
    with store.lock():
        reports = store.load_reports()
        if any(r["id"] == rid for r in reports):
            return next(r for r in reports if r["id"] == rid)
        rec = _new_record(rid, kind, link, reason, fields, entry_id, stamp)
        store.save_reports([*reports, rec])
    return rec


def _new_record(rid: str, kind: str, link: str, reason: str, fields: dict, entry_id: str, stamp: str) -> dict:
    return {"id": rid, "kind": kind, "status": "pending", "official_link": link, "reason": reason,
           "fields": fields, "entry_id": entry_id or None, "submitted_at": stamp,
           "decided_at": None, "decided_by": None, "note": None, "applied_obs_id": None}


def list_reports(store: CatalogStore, status: str | None = None) -> list[dict]:
    return [r for r in store.load_reports() if status in (None, r["status"])]


def decide(
    store: CatalogStore, report_id: str, decision: str, *, reviewer: str, now: datetime,
    region: Region, note: str = "",
) -> dict:
    """사람 검토. 승인된 새 행사 제보는 ``report`` 출처 관찰값으로 반영한다(검증은 needs_check)."""
    if decision not in DECISIONS:
        raise ReportError(f"decision 은 {'|'.join(DECISIONS)}")
    who = reviewer.strip() if isinstance(reviewer, str) else ""
    if not who or who.casefold().startswith("agent:"):
        raise ReportError("검토자 신원이 올바르지 않다 (agent: 신원은 승인할 수 없다)")
    with store.lock():
        reports = store.load_reports()
        rec = next((r for r in reports if r["id"] == report_id), None)
        if rec is None:
            raise ReportError("제보를 찾을 수 없다")
        if rec["status"] != "pending":
            raise ReportError("이미 검토한 제보다")
        stamp = to_kst(now).strftime("%Y-%m-%dT%H:%M")
        rec.update(status="accepted" if decision == "approve" else "rejected", decided_at=stamp,
                   decided_by=who, note=_clean(note, 300) or None)
        if decision == "approve" and rec["kind"] == "new_event":
            f = rec["fields"]
            venue = classify_venue(name=f.get("venue_name", ""), address=f.get("venue_address", ""),
                                   region=region)
            obs = Observation(
                obs_id=f"report:{rec['id']}", title=f["title"],
                venue=venue,
                schedule=Schedule(start_date=f.get("start_date"), end_date=f.get("end_date")),
                description=f.get("note", ""),
                evidence=Evidence(source_id="user_report", source_name="이용자 제보(검토 승인)", kind="report",
                                  url=rec["official_link"], quote=f"이용자 제보 — {f['title']}"[:200],
                                  origin=f"report:{rec['id']}", collected_at=stamp[:10]),
            )
            obs_store = store.load_observations()
            obs_store[obs.obs_id] = {"observation": obs, "source_id": "user_report",
                                     "first_seen_at": stamp, "last_seen_at": stamp}
            store.save_observations(obs_store)
            rec["applied_obs_id"] = obs.obs_id
            store.save_reports(reports)
            rebuild(store, now)
        else:
            store.save_reports(reports)
        return rec
