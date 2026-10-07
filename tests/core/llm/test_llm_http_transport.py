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
