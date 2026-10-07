"""Tavily 검색으로 구청 행사 후보(URL·본문)를 모은다 (D12). 호스트 수집기 전용.

- 키는 env ``TAVILY_SEARCH_KEY`` 에서만 읽는다. 로그·예외에는 키 값이 남지 않는다.
- 요청 ``include_domains`` 는 도메인만 받는다(공식 문서). 경로 제한·차단 경로는 응답 URL 을
  이 모듈이 다시 거른다(``url_allowed``). 서버가 어겨도 코드가 거른다.
- 이 모듈은 구청 페이지를 직접 가져오지 않는다. Tavily 가 돌려준 본문만 쓴다.
"""

from __future__ import annotations

import json
import os
import posixpath
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

import httpx

from core.audit.redact import redact_text
from domains.kcontext.paths import data_dir

__all__ = [
    "KEY_ENV",
    "Candidate",
    "KeyMissing",
    "SearchOutcome",
    "SourceUnconfirmed",
    "WebSearchError",
    "build_queries",
    "load_web_source",
    "month_label",
    "search_candidates",
    "url_allowed",
]

KEY_ENV = "TAVILY_SEARCH_KEY"
ENDPOINT = "https://api.tavily.com/search"
MAX_CONTENT_CHARS = 20_000
_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
_KEYS = {
    "region", "gu", "domains", "allow_url_prefixes", "disallow_path_prefixes",
    "drop_urls_with_query", "queries", "status", "note",
}
_REQUIRED = {"region", "gu", "domains", "queries", "status"}
_PLACEHOLDER = "[확인 필요]"


class WebSearchError(RuntimeError):
    pass


class KeyMissing(WebSearchError):
    pass


class SourceUnconfirmed(WebSearchError):
    pass


@dataclass(frozen=True)
class Candidate:
    url: str
    title: str
    content: str
    score: float


@dataclass(frozen=True)
class SearchOutcome:
    candidates: tuple[Candidate, ...]
    problems: tuple[str, ...]
    calls: int
    dropped_urls: int


def _str_list(v: object, what: str, fname: str, *, allow_empty: bool) -> list[str]:
    if not isinstance(v, list) or not all(isinstance(x, str) and x.strip() for x in v):
        raise ValueError(f"{fname}: {what} 는 비어 있지 않은 문자열 목록이어야 한다")
    if not v and not allow_empty:
        raise ValueError(f"{fname}: {what} 가 비었다")
    return v


def load_web_source(source_id: str, directory: Path | None = None) -> dict:
    """data/web_sources/<source_id>.json. 모르는 키·빠진 키는 거부한다."""
    if not _ID_RE.match(source_id):
        raise ValueError(f"source id 형식 오류: {source_id!r}")
    base = Path(directory) if directory is not None else data_dir() / "web_sources"
    path = base / f"{source_id}.json"
    fname = path.name
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except (OSError, ValueError) as e:
        raise ValueError(f"{fname}: 읽을 수 없다 ({type(e).__name__})") from e
    if not isinstance(raw, dict):
        raise ValueError(f"{fname}: 최상위가 객체가 아니다")  # noqa: TRY004
    if set(raw) - _KEYS:
        raise ValueError(f"{fname}: 모르는 키 {sorted(set(raw) - _KEYS)}")
    if _REQUIRED - set(raw):
        raise ValueError(f"{fname}: 빠진 키 {sorted(_REQUIRED - set(raw))}")
    for k in ("region", "gu"):
        if not isinstance(raw[k], str) or not raw[k].strip():
            raise ValueError(f"{fname}: {k} 는 문자열이어야 한다")
    if raw["status"] not in ("confirmed", "unconfirmed"):
        raise ValueError(f"{fname}: status 는 confirmed|unconfirmed")
    _str_list(raw["domains"], "domains", fname, allow_empty=False)
    _str_list(raw["queries"], "queries", fname, allow_empty=False)
    _str_list(raw.get("allow_url_prefixes", []), "allow_url_prefixes", fname, allow_empty=True)
    _str_list(raw.get("disallow_path_prefixes", []), "disallow_path_prefixes", fname,
              allow_empty=True)
    if not isinstance(raw.get("drop_urls_with_query", False), bool):
        raise ValueError(f"{fname}: drop_urls_with_query 는 boolean")  # noqa: TRY004
    return raw


def month_label(month: str) -> str:
    """``2026-10`` → ``2026년 10월``."""
    m = _MONTH_RE.match(month)
    if not m:
        raise ValueError(f"month 는 YYYY-MM 형식이어야 한다: {month!r}")
    return f"{m.group(1)}년 {int(m.group(2))}월"


def build_queries(src: Mapping, month: str) -> list[str]:
    label = month_label(month)
    return [q.replace("{gu}", src["gu"]).replace("{month}", label) for q in src["queries"]]


def _host_ok(host: str, domains: list[str]) -> bool:
    host = host.lower()
    for d in domains:
        d = d.lower()
        if host == d or host.endswith("." + d):
            return True
    return False


def _clean_path(path: str) -> str:
    """퍼센트 디코딩(두 번)·``//``·``/./``·``..`` 를 정리하고 소문자로 맞춘다."""
    p = unquote(unquote(path)).replace("\\", "/")
    norm = posixpath.normpath(p) if p else "/"
    if p.endswith("/") and not norm.endswith("/"):
        norm += "/"
    return ("/" + norm.lstrip("/")).casefold()


def _blocked(prefix: str, path: str, query: str) -> bool:
    """차단 항목 ``/경로`` 또는 ``/경로?키=값&…`` 가 이 URL 을 막는지.

    경로는 정리한 뒤 접두로 비교한다. 항목에 쿼리가 있으면 그 키=값이 모두 URL 쿼리에 있어야
    막는다(순서가 달라도 막고, ``cmsid=142320`` 같은 다른 값은 막지 않는다).
    """
    pre_path, _, pre_query = prefix.partition("?")
    if not path.startswith(_clean_path(pre_path)):
        return False
    if not pre_query:
        return True
    have = {(k.casefold(), v) for k, v in parse_qsl(query, keep_blank_values=True)}
    return all((k.casefold(), v) in have for k, v in parse_qsl(pre_query, keep_blank_values=True))


def url_allowed(url: str, src: Mapping) -> bool:
    """호스트가 domains 안 · allow_url_prefixes 접두 · disallow·쿼리 규칙에 걸리지 않는지."""
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return False
    if not _host_ok(parts.hostname.rstrip("."), src["domains"]):
        return False
    prefixes = src.get("allow_url_prefixes") or []
    if prefixes and not any(url.startswith(p) for p in prefixes):
        return False
    if src.get("drop_urls_with_query") and parts.query:
        return False
    path = _clean_path(parts.path)
    return not any(_blocked(d, path, parts.query) for d in src.get("disallow_path_prefixes") or [])


def _mask(text: str, key: str | None) -> str:
    if key:
        text = text.replace(key, "***")
    return redact_text(text)


def search_candidates(
    src: Mapping,
    *,
    month: str,
    client: httpx.Client | None = None,
    env: Mapping[str, str] | None = None,
    max_calls: int = 30,
    time_range: str | None = None,
) -> SearchOutcome:
    if src.get("status") != "confirmed" or any(_PLACEHOLDER in d for d in src["domains"]):
        raise SourceUnconfirmed(f"{src.get('gu')}: web_sources 가 confirmed 가 아니다")
    key = (os.environ if env is None else env).get(KEY_ENV, "")
    if not key:
        raise KeyMissing(f"{KEY_ENV} 가 설정되지 않았다")
    queries = build_queries(src, month)
    problems: list[str] = []
    if len(queries) > max_calls:
        problems.append(f"max_calls={max_calls} 초과 — 질의 {len(queries) - max_calls}건 건너뜀")
        queries = queries[: max(max_calls, 0)]
    own = client is None
    http = client or httpx.Client(timeout=10.0)
    best: dict[str, Candidate] = {}
    dropped_set: set[str] = set()
    calls = 0
    try:
        for q in queries:
            body: dict = {
                "query": q,
                "include_domains": src["domains"],
                "search_depth": "basic",
                "max_results": 10,
                "include_raw_content": "text",
            }
            if time_range:
                body["time_range"] = time_range
            calls += 1
            try:
                resp = http.post(ENDPOINT, json=body, headers={"Authorization": f"Bearer {key}"})
                resp.raise_for_status()
                data = resp.json()
            except httpx.HTTPStatusError as e:
                raise WebSearchError(
                    _mask(f"Tavily HTTP {e.response.status_code}", key)
                ) from None
            except (httpx.HTTPError, ValueError) as e:
                raise WebSearchError(_mask(f"Tavily 호출 실패 ({type(e).__name__})", key)) from None
            results = data.get("results") if isinstance(data, dict) else None
            if not isinstance(results, list):
                problems.append(f"질의 {q!r}: results 가 목록이 아님")
                continue
            for r in results:
                if not isinstance(r, dict) or not isinstance(r.get("url"), str):
                    problems.append(f"질의 {q!r}: 결과 항목 형식 오류")
                    continue
                if not url_allowed(r["url"], src):
                    dropped_set.add(r["url"])
                    continue
                text = r.get("raw_content") or r.get("content") or ""
                score = r.get("score")
                cand = Candidate(
                    url=r["url"],
                    title=str(r.get("title") or ""),
                    content=str(text)[:MAX_CONTENT_CHARS],
                    score=float(score) if isinstance(score, (int, float)) else 0.0,
                )
                if cand.url not in best or cand.score > best[cand.url].score:
                    best[cand.url] = cand
    finally:
        if own:
            http.close()
    ordered = tuple(sorted(best.values(), key=lambda c: (-c.score, c.url)))
    return SearchOutcome(ordered, tuple(problems), calls, len(dropped_set))
