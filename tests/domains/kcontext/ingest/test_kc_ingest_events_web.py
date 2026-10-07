import json
from pathlib import Path

import httpx
import pytest

from domains.kcontext.ingest.events.web import (
    KEY_ENV,
    KeyMissing,
    SourceUnconfirmed,
    WebSearchError,
    build_queries,
    load_web_source,
    month_label,
    search_candidates,
    url_allowed,
)
from domains.kcontext.regions import load_regions

KEY = "tvly-" + "a" * 24  # 실행 시 조립 — 키 모양 리터럴을 소스에 두지 않는다


def src(**over) -> dict:
    base = {
        "region": "r", "gu": "○○구", "domains": ["www.example-gu.invalid"],
        "queries": ["{gu} 축제 행사 {month}", "{gu} 문화행사 {month}"], "status": "confirmed",
    }
    base.update(over)
    return base


def test_real_sources_load_and_match_regions():
    regions = load_regions()
    for sid in ("junggu", "mapo", "gangnam"):
        s = load_web_source(sid)
        assert s["status"] == "confirmed"
        assert s["region"] in regions
        assert s["gu"] in regions[s["region"]].gu
        assert s["domains"] and all("[확인 필요]" not in d for d in s["domains"])


def test_naver_blog_is_excluded_from_junggu():
    s = load_web_source("junggu")
    assert not any("naver" in d for d in s["domains"])
    assert not any("naver" in p for p in s.get("allow_url_prefixes", []))


def test_load_rejects_unknown_and_missing_keys(tmp_path: Path):
    (tmp_path / "aa.json").write_text(json.dumps({**src(), "extra": 1}), encoding="utf-8")
    with pytest.raises(ValueError, match="모르는 키"):
        load_web_source("aa", tmp_path)
    (tmp_path / "bb.json").write_text(json.dumps({"region": "r"}), encoding="utf-8")
    with pytest.raises(ValueError, match="빠진 키"):
        load_web_source("bb", tmp_path)
    with pytest.raises(FileNotFoundError):
        load_web_source("nope", tmp_path)
    with pytest.raises(ValueError, match="형식"):
        load_web_source("../etc", tmp_path)


def test_month_label_and_queries():
    assert month_label("2026-10") == "2026년 10월"
    with pytest.raises(ValueError):
        month_label("2026-13")
    assert build_queries(src(), "2026-10") == ["○○구 축제 행사 2026년 10월",
                                               "○○구 문화행사 2026년 10월"]


def test_url_allowed_rules():
    s = src(domains=["a.invalid"], allow_url_prefixes=["https://www.a.invalid/ok"],
            disallow_path_prefixes=["/ok/secret", "/ok/x.do?id=9"], drop_urls_with_query=False)
    assert url_allowed("https://www.a.invalid/ok/page", s)  # 서브도메인
    assert not url_allowed("https://www.a.invalid/other", s)  # 접두 밖
    assert not url_allowed("https://b.invalid/ok/page", s)  # 호스트 밖
    assert not url_allowed("https://evil-a.invalid/ok/page", s)  # 접미만 같은 호스트
    assert not url_allowed("https://www.a.invalid/ok/secret/1", s)
    assert not url_allowed("https://www.a.invalid/ok/x.do?id=9", s)
    assert url_allowed("https://www.a.invalid/ok/x.do?id=8", s)
    assert not url_allowed("ftp://www.a.invalid/ok", s)
    assert not url_allowed("javascript:alert(1)", s)


def test_drop_urls_with_query():
    s = src(domains=["a.invalid"], drop_urls_with_query=True)
    assert url_allowed("https://a.invalid/p", s)
    assert not url_allowed("https://a.invalid/p?x=1", s)


def tavily(results_by_query: dict[str, list[dict]], seen: list) -> httpx.Client:
    def handler(req: httpx.Request) -> httpx.Response:
        body = json.loads(req.content)
        seen.append((body, req.headers.get("authorization")))
        return httpx.Response(200, json={"results": results_by_query.get(body["query"], [])})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_search_filters_dedups_and_sends_expected_request():
    seen: list = []
    ok = "https://www.example-gu.invalid/b/1"
    results = {
        "○○구 축제 행사 2026년 10월": [
            {"url": ok, "title": "t", "content": "짧음", "score": 0.4},
            {"url": "https://other.invalid/x", "title": "밖", "content": "c", "score": 0.99},
        ],
        "○○구 문화행사 2026년 10월": [
            {"url": ok, "title": "t", "content": "짧음", "raw_content": "원문 본문", "score": 0.8},
        ],
    }
    out = search_candidates(src(), month="2026-10", client=tavily(results, seen),
                            env={KEY_ENV: KEY})
    assert out.calls == 2 and out.dropped_urls == 1
    assert [c.url for c in out.candidates] == [ok]
    assert out.candidates[0].score == 0.8 and out.candidates[0].content == "원문 본문"
    body, auth = seen[0]
    assert auth == f"Bearer {KEY}"
    assert body["include_domains"] == ["www.example-gu.invalid"]
    assert body["search_depth"] == "basic" and "time_range" not in body


def test_search_time_range_is_optional_param():
    seen: list = []
    search_candidates(src(), month="2026-10", client=tavily({}, seen), env={KEY_ENV: KEY},
                      time_range="month")
    assert all(b["time_range"] == "month" for b, _ in seen)


def test_search_requires_key_and_confirmed():
    with pytest.raises(KeyMissing, match=KEY_ENV):
        search_candidates(src(), month="2026-10", env={})
    with pytest.raises(SourceUnconfirmed):
        search_candidates(src(status="unconfirmed"), month="2026-10", env={KEY_ENV: KEY})
    with pytest.raises(SourceUnconfirmed):
        search_candidates(src(domains=["[확인 필요]"]), month="2026-10", env={KEY_ENV: KEY})


def test_search_http_error_never_leaks_key():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text=f"bad key {KEY}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(WebSearchError) as ei:
        search_candidates(src(), month="2026-10", client=client, env={KEY_ENV: KEY})
    assert KEY not in str(ei.value) and "401" in str(ei.value)


def test_search_transport_error_never_leaks_key():
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"cannot connect with {KEY}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(WebSearchError) as ei:
        search_candidates(src(), month="2026-10", client=client, env={KEY_ENV: KEY})
    assert KEY not in str(ei.value) and "ConnectError" in str(ei.value)


def test_search_max_calls_limits_requests():
    seen: list = []
    out = search_candidates(src(), month="2026-10", client=tavily({}, seen),
                            env={KEY_ENV: KEY}, max_calls=1)
    assert out.calls == 1 and len(seen) == 1
    assert any("max_calls" in p for p in out.problems)
    seen.clear()
    out = search_candidates(src(), month="2026-10", client=tavily({}, seen),
                            env={KEY_ENV: KEY}, max_calls=0)
    assert out.calls == 0 and not seen


def test_search_bad_results_shape_is_a_problem_not_a_crash():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": "oops"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    out = search_candidates(src(queries=["{gu} {month}"]), month="2026-10", client=client,
                            env={KEY_ENV: KEY})
    assert out.candidates == () and out.problems


def test_url_allowed_resists_path_tricks():
    s = src(domains=["a.invalid"],
            disallow_path_prefixes=["/CmsWeb/", "/content.do?cmsid=14232", "/search"])
    ok = "https://a.invalid/board/1"
    assert url_allowed(ok, s)
    for bad in (
        "https://a.invalid/cmsweb/x",            # 대소문자
        "https://a.invalid/%43msWeb/x",          # 퍼센트 인코딩
        "https://a.invalid/%2543msWeb/x",        # 이중 인코딩
        "https://a.invalid//CmsWeb/x",           # 겹슬래시
        "https://a.invalid/board/../CmsWeb/x",   # ..
        "https://a.invalid/./search",            # ./
        "https://a.invalid/content.do?cmsid=14232",
        "https://a.invalid/content.do?x=1&cmsid=14232",   # 쿼리 순서
        "https://a.invalid/content.do?cmsid=14232&mode=view",
    ):
        assert not url_allowed(bad, s), bad
    assert url_allowed("https://a.invalid/content.do?cmsid=142320", s)  # 다른 값은 막지 않는다
    assert url_allowed("https://a.invalid/content.do?cmsid=14231", s)


def test_url_allowed_resists_host_tricks():
    s = src(domains=["a.invalid"])
    for bad in (
        "https://a.invalid.evil.com/",
        "https://evil.com/?u=a.invalid",
        "https://user@evil.com/",
        "https://a.invalid@evil.com/",
        "https://evila.invalid/",
        "https://a.invalid\\@evil.com/",
    ):
        assert not url_allowed(bad, s), bad
    assert url_allowed("https://A.INVALID/x", s)
    assert url_allowed("https://a.invalid./x", s)  # 끝의 점
    assert url_allowed("https://a.invalid:8443/x", s)
