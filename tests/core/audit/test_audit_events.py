import json

import pytest

from core.audit.events import AuditEvent, AuditFormatError

TOOL_DATA = {
    ("call", "tool"): {"args": {"a": 1}},
    ("result", "tool"): {"ok": True, "summary": "1"},
    ("error", "tool"): {"ok": False, "error_type": "ValueError", "message": "x"},
}
NET = {"host": "a.io", "port": 443, "binary": None, "method": "GET", "path": "/",
       "decision": "observed", "raw": None}
FILE = {"path": "/tmp/x", "mode": "read"}


def make(phase="call", kind="tool", **over):
    if kind == "tool":
        data, call_id, name = TOOL_DATA.get((phase, kind), {"args": {}}), "c1", "t"
    elif kind == "net":
        data, call_id, name = dict(NET), None, "a.io:443"
    else:
        data, call_id, name = dict(FILE), None, "/tmp/x"
    d = {"seq": 1, "ts": "2026-01-01T00:00:00.000+00:00", "run_id": "r", "actor": "a",
         "phase": phase, "kind": kind, "name": name, "call_id": call_id, "data": data,
         "source": "core.audit", "schema": "audit/v1"}
    d.update(over)
    return d


def bad(d):
    with pytest.raises(AuditFormatError):
        AuditEvent.from_json(json.dumps(d))


@pytest.mark.parametrize("phase,kind", [("call", "tool"), ("result", "tool"), ("error", "tool"),
                                        ("observe", "net"), ("observe", "file")])
def test_roundtrip_json(phase, kind):
    line = json.dumps(make(phase, kind))
    ev = AuditEvent.from_json(line)
    assert AuditEvent.from_json(ev.to_json()) == ev
    assert "\n" not in ev.to_json()


def test_from_json_rejects_wrong_schema():
    bad(make(schema="audit/v2"))


def test_from_json_rejects_unknown_source():
    bad(make(source="x"))


@pytest.mark.parametrize("key", ["source", "schema", "call_id"])
def test_from_json_missing_field(key):
    d = make()
    del d[key]
    bad(d)


def test_from_json_extra_key_rejected():
    bad(make(extra=1))


@pytest.mark.parametrize("phase,kind", [("observe", "tool"), ("call", "net")])
def test_from_json_bad_combo(phase, kind):
    bad(make(phase=phase, kind=kind))


def test_bad_phase():
    bad(make(phase="nope"))


@pytest.mark.parametrize("seq", [True, 0, -1, 1.5])
def test_seq_bool_or_zero_rejected(seq):
    bad(make(seq=seq))


@pytest.mark.parametrize("port", [0, 65536, True, "80"])
def test_net_port_out_of_range(port):
    d = make("observe", "net")
    d["data"]["port"] = port
    bad(d)


def test_file_relative_path():
    d = make("observe", "file")
    d["data"]["path"] = "rel/x"
    bad(d)


def test_tool_call_without_call_id():
    bad(make(call_id=None))
    bad(make(call_id=""))


def test_observe_with_call_id_rejected():
    bad(make("observe", "net", call_id="c"))


def test_data_keys_mismatch():
    d = make()
    d["data"]["more"] = 1
    bad(d)
    d = make("result", "tool")
    del d["data"]["summary"]
    bad(d)


def test_not_json_or_not_dict():
    with pytest.raises(AuditFormatError):
        AuditEvent.from_json("{nope")
    with pytest.raises(AuditFormatError):
        AuditEvent.from_json("[1]")
