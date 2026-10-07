import asyncio
import json

import httpx
import pytest

from core.llm import HttpxTransport, parse_config

KEY = "nvapi-" + "k" * 24  # 런타임 조립


def _provider(base="https://api.example/v1", timeout=5.0):
    cfg = parse_config(
        {
            "providers": {"p": {"api_key_envs": ["K"], "base_url": base, "max_concurrency": 1,
                                "timeout_s": timeout}},
            "features": {"f": {"provider": "p", "model": "m"}},
        }
    )
    return cfg.providers["p"]


def _send(handler, base="https://api.example/v1", key=KEY):
    t = HttpxTransport(transport=httpx.MockTransport(handler))
    return asyncio.run(
        t.send(provider=_provider(base), model="m1", base_url=base, api_key=key,
               messages=[{"role": "user", "content": "q"}])
    )


def _ok(content, **extra):
    msg = {"role": "assistant", "content": content, **extra}
    return httpx.Response(200, json={"choices": [{"message": msg}, {"message": {"content": "X"}}]})


def test_request_shape_and_first_choice_content():
    seen = {}

    def handler(req):
        seen["url"] = str(req.url)
        seen["auth"] = req.headers.get("authorization")
        seen["body"] = json.loads(req.content)
        return _ok("  안녕  ")

    r = _send(handler)
    assert (r.status, r.text) == (200, "안녕")
    assert seen["url"] == "https://api.example/v1/chat/completions"
    assert seen["auth"] == f"Bearer {KEY}"
    assert seen["body"]["model"] == "m1" and seen["body"]["messages"] == [
        {"role": "user", "content": "q"}
    ]


def test_reasoning_only_response_is_not_used_as_answer():
    r = _send(lambda req: _ok(None, reasoning_content="사고 과정 노출 금지"))
    assert r.status == 200 and r.text == ""
    r = _send(lambda req: _ok("", reasoning_content="사고 과정"))
    assert r.text == ""


def test_reasoning_model_with_content_returns_content_only():
    r = _send(lambda req: _ok("답", reasoning_content="사고"))
    assert r.text == "답"


@pytest.mark.parametrize("status", [401, 429, 500, 503])
def test_error_status_passes_through_without_body(status):
    r = _send(lambda req: httpx.Response(status, text="BODY-" + KEY))
    assert r.status == status and r.text == "" and KEY not in repr(r)


@pytest.mark.parametrize("payload", [[], {}, {"choices": []}, {"choices": [1]},
                                      {"choices": [{"message": "x"}]}])
def test_malformed_payload_raises_value_error(payload):
    with pytest.raises(ValueError) as ei:
        _send(lambda req: httpx.Response(200, json=payload))
    assert KEY not in str(ei.value)


def test_non_json_body_raises_without_leaking():
    with pytest.raises(ValueError) as ei:
        _send(lambda req: httpx.Response(200, text="not json " + KEY))
    assert KEY not in str(ei.value)


def test_timeout_propagates_as_httpx_error():
    def handler(req):
        raise httpx.ReadTimeout("timeout")

    with pytest.raises(httpx.TimeoutException):
        _send(handler)


def test_plain_http_rejected_except_loopback_and_inference_local():
    def handler(req):
        return _ok("a")

    with pytest.raises(ValueError) as ei:
        _send(handler, base="http://evil.example/v1")
    assert KEY not in str(ei.value)
    assert _send(handler, base="http://localhost:8000/v1").text == "a"
    assert _send(handler, base="https://inference.local/v1").text == "a"


def test_no_key_means_no_authorization_header():
    seen = {}

    def handler(req):
        seen["auth"] = req.headers.get("authorization")
        return _ok("a")

    _send(handler, base="http://127.0.0.1:1/v1", key=None)
    assert seen["auth"] is None


def test_http_inference_local_allowed_and_localhost_lookalike_rejected():
    def handler(req):
        return _ok("a")

    assert _send(handler, base="http://inference.local/v1").text == "a"
    with pytest.raises(ValueError):
        _send(handler, base="http://localhost.evil.example/v1")
    with pytest.raises(ValueError):
        _send(handler, base="http://inference.local.evil.example/v1")


def test_redirect_is_not_followed():
    hits = []

    def handler(req):
        if req.url.host == "evil.example":
            hits.append(str(req.url))
            return _ok("leaked")
        return httpx.Response(302, headers={"Location": "https://evil.example/steal"})

    resp = _send(handler)
    assert resp.status == 302 and resp.text == "" and hits == []


def test_total_time_is_capped_even_if_each_read_is_fast():
    async def handler(req):
        await asyncio.sleep(1)
        return _ok("late")

    t = HttpxTransport(transport=httpx.MockTransport(handler))

    async def run():
        return await t.send(provider=_provider(timeout=0.05), model="m", base_url="https://a.example/v1",
                            api_key=KEY, messages=[{"role": "user", "content": "q"}])

    with pytest.raises(TimeoutError):
        asyncio.run(run())


def test_empty_reply_logs_finish_reason_only(caplog):
    body = {"choices": [{"finish_reason": "length",
                         "message": {"content": None, "reasoning_content": "SECRET-THOUGHT"}}]}
    with caplog.at_level("WARNING", logger="core.llm.http_transport"):
        assert _send(lambda r: httpx.Response(200, json=body)).text == ""
    log = caplog.text
    assert "finish_reason=length" in log
    assert KEY not in log and "SECRET-THOUGHT" not in log


def test_finish_reason_is_sanitized_in_log(caplog):
    body = {"choices": [{"finish_reason": "x\n" + KEY, "message": {"content": ""}}]}
    with caplog.at_level("WARNING", logger="core.llm.http_transport"):
        _send(lambda r: httpx.Response(200, json=body))
    assert KEY not in caplog.text and "finish_reason=?" in caplog.text
