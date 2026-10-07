import json
import re
from datetime import UTC, datetime

import pytest

from core.audit import REDACTED, AuditLog, JsonlSink, MemorySink, redact, redact_text
from core.audit.redact import truncate

NV = "nvapi-" + "A" * 20
BEARER = "Bearer " + "b" * 20
PAT = re.compile(r"nvapi-[A-Za-z0-9_\-]{10,}")


def mk(sink):
    return AuditLog(sink, run_id="r", actor="a",
                    clock=lambda: datetime(2026, 1, 1, tzinfo=UTC))


def test_redact_secret_keys_nested():
    out = redact({"API_Key": "x", "n": {"token": "y", "ok": [{"Password": "z"}]}, "t": ("a",)})
    assert out["API_Key"] == REDACTED
    assert out["n"]["token"] == REDACTED
    assert out["n"]["ok"][0]["Password"] == REDACTED
    assert out["t"] == ["a"]


def test_redact_nvapi_value_anywhere():
    out = redact({"a": [f"x {NV} y"], "b": {"c": NV}})
    assert NV not in json.dumps(out)


def test_truncate_long_strings():
    assert truncate("a" * 600) == "a" * 512 + "…(+88)"
    assert len(redact({"a": "b" * 1000})["a"]) < 600


def test_redact_before_truncate():
    s = "x" * 505 + NV
    out = redact({"a": s})["a"]
    assert "nvapi-" not in out


def test_redact_text_does_not_truncate():
    assert len(redact_text("y" * 2000)) == 2000


def test_non_json_value_repr_redacted():
    class O:
        def __repr__(self):
            return f"O({NV})"

    assert NV not in json.dumps(redact({"o": O()}))


def test_result_summary_redacted():
    sink = MemorySink()
    log = mk(sink)
    cid = log.call("t", {})
    ev = log.result(cid, {"k": NV})
    assert PAT.search(ev.to_json()) is None


def test_error_message_redacted():
    sink = MemorySink()
    log = mk(sink)
    cid = log.call("t", {})
    ev = log.error(cid, RuntimeError(f"auth failed {BEARER}"))
    assert "b" * 20 not in ev.to_json()
    assert REDACTED in ev.data["message"]


def test_observe_raw_and_path_redacted():
    log = mk(MemorySink())
    ev = log.observe_net("a.io", 443, path=f"/x?token={NV}", raw=f"GET {NV}", binary=NV)
    assert PAT.search(ev.to_json()) is None
    assert REDACTED in ev.data["raw"] and REDACTED in ev.data["path"]


def test_name_redacted():
    sink = MemorySink()
    log = mk(sink)
    log.call(f"tool-{NV}", {})
    assert PAT.search(sink.events[-1].to_json()) is None


def test_event_json_never_contains_secret(tmp_path):
    p = tmp_path / "l.jsonl"
    log = mk(JsonlSink(p))
    cid = log.call("t", {"api_key": NV, "x": f"hi {NV}", "n": [NV]})
    log.result(cid, NV)
    cid = log.call("t", {})
    log.error(cid, ValueError(NV))
    log.observe_net("a.io", 1, path=NV, raw=NV)
    log.observe_file("/tmp/" + NV, "write")
    text = p.read_text()
    assert PAT.search(text) is None
    assert re.search(r"(?i)bearer\s+[a-z0-9]{10,}", text) is None

PLAIN_LEAKS = [
    "GET /x?api_key=plainvalue1",
    "token=abcdef",
    "Authorization: Basic dXNlcjpwYXNz",
    "x-api-key: plainvalue1",
    "password = 'hunter two'",
    "{'token': 'plainvalue1'}",
    '{"access_token": "plainvalue1"}',
    "passwd:plainvalue1",
]


@pytest.mark.parametrize("s", PLAIN_LEAKS)
def test_key_value_secrets_masked(s):
    out = redact_text(s)
    assert REDACTED in out
    for leak in ("plainvalue1", "abcdef", "dXNlcjpwYXNz", "hunter"):
        assert leak not in out


def test_key_name_preserved_and_value_only_masked():
    assert redact_text("token=abc&x=1") == f"token={REDACTED}&x=1"


@pytest.mark.parametrize(
    "s", ["max_tokens=5", "tokens: 3", "the token was refreshed", "keyboard=us", "token count"]
)
def test_no_overmasking(s):
    assert redact_text(s) == s


def test_result_summary_repr_dict_masked():
    log = mk(MemorySink())
    cid = log.call("t", {})
    ev = log.result(cid, {"token": "plainvalue1", "n": 1})
    assert "plainvalue1" not in ev.to_json()


def test_dict_key_position_secret_masked():
    out = redact({NV: 1, "n": {NV: 2}})
    assert NV not in json.dumps(out)
    sink = MemorySink()
    mk(sink).call("t", {"n": {NV: 2}})
    assert NV not in sink.events[0].to_json()


def test_tavily_key_shape_is_redacted():
    key = "tvly-" + "a" * 24
    assert key not in redact_text(f"error for {key} here")
