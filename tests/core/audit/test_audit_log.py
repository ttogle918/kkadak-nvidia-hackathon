import threading
from datetime import UTC, datetime

import pytest

from core.audit import (
    AuditLog,
    AuditWriteError,
    JsonlSink,
    MemorySink,
    audited,
    read_jsonl,
)
from core.audit.events import AuditFormatError


def mk(sink=None):
    sink = sink if sink is not None else MemorySink()
    clock = lambda: datetime(2026, 1, 1, tzinfo=UTC)
    return AuditLog(sink, run_id="r", actor="agent:1", clock=clock), sink


class BadSink:
    def __init__(self):
        self.fail = True
        self.events = []

    def write(self, event):
        if self.fail:
            raise OSError("disk")
        self.events.append(event)


def test_call_event_emitted_before_body():
    log, sink = mk()
    seen = []

    @audited(log)
    def tool(x):
        seen.append(sink.events[-1])
        return x

    tool(3)
    assert seen[0].phase == "call" and seen[0].name == "tool"
    assert seen[0].data["args"] == {"x": 3}
    assert [e.phase for e in sink.events] == ["call", "result"]


def test_audited_rejects_async():
    log, _ = mk()
    with pytest.raises(TypeError):
        @audited(log)
        async def f():
            return 1


def test_error_recorded_and_reraised():
    log, sink = mk()

    @audited(log, name="boom")
    def f():
        raise KeyError("k")

    with pytest.raises(KeyError):
        f()
    ev = sink.events[-1]
    assert ev.phase == "error" and ev.data["error_type"] == "KeyError" and ev.name == "boom"


def test_sink_failure_blocks_tool_body():
    sink = BadSink()
    log, _ = mk(sink)
    ran = []

    @audited(log)
    def f():
        ran.append(True)

    with pytest.raises(AuditWriteError):
        f()
    assert ran == []


def test_failed_write_does_not_consume_seq():
    sink = BadSink()
    log, _ = mk(sink)
    with pytest.raises(AuditWriteError):
        log.call("t", {})
    sink.fail = False
    log.call("t", {})
    assert [e.seq for e in sink.events] == [1]


def test_seq_contiguous_under_threads(tmp_path):
    path = tmp_path / "a" / "log.jsonl"
    log, _ = mk(JsonlSink(path))

    def work():
        for _ in range(25):
            cid = log.call("t", {"a": 1})
            log.result(cid, 1)

    ts = [threading.Thread(target=work) for _ in range(8)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    events = read_jsonl(path)
    seqs = [e.seq for e in events]
    assert seqs == list(range(1, 401))


def test_result_unknown_call_id_raises():
    log, _ = mk()
    with pytest.raises(ValueError):
        log.result("nope", 1)


def test_double_result_raises():
    log, _ = mk()
    cid = log.call("t", {})
    log.result(cid, 1)
    with pytest.raises(ValueError):
        log.result(cid, 1)
    with pytest.raises(ValueError):
        log.error(cid, RuntimeError("x"))


def test_read_jsonl_bad_line_reports_line_number(tmp_path):
    log, _ = mk(JsonlSink(tmp_path / "l.jsonl"))
    log.call("t", {})
    with open(tmp_path / "l.jsonl", "a") as f:
        f.write("garbage\n")
    with pytest.raises(AuditFormatError, match="2"):
        read_jsonl(tmp_path / "l.jsonl")


def test_read_jsonl_skips_blank_lines(tmp_path):
    p = tmp_path / "l.jsonl"
    log, _ = mk(JsonlSink(p))
    log.call("t", {})
    with open(p, "a") as f:
        f.write("\n   \n")
    assert len(read_jsonl(p)) == 1


def test_observe_net_normalizes_host_method():
    log, _ = mk()
    ev = log.observe_net("API.Example.COM", 443, method="get")
    assert ev.data["host"] == "api.example.com" and ev.data["method"] == "GET"
    assert ev.name == "api.example.com:443" and ev.call_id is None


def test_observe_net_rejects_unknown_source():
    log, _ = mk()
    with pytest.raises(ValueError):
        log.observe_net("a.io", 1, source="evil")
    with pytest.raises(ValueError):
        log.observe_net("a.io", True)
    with pytest.raises(ValueError):
        log.observe_net("a.io", 80, decision="maybe")


def test_observe_file_normalizes_and_rejects_relative():
    log, _ = mk()
    assert log.observe_file("/a/b/../c", "read").data["path"] == "/a/c"
    with pytest.raises(ValueError):
        log.observe_file("a/b", "read")


def test_empty_run_id_or_actor():
    with pytest.raises(ValueError):
        AuditLog(MemorySink(), run_id="", actor="a")
    with pytest.raises(ValueError):
        AuditLog(MemorySink(), run_id="r", actor=" ")


@pytest.mark.parametrize("name", ["", "   ", None, 3])
def test_call_rejects_bad_name_without_seq(name):
    sink = MemorySink()
    log = AuditLog(sink, run_id="r", actor="a")
    with pytest.raises((ValueError, TypeError)):
        log.call(name, {})
    assert sink.events == []
    log.call("ok", {})
    assert sink.events[0].seq == 1


def test_call_rejects_non_mapping_args():
    log = AuditLog(MemorySink(), run_id="r", actor="a")
    with pytest.raises(TypeError):
        log.call("t", [1])


@pytest.mark.parametrize("field", ["binary", "method", "path", "raw"])
def test_observe_net_rejects_non_str_fields(field, tmp_path):
    p = tmp_path / "l.jsonl"
    log = AuditLog(JsonlSink(p), run_id="r", actor="a")
    with pytest.raises((ValueError, TypeError)):
        log.observe_net("a.io", 443, **{field: 5})
    log.observe_net("a.io", 443, path="/ok")
    events = read_jsonl(p)
    assert [e.seq for e in events] == [1]
