"""수집 → 병합 → 변경 비교 → 저장. 실패해도 기존 데이터를 그대로 둔다.

- 수집이 실패하면 오류만 기록한다(재시도 대기 포함). 관찰값·항목은 바뀌지 않는다.
- 성공한 수집에서 **보이지 않는** 관찰값(게시글 삭제·목록에서 빠짐)은 지우지 않고, 그것만으로 취소 처리하지 않는다.
  마지막으로 확인된 시각(``last_seen_at``)이 오래된 채로 남을 뿐이다. 취소는 출처가 알릴 때만 반영된다(merge).
- 빈 결과도 성공으로 기록하되 경고를 남긴다.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime

from core.audit.redact import redact_text

from .changes import diff_catalog
from .merge import build_entries
from .model import Observation
from .rules import to_kst
from .runlog import due, record_failure, record_success
from .store import CatalogStore

__all__ = ["RunResult", "rebuild", "run_due", "run_source"]


@dataclass(frozen=True)
class RunResult:
    source_id: str
    ok: bool
    fetched: int = 0
    new_entries: int = 0
    changes: int = 0
    error: str | None = None


def _iso(now: datetime) -> str:
    return to_kst(now).strftime("%Y-%m-%dT%H:%M")


def _safe_error(e: BaseException) -> str:
    return f"{type(e).__name__}: {redact_text(str(e))}"[:300]


def rebuild(store: CatalogStore, now: datetime) -> tuple[int, int]:
    """저장된 관찰값 전체로 항목을 다시 만들고 변경을 이력에 남긴다. (새 항목 수, 변경 수)."""
    obs_store = store.load_observations()
    old = store.load_entries()
    prior = {k: e.id for e in old for k in e.external_ids}
    seen = {k: v["last_seen_at"] for k, v in obs_store.items()}
    entries = build_entries([v["observation"] for v in obs_store.values()], now=now,
                            verified_at=_iso(now), prior=prior, seen_at=seen)
    changes = diff_catalog(old, entries, _iso(now)) if old else diff_catalog([], entries, _iso(now))
    # 처음 만들 때(이전 항목이 없음)는 전부 새 항목이지만, 알림 폭주를 막기 위해 기록은 남기고 구분한다.
    store.append_changes([c.to_dict() for c in changes])
    store.save_entries(entries, _iso(now))
    return sum(1 for c in changes if c.field == "__new__"), len(changes)


def run_source(
    store: CatalogStore, source_id: str, fetch: Callable[[], list[Observation]], *, now: datetime
) -> RunResult:
    try:
        fetched = fetch()  # 네트워크 호출은 잠금 밖에서 한다
    except Exception as e:  # noqa: BLE001 - 어떤 수집 오류든 기존 데이터를 지키고 기록만 한다
        err = _safe_error(e)
        with store.lock():
            runs = store.load_runs()
            record_failure(runs, source_id, now, err)
            store.save_runs(runs)
        return RunResult(source_id, False, error=err)
    with store.lock():
        runs = store.load_runs()
        obs_store = store.load_observations()
        stamp = _iso(now)
        for o in fetched:
            prev = obs_store.get(o.obs_id)
            obs_store[o.obs_id] = {
                "observation": o, "source_id": source_id,
                "first_seen_at": prev["first_seen_at"] if prev else stamp, "last_seen_at": stamp,
            }
        store.save_observations(obs_store)
        new, changed = rebuild(store, now)
        record_success(runs, source_id, now, {"fetched": len(fetched), "new_entries": new, "changes": changed})
        store.save_runs(runs)
    return RunResult(source_id, True, len(fetched), new, changed)


def run_due(
    store: CatalogStore, sources: list[dict], fetchers: Mapping[str, Callable[[], list[Observation]]],
    *, now: datetime, force: bool = False,
) -> list[RunResult]:
    """주기가 된 출처만 수집한다. ``force`` 면 전부(관리자 수동 재확인). 구현 안 된 출처는 건너뛴다."""
    out = []
    for s in sources:
        fetch = fetchers.get(s["id"])
        if fetch is None:
            continue
        if force or due(store.load_runs(), s["id"], now, s["cadence_hours"]):
            out.append(run_source(store, s["id"], fetch, now=now))
    return out
