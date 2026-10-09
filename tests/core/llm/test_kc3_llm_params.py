import asyncio
import json
from pathlib import Path

import httpx
import pytest

from core.audit import AuditLog, MemorySink
from core.llm import (
    HttpxTransport,
    LlmClient,
    LlmConfigError,
    TransportResponse,
    load_config,
    parse_config,
)

ROOT = Path(__file__).resolve().parents[3]
KEY = "nvapi-" + "k" * 24  # 런타임 조립


def _data(params=None, **fextra):
    f = {"provider": "p", "model": "m", **fextra}
    if params is not None:
        f["params"] = params
    return {
        "providers": {"p": {"api_key_envs": ["K"], "base_url": "https://a.example/v1",
                            "max_concurrency": 1}},
        "features": {"f": f},
    }


def _params(params):
    return parse_config(_data(params)).features["f"].params


def test_params_default_empty_and_readonly():
    assert dict(parse_config(_data()).features["f"].params) == {}
    assert dict(_params({})) == {}
    p = _params({"temperature": 0})
    with pytest.raises(TypeError):
        p["x"] = 1  # type: ignore[index]


def test_valid_values():
    p = _params({"temperature": 0, "top_p": 1, "seed": 7, "max_tokens": 4096,
                 "response_format": {"type": "json_object"}, "reasoning_effort": "low"})
    assert p["seed"] == 7 and p["response_format"] == {"type": "json_object"}


@pytest.mark.parametrize("bad", [
    {"temperature": 1.5}, {"temperature": -0.1}, {"temperature": True},
    {"top_p": 0}, {"top_p": 1.1}, {"seed": -1}, {"seed": True}, {"seed": 1.5},
    {"max_tokens": 0}, {"max_tokens": 4097}, {"max_tokens": True},
    {"response_format": {"type": "text"}}, {"response_format": "json_object"},
    {"reasoning_effort": "extreme"}, {"stream": True},
])
def test_invalid_values_rejected(bad):
    with pytest.raises(LlmConfigError):
        _params(bad)


def test_error_names_key_not_value():
    secret = "SECRET-" + "x" * 8
    with pytest.raises(LlmConfigError) as ei:
        _params({"reasoning_effort": secret})
    assert secret not in str(ei.value) and "reasoning_effort" in str(ei.value)
    with pytest.raises(LlmConfigError) as ei:
        _params({secret: 1})
    assert "알 수 없는" in str(ei.value)


def test_params_not_mapping_and_unknown_feature_key():
    with pytest.raises(LlmConfigError):
        parse_config(_data(params=[1]))
    with pytest.raises(LlmConfigError):
        parse_config(_data(extra=1))


def test_load_config_check_keys(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps(_data()), encoding="utf-8")
    with pytest.raises(LlmConfigError):
        load_config(p, env={})
    assert "f" in load_config(p, env={}, check_keys=False).features


def test_deploy_chat_yaml_values():
    cfg = load_config(ROOT / "deploy/llm.chat.yaml", check_keys=False)
    assert sorted(cfg.features) == ["chat", "schedule"]
    assert dict(cfg.features["chat"].params) == {}
    assert dict(cfg.features["schedule"].params) == {"temperature": 0, "reasoning_effort": "low"}
    assert cfg.providers["nvidia"].timeout_s == 40.0


def test_example_yaml_still_loads():
    load_config(ROOT / "deploy/llm.example.yaml", check_keys=False)


def _post(params, **kw):
    seen = {}

    def handler(req):
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    cfg = parse_config(_data())
    t = HttpxTransport(transport=httpx.MockTransport(handler), **kw)
    asyncio.run(t.send(provider=cfg.providers["p"], model="m", base_url="https://a.example/v1",
                       api_key=KEY, messages=[{"role": "user", "content": "q"}], params=params))
    return seen["body"]


def test_transport_merges_params_and_overrides_max_tokens():
    b = _post({"temperature": 0, "max_tokens": 1000}, max_tokens=2048)
    assert b["temperature"] == 0 and b["max_tokens"] == 1000 and b["stream"] is False
    assert _post(None, max_tokens=2048)["max_tokens"] == 2048
    assert "temperature" not in _post({})
    b = _post({"temperature": 0})
    assert b["max_tokens"] == 2048


class Rec:
    def __init__(self):
        self.calls = []

    async def send(self, *, provider, model, base_url, api_key, messages, **kw):
        self.calls.append(kw)
        return TransportResponse(200, "ok")


def _client(data):
    sink = MemorySink()
    c = LlmClient(parse_config(data), Rec(), AuditLog(sink, run_id="r", actor="t"), env={"K": KEY})
    return c, sink


async def test_client_passes_params_only_when_nonempty_and_audits_names():
    d = _data({"temperature": 0, "seed": 7})
    d["features"]["g"] = {"provider": "p", "model": "m"}
    c, sink = _client(d)
    msgs = [{"role": "user", "content": "q"}]
    await c.complete("f", msgs)
    await c.complete("g", msgs)
    t = c._transport
    assert t.calls == [{"params": {"temperature": 0, "seed": 7}}, {}]
    calls = [e for e in sink.events if e.phase == "call"]
    assert calls[0].data["args"]["params"] == ["seed", "temperature"]
    assert "params" not in calls[1].data["args"]
    assert KEY not in str(sink.events)
