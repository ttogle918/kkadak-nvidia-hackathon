"""출처별 수집 실행 기록. 성공 시각·오류·재시도 상태. 실패해도 기존 데이터는 그대로다."""

from __future__ import annotations

from datetime import datetime, timedelta

from domains.kcontext.catalog.rules import to_kst

__all__ = ["backoff_minutes", "due", "record_failure", "record_success"]

BASE_RETRY_MIN = 5
MAX_RETRY_MIN = 6 * 60


def _iso(now: datetime) -> str:
    return to_kst(now).strftime("%Y-%m-%dT%H:%M")


def backoff_minutes(failures: int) -> int:
    """연속 실패 횟수에 따른 재시도 대기(분): 5, 10, 20 … 최대 6시간."""
    return min(BASE_RETRY_MIN * 2 ** max(failures - 1, 0), MAX_RETRY_MIN)


def record_success(runs: dict[str, dict], source_id: str, now: datetime, counts: dict) -> dict:
    prev = runs.get(source_id, {})
    runs[source_id] = {
        **prev,
        "last_attempt_at": _iso(now),
        "last_success_at": _iso(now),
        "last_error": None,
        "consecutive_failures": 0,
        "next_retry_at": None,
        "attempts_total": prev.get("attempts_total", 0) + 1,
        "last_counts": counts,
        "last_warning": "빈 결과" if counts.get("fetched") == 0 else None,
    }
    return runs[source_id]


def record_failure(runs: dict[str, dict], source_id: str, now: datetime, error: str) -> dict:
    prev = runs.get(source_id, {})
    failures = prev.get("consecutive_failures", 0) + 1
    runs[source_id] = {
        **prev,
        "last_attempt_at": _iso(now),
        "last_error": error[:300],
        "consecutive_failures": failures,
        "next_retry_at": _iso(now + timedelta(minutes=backoff_minutes(failures))),
        "attempts_total": prev.get("attempts_total", 0) + 1,
    }
    return runs[source_id]


def due(runs: dict[str, dict], source_id: str, now: datetime, cadence_hours: float) -> bool:
    """수집할 때가 됐는가. 실패 중이면 재시도 시각, 아니면 마지막 성공 + 주기."""
    r = runs.get(source_id)
    if not r or not r.get("last_attempt_at"):
        return True
    now_s = _iso(now)
    if r.get("next_retry_at"):
        return now_s >= r["next_retry_at"]
    last = datetime.fromisoformat(r["last_success_at"] or r["last_attempt_at"])
    return now_s >= (last + timedelta(hours=cadence_hours)).strftime("%Y-%m-%dT%H:%M")
