"""행사 출처 레지스트리와 수집기 연결. 출처마다 실제 제공 방식(api·search·html·manual)을 확인한 값만 적는다."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path

import httpx

from domains.kcontext.ingest.events.web import load_web_source
from domains.kcontext.paths import data_dir
from domains.kcontext.regions import Region

from .model import Observation
from .seoul import KEY_ENV as SEOUL_KEY_ENV
from .seoul import fetch_rows, observations_from_rows
from .web_events import default_events_file, make_web_fetcher

__all__ = ["METHODS", "STATUSES", "SourceError", "load_sources", "make_fetcher"]

METHODS = ("api", "search", "html", "manual")
STATUSES = ("implemented", "partial", "configurable_unverified", "candidate_not_implemented", "manual_only")
_KEYS = {"id", "name", "url", "method", "status", "cadence_hours", "env_keys", "verified_at", "license",
         "links", "notes", "web_source"}
_REQUIRED = {"id", "name", "url", "method", "status", "cadence_hours", "env_keys", "verified_at", "notes"}


class SourceError(RuntimeError):
    pass


def load_sources(path: Path | None = None) -> list[dict]:
    p = Path(path) if path is not None else data_dir() / "catalog_sources.json"
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{p.name}: 최상위가 배열이 아니다")  # noqa: TRY004
    seen: set[str] = set()
    for i, s in enumerate(raw):
        at = f"{p.name}[{i}]"
        if not isinstance(s, dict) or set(s) - _KEYS or _REQUIRED - set(s):
            raise ValueError(f"{at}: 키가 맞지 않는다")
        if s["method"] not in METHODS or s["status"] not in STATUSES:
            raise ValueError(f"{at}: method·status 값 오류")
        if s["id"] in seen:
            raise ValueError(f"{at}: id 중복 {s['id']}")
        seen.add(s["id"])
        if not isinstance(s["cadence_hours"], (int, float)) or s["cadence_hours"] <= 0:
            raise ValueError(f"{at}: cadence_hours")
        if not (isinstance(s["env_keys"], list) and all(isinstance(k, str) for k in s["env_keys"])):
            raise ValueError(f"{at}: env_keys")
        if "web_source" in s and not (isinstance(s["web_source"], str) and s["web_source"].strip()):
            raise ValueError(f"{at}: web_source")
    return raw


def make_fetcher(
    source_id: str, *, region: Region, now: datetime, env: Mapping[str, str] | None = None,
    client: httpx.Client | None = None, sample: bool = False, web_events: Path | None = None,
    sources: list[dict] | None = None,
) -> Callable[[], list[Observation]]:
    """자동 수집이 구현된 출처의 수집 함수. 구현되지 않은 출처는 SourceError."""
    e = os.environ if env is None else env
    collected = now.strftime("%Y-%m-%d")
    if source_id == "seoul_openapi":
        key = "sample" if sample else e.get(SEOUL_KEY_ENV, "")

        def fetch_seoul() -> list[Observation]:
            rows, _ = fetch_rows(key, client=client, page_size=5 if sample else 1000,
                                 max_pages=1 if sample else 30)
            return observations_from_rows(rows, region=region, collected_at=collected)

        return fetch_seoul
    entry = next((x for x in (sources if sources is not None else load_sources())
                  if x["id"] == source_id), None)
    if entry is not None and entry.get("web_source"):
        # D12: 호스트 수집기(web_run)가 쓴 JSONL 을 읽는다 — 검색·LLM 호출은 여기서 하지 않는다
        wid = entry["web_source"]
        try:
            ws = load_web_source(wid)
        except (OSError, ValueError) as err:  # 파일 없음·형식 오류
            raise SourceError(f"{source_id}: web_sources/{wid}.json 을 쓸 수 없다 ({type(err).__name__})") from err
        if ws["status"] != "confirmed":
            raise SourceError(f"{source_id}: web_sources/{wid}.json 이 confirmed 가 아니다 (D12 ①)")
        path = web_events if web_events is not None else default_events_file(wid)
        if not path.is_file():
            raise SourceError(f"{source_id}: 검색 수집 결과 파일이 없다 ({path.name}) — "
                              f"web_run --source {wid} --out var/data/events/web.{wid}.jsonl 으로 먼저 만든다")
        return make_web_fetcher(path, region=region, source_id=source_id, only_region=ws["region"])
    raise SourceError(f"{source_id}: 자동 수집이 구현돼 있지 않다 (docs: catalog_sources.json 의 status)")
