import hashlib
import random
from pathlib import Path

import pytest

from core.audit import AuditEvent, AuditLog, JsonlSink, MemorySink
from core.policy_proposer import propose, propose_from_jsonl, render_yaml

REPO = Path(__file__).resolve().parents[3]


def mk(run="r1"):
    sink = MemorySink()
    return AuditLog(sink, run_id=run, actor="agent:t"), sink


def net(log, host="api.example.com", port=443, binary="/usr/bin/curl", **kw):
    return log.observe_net(host, port, binary=binary, **kw)


def test_inference_local_skipped():
    log, s = mk()
    net(log, "inference.local", 443)
    d = propose(s.events)
    assert d.network == ()
    assert [x.subject for x in d.skipped] == ["inference.local:443"]
    assert d.skipped[0].reason.startswith("D1")
    assert "network_policies: {}" in render_yaml(d)


def test_missing_binary_skipped():
    log, s = mk()
    net(log, binary=None)
    d = propose(s.events)
    assert d.network == ()
    assert "fail-closed" in d.skipped[0].reason


def test_mixed_l7_rules_only_from_l7():
    log, s = mk()
    net(log, method="get", path="/a")
    net(log)
    d = propose(s.events)
    (e,) = d.network
    assert e.protocol == "rest"
    assert e.rules == (("GET", "/a"),)


def test_all_without_l7_is_tcp():
    log, s = mk()
    net(log)
    (e,) = propose(s.events).network
    assert e.protocol == "tcp" and e.rules == ()


def test_query_string_stripped():
    log, s = mk()
    net(log, method="GET", path="/v1/x?token=1#frag")
    net(log, method="GET", path="?q=1")
    (e,) = propose(s.events).network
    assert e.rules == (("GET", "/"), ("GET", "/v1/x"))


def test_fs_baseline_covered_not_proposed():
    log, s = mk()
    log.observe_file("/usr/lib/x", "read")
    log.observe_file("/tmp/a", "write")
    log.observe_file("/tmp/b", "read")
    log.observe_file("/dev/null", "write")
    d = propose(s.events)
    assert d.filesystem == () and d.skipped == ()


def test_fs_write_under_app_rejected():
    log, s = mk()
    log.observe_file("/app/x", "write")
    log.observe_file("/etc/passwd", "write")
    d = propose(s.events)
    assert d.filesystem == ()
    assert [x.subject for x in d.skipped] == ["/app/x", "/etc/passwd"]


def test_fs_read_and_write_merges_to_rw():
    log, s = mk()
    log.observe_file("/sandbox/a", "read")
    log.observe_file("/sandbox/a", "write")
    log.observe_file("/sandbox/b", "read")
    d = propose(s.events)
    assert [(f.path, f.access) for f in d.filesystem] == [
        ("/sandbox/b", "read_only"),
        ("/sandbox/a", "read_write"),
    ]
    assert d.filesystem[1].evidence.count == 2


def test_tool_events_not_in_policy():
    log, s = mk()
    cid = log.call("t", {"a": 1})
    log.result(cid, "ok")
    d = propose(s.events)
    assert d.network == () and d.filesystem == () and d.tools == ()
    assert d.event_count == 2 and d.status == "draft"


def test_evidence_counts():
    log, s = mk()
    net(log, decision="allowed")
    net(log, decision="allowed")
    net(log, decision="denied")
    net(log, decision="observed", source="openshell")
    log2, s2 = mk("r0")
    net(log2)
    (e,) = propose(list(s.events) + list(s2.events)).network
    ev = e.evidence
    assert (ev.count, ev.allowed, ev.denied, ev.observed) == (5, 2, 1, 2)
    assert ev.first_seq == 1
    assert ev.run_ids == ("r0", "r1")
    assert ev.sources == ("core.audit", "openshell")


def test_sample_raw_skips_events_without_raw():
    log, s = mk()
    net(log)
    net(log, raw="B")
    net(log, raw="C")
    (e,) = propose(s.events).network
    assert e.evidence.sample_raw == "B"


def test_key_collision_gets_hash_suffix():
    log, s = mk()
    net(log, "a.b", 443)
    net(log, "a-b", 443)
    d1 = propose(s.events)
    d2 = propose(reversed(s.events))
    keys = [n.key for n in d1.network]
    assert len(set(keys)) == 2 and all(k.startswith("a_b_443_") for k in keys)
    assert keys == [n.key for n in d2.network]
    h = hashlib.sha256(b"a.b:443").hexdigest()[:8]
    assert f"a_b_443_{h}" in keys


def test_no_collision_no_suffix():
    log, s = mk()
    net(log, "a.b", 443)
    net(log, "a.b", 80)
    assert [n.key for n in propose(s.events).network] == ["a_b_443", "a_b_80"]


def test_deterministic_under_shuffle():
    log, s = mk()
    net(log, method="GET", path="/a", raw="x")
    net(log, "h2.example.com", 80, binary="/bin/b")
    log.observe_file("/sandbox/a", "write")
    log.observe_file("/app/z", "write")
    cid = log.call("t", {})
    log.result(cid, 1)
    base = render_yaml(propose(s.events))
    evs = list(s.events)
    for seed in range(5):
        random.Random(seed).shuffle(evs)
        assert render_yaml(propose(evs)) == base


def test_non_event_rejected():
    with pytest.raises(TypeError):
        propose([{"seq": 1}])


def test_propose_from_jsonl(tmp_path):
    p = tmp_path / "a.jsonl"
    log = AuditLog(JsonlSink(p), run_id="r1", actor="agent:t")
    net(log, method="GET", path="/a")
    d = propose_from_jsonl(p)
    assert d.network[0].rules == (("GET", "/a"),) and d.event_count == 1
    assert isinstance(AuditEvent.from_json(p.read_text().splitlines()[0]), AuditEvent)


def test_no_file_written(tmp_path, monkeypatch):
    deploy = REPO / "deploy/openshell/policy.yaml"
    before = hashlib.sha256(deploy.read_bytes()).hexdigest()
    monkeypatch.chdir(tmp_path)
    log, s = mk()
    net(log)
    render_yaml(propose(s.events))
    assert list(tmp_path.iterdir()) == []
    assert hashlib.sha256(deploy.read_bytes()).hexdigest() == before
