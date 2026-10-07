"""구청 행사 검색 수집 실행기 (D12, T226).

    python -m domains.kcontext.ingest.events.web_run --source junggu --month 2026-10 \\
        --out var/data/events/web.jsonl --collected-at YYYY-MM-DD [--fixture PATH] [--max-calls N]
    python -m domains.kcontext.ingest.events.web_run --source gangnam --month 2026-10 --candidates-only

``python -m domains.kcontext.ingest.events --provider web ...`` 로도 부를 수 있다(T210 ``__main__``).
종료 코드: 0 정상 · 2 실행 조건 미충족(키·확인 상태·screen·추출기 없음) — 메시지에 대안을 적는다.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import httpx
from dotenv import dotenv_values

from domains.kcontext.index.store import LocalIndex
from domains.kcontext.paths import repo_root
from domains.kcontext.regions import load_regions

from .extract import Extractor, ScreenFn, extract_events
from .store import to_chunks, write_jsonl
from .web import (
    KEY_ENV,
    Candidate,
    KeyMissing,
    SourceUnconfirmed,
    WebSearchError,
    load_web_source,
    month_label,
    search_candidates,
)

__all__ = ["main", "run"]


def _fail(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 2


def _env_with_dotenv(env: Mapping[str, str] | None) -> Mapping[str, str]:
    """셸 env 우선, 없으면 레포 .env 의 TAVILY 키만 보충한다(os.environ 은 바꾸지 않는다)."""
    if env is not None:
        return env
    merged = dict(os.environ)
    if not merged.get(KEY_ENV):
        val = dotenv_values(repo_root() / ".env").get(KEY_ENV)
        if val:
            merged[KEY_ENV] = val
    return merged


def _default_screen() -> ScreenFn | None:
    try:
        from domains.kcontext.judge.inject import screen  # type: ignore[import-not-found]
    except ImportError:
        return None
    return screen


def _load_fixture(path: Path) -> tuple[list[Candidate], dict[str, list[dict]], bool]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cands: list[Candidate] = []
    table: dict[str, list[dict]] = {}
    for c in raw.get("candidates", []):
        cands.append(Candidate(c["url"], c.get("title", ""), c["content"], float(c.get("score", 0))))
        table[c["url"]] = c.get("extracted", [])
    return cands, table, raw.get("synthetic") is True


def run(
    argv: Sequence[str],
    *,
    screen: ScreenFn | None = None,
    extractor_for: Callable[[Candidate], Extractor] | None = None,
    client: httpx.Client | None = None,
    env: Mapping[str, str] | None = None,
    sources_dir: Path | None = None,
    regions_dir: Path | None = None,
) -> int:
    ap = argparse.ArgumentParser(prog="web_run")
    ap.add_argument("--source", required=True, help="data/web_sources/<id>.json 의 id")
    ap.add_argument("--month", required=True, help="YYYY-MM")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--db", type=Path)
    ap.add_argument("--collected-at")
    ap.add_argument("--fixture", type=Path)
    ap.add_argument("--max-calls", type=int, default=30)
    ap.add_argument("--time-range", choices=["day", "week", "month", "year"])
    ap.add_argument("--candidates-only", action="store_true")
    a = ap.parse_args(list(argv))
    try:
        month_label(a.month)
    except ValueError as e:
        return _fail(str(e))

    try:
        src = load_web_source(a.source, sources_dir)
    except FileNotFoundError:
        return _fail(f"web_sources/{a.source}.json 이 없다")
    except ValueError as e:
        return _fail(str(e))
    regions = load_regions(regions_dir)
    region = regions.get(src["region"])
    if region is None:
        return _fail(f"지역 {src['region']!r} 이 regions/ 에 없다")

    problems: list[str] = []
    calls = dropped_urls = 0
    table: dict[str, list[dict]] = {}
    synthetic = False
    if a.fixture:
        cands, table, synthetic = _load_fixture(a.fixture)
        if synthetic and a.db:
            return _fail("합성 fixture 는 색인에 넣지 않는다 — --db 를 빼고 실행한다")
    else:
        try:
            out = search_candidates(
                src, month=a.month, client=client, env=_env_with_dotenv(env),
                max_calls=a.max_calls, time_range=a.time_range,
            )
        except (KeyMissing, SourceUnconfirmed) as e:
            return _fail(f"{e} — --fixture 로 실행할 수 있다")
        except WebSearchError as e:
            return _fail(str(e))
        cands, problems, calls, dropped_urls = (
            list(out.candidates), list(out.problems), out.calls, out.dropped_urls,
        )

    if a.candidates_only:
        for c in cands:
            print(json.dumps({"url": c.url, "title": c.title, "score": c.score,
                              "chars": len(c.content)}, ensure_ascii=False))
        print(json.dumps({"candidates": len(cands), "calls": calls,
                          "dropped_urls": dropped_urls, "problems": len(problems)}))
        return 0

    if not a.collected_at:
        return _fail("--collected-at YYYY-MM-DD 가 필요하다")
    scr = screen or _default_screen()
    if scr is None:
        return _fail("주입 차단(domains.kcontext.judge.inject.screen, T211b)이 아직 없다 — "
                     "--candidates-only 로 후보만 볼 수 있다")
    if extractor_for is None and a.fixture:
        def extractor_for(c: Candidate) -> Extractor:
            items = table.get(c.url, [])  # fixture 의 합성 추출 결과
            return lambda _content: items
    if extractor_for is None:
        return _fail("LLM 추출기(core.llm transport, T223)가 아직 없다 — "
                     "--fixture 또는 --candidates-only 로 실행할 수 있다")

    records = []
    dropped = 0
    for c in cands:
        res = extract_events(c, extractor=extractor_for(c), screen=scr, region=region,
                             source_name=f"{src['gu']}청", collected_at=a.collected_at,
                             year=int(a.month[:4]), synthetic=synthetic)
        records.extend(res.records)
        problems.extend(res.problems)
        dropped += res.dropped
    for p in problems:
        print(f"problem: {p}", file=sys.stderr)
    if a.out:
        write_jsonl(records, a.out)
    if a.db:
        a.db.parent.mkdir(parents=True, exist_ok=True)
        with LocalIndex(a.db) as idx:
            idx.add([c for r in records for c in to_chunks(r)])
    print(json.dumps({"candidates": len(cands), "records": len(records), "dropped": dropped,
                      "dropped_urls": dropped_urls, "problems": len(problems), "calls": calls}))
    return 0


def main() -> None:
    raise SystemExit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
