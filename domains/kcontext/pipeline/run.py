"""일정 글 → 앵커(좌표 부착) → 앵커별 실록 언급 → 출력 묶음(``kc-chat-bundle/v1``) 한 파일.

호스트 에이전트 프로세스 전용(D10): backend 는 이 모듈을 import 하지 않는다. LLM 은 주입한다(``complete``).
좌표는 장소 사전(places.py)에 있는 이름만 붙이고, 없으면 null + COORD_UNKNOWN 이다(추측 없음).
언급 기록은 방문(visit) 앵커에만 붙인다 — 숙소는 근사 좌표만 받는다.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from domains.kcontext.index import LocalIndex
from domains.kcontext.places import PlaceBook, load_places
from domains.kcontext.schedule import RETRY_CODES, ScheduleCache, understand_with_meta
from domains.kcontext.story import COVERAGE_NOTE, build_mentions, to_card
from domains.kcontext.story.finder import DEFAULT_LIMIT

__all__ = [
    "BUNDLE_FILE",
    "BUNDLE_SCHEMA",
    "BundleExistsError",
    "run_story_pipeline",
    "write_bundle",
]

BUNDLE_SCHEMA = "kc-chat-bundle/v1"
BUNDLE_FILE = "bundle.json"
MENTION_SCHEMA = "kc-mention/v1"

Complete = Callable[[str, str], str]


class BundleExistsError(FileExistsError):
    """OUT/bundle.json 이 이미 있다."""


def _problem(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _attach_coords(
    anchors: list[dict[str, Any]], book: PlaceBook, problems: list[dict[str, str]]
) -> None:
    for a in anchors:
        name = a.get("name")
        if not isinstance(name, str) or not name.strip():
            problems.append(_problem("ANCHOR_NO_NAME", "이름 없는 앵커 — 좌표·언급을 찾지 않음"))
            continue
        place = book.lookup(name)
        if place is None:
            a["lat"] = a["lng"] = None
            problems.append(_problem("COORD_UNKNOWN", f"{name}: 장소 사전에 없어 좌표를 비워 둠"))
        else:
            a["lat"], a["lng"] = place.lat, place.lng


def _unique_card_ids(cards: list[dict[str, Any]]) -> None:
    """같은 기사가 두 앵커에 걸리면 카드 id 가 겹친다 — 뒤의 것에 _2, _3 … 을 붙인다."""
    seen: dict[str, int] = {}
    for c in cards:
        cid = c["card"]["id"]
        seen[cid] = seen.get(cid, 0) + 1
        if seen[cid] > 1:
            c["card"]["id"] = f"{cid}_{seen[cid]}"


def _unfit(res: dict[str, Any]) -> bool:
    """캐시에 있어선 안 되는 결과(부분·실패) — 적중으로 치지 않는다(심층 방어)."""
    bad = {"QUOTE_NOT_FOUND", *RETRY_CODES}
    return any(isinstance(p, dict) and p.get("code") in bad for p in res.get("problems", []))


def run_story_pipeline(
    text: str,
    *,
    complete: Complete,
    db: str | Path | LocalIndex,
    trip: tuple[str, str] | None,
    limit: int = DEFAULT_LIMIT,
    places: PlaceBook | None = None,
    now: datetime | None = None,
    max_attempts: int = 2,
    budget_s: float | None = None,
    attempt_timeout_s: float | None = None,
    retry_unverified: bool = False,
    retry_partial: bool = True,
    cache: ScheduleCache | None = None,
    cache_key: str | None = None,
) -> dict[str, Any]:
    """묶음(dict)을 돌려준다. 묶음 디스크 쓰기는 없다(캐시 쓰기는 cache 가 있을 때만).

    db 가 LocalIndex 면 닫지 않는다. ``bundle["schedule"]`` 에 이해 결과의 출처를 남긴다(§6.5).
    """
    book = places if places is not None else load_places()
    t_from, t_to = trip if trip else (None, None)
    use_cache = cache is not None and cache_key is not None
    hit = cache.get(cache_key) if use_cache else None  # type: ignore[union-attr,arg-type]
    cache_problems: list[dict[str, str]] = []
    if hit is not None and hit["result"].get("anchors") and not _unfit(hit["result"]):
        sched = hit["result"]
        schedule = {
            "source": "cache",
            "attempts": 0,
            "model": hit["meta"].get("model"),
            "prompt_sha": hit["meta"].get("prompt_sha"),
            "cache_created_at": hit["created_at"],
        }
    else:
        sched, meta = understand_with_meta(
            text, complete=complete, trip_from=t_from, trip_to=t_to, max_attempts=max_attempts,
            budget_s=budget_s, attempt_timeout_s=attempt_timeout_s,
            retry_unverified=retry_unverified, retry_partial=retry_partial,
        )  # fmt: skip
        meta["model"] = getattr(complete, "model", None)
        schedule = {**meta, "cache_created_at": None}
        failed = any(p["code"] in RETRY_CODES for p in sched["problems"])
        partial = any(p["code"] == "QUOTE_NOT_FOUND" for p in sched["problems"])  # 불완전할 수 있는 결과는 고정하지 않는다
        if use_cache and sched["anchors"] and not failed and not partial and meta["attempts"] > 0:
            try:
                cache.put(cache_key, sched, meta)  # type: ignore[union-attr,arg-type]
            except OSError as e:
                cache_problems.append(_problem("CACHE_UNAVAILABLE", f"캐시를 쓸 수 없음 ({type(e).__name__})"))  # fmt: skip
    anchors: list[dict[str, Any]] = [dict(a) for a in sched["anchors"]]
    problems: list[dict[str, str]] = [dict(p) for p in sched["problems"]] + cache_problems
    _attach_coords(anchors, book, problems)

    visits = [a for a in anchors if a.get("type") == "visit" and a.get("name")]
    if isinstance(db, LocalIndex):
        mention_out = build_mentions(db, visits, limit=limit)
    else:
        with LocalIndex(db) as idx:
            mention_out = build_mentions(idx, visits, limit=limit)
    for p in mention_out["problems"]:
        who = p.get("anchor") or "-"
        problems.append(_problem(f"MENTION_{str(p.get('kind', 'unknown')).upper()}", f"{who}: {p.get('article_id', '')}".rstrip(": ")))  # fmt: skip

    cards = [
        to_card(r["anchor"], m)
        for r in mention_out["anchors"]
        if r["anchor"]
        for m in r["mentions"]
    ]
    _unique_card_ids(cards)
    stamp = (now or datetime.now(UTC)).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema": BUNDLE_SCHEMA,
        "schedule": schedule,
        "generated_at": stamp,
        "trip": {"from": t_from, "to": t_to} if trip else None,
        "itinerary": {"anchors": anchors, "free_slots": sched["free_slots"]},
        "mentions": {**mention_out, "schema": MENTION_SCHEMA},
        "cards": cards,
        "problems": problems,
        "coverage_note": COVERAGE_NOTE,
    }


def summarize(bundle: dict[str, Any]) -> dict[str, Any]:
    n_anchor = len(bundle["itinerary"]["anchors"])
    n_ment = sum(len(r["mentions"]) for r in bundle["mentions"]["anchors"])
    return {
        "anchors": n_anchor,
        "mentions": n_ment,
        "problems": len(bundle["problems"]),
        "status": "ok" if n_anchor else "no_anchors",
    }


def write_bundle(bundle: dict[str, Any], out_dir: Path, *, force: bool = False) -> Path:
    """OUT/bundle.json 을 새 파일로 쓴다. 이미 있으면 BundleExistsError(force 면 교체). OUT 밖에는 쓰지 않는다."""
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / BUNDLE_FILE
    if not force and os.path.lexists(dest):
        raise BundleExistsError(f"{BUNDLE_FILE} 이 이미 있다 (--force 로 교체)")
    tmp = out_dir / f".{BUNDLE_FILE}.{uuid.uuid4().hex[:8]}.tmp"
    try:
        tmp.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if force:
            os.replace(tmp, dest)
        else:
            os.link(tmp, dest)  # 이미 있으면 FileExistsError — 경쟁 상태에서도 덮어쓰지 않는다
    except FileExistsError as e:
        raise BundleExistsError(f"{BUNDLE_FILE} 이 이미 있다 (--force 로 교체)") from e
    finally:
        tmp.unlink(missing_ok=True)
    return dest
