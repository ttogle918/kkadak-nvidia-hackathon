"""재작업 회귀(T202 B1~B3·W1·W2): 외부 jsonl 로 들어온 값은 검증이 약하므로 fail-closed."""

import json

import pytest

from core.audit import AuditEvent, AuditFormatError, AuditLog, MemorySink
from core.policy_proposer import baseline, propose, render_yaml


def _log():
    s = MemorySink()
    return AuditLog(s, run_id="r1", actor="agent:t"), s


def ext(kind, **data):
    """AuditLog 로 틀을 만들고 data 를 덮어쓴 뒤 from_json 으로 다시 읽는다(외부 jsonl 모사)."""
    log, _ = _log()
    if kind == "net":
        base = log.observe_net("seed.example.com", 443, binary="/b")
    else:
        base = log.observe_file("/seed", "read")
    obj = json.loads(base.to_json())
    obj["data"].update(data)
    if kind == "file":
        obj["name"] = data["path"]
    else:
        obj["name"] = data["host"] if "host" in data else obj["name"]
    return AuditEvent.from_json(json.dumps(obj))


def net_ev(host="api.example.com", binary="/b", method="GET", path="/ok", port=443):
    return ext("net", host=host, port=port, binary=binary, method=method, path=path)


def fs_ev(path, mode="write"):
    return ext("file", path=path, mode=mode)


def _assert_absent(d, needle):
    assert not d.network and not d.filesystem
    assert needle not in render_yaml(d)
    assert d.skipped


SECRET = "nvapi-" + "A" * 20  # 키 모양 리터럴을 소스에 두지 않는다


def test_secret_path_not_proposed():
    d = propose([net_ev(path=f"/v1/{SECRET}/x")])
    _assert_absent(d, SECRET)
    assert SECRET not in "".join(s.subject + s.reason for s in d.skipped)


def test_already_redacted_path_not_proposed():
    log, s = _log()
    log.observe_net(
        "api.example.com", 443, binary="/b", method="GET", path=f"/v1/{SECRET}/x"
    )
    d = propose(s.events)
    _assert_absent(d, "REDACTED")


@pytest.mark.parametrize("path", ["/**", "/a/*", "/a[1]", "/{a}", "v1/x"])
def test_bad_rule_path(path):
    d = propose([net_ev(path=path)])
    _assert_absent(d, "**")
    assert "path:" not in render_yaml(d)


@pytest.mark.parametrize("host", ["*.x.com", "a?.com", "a[b].com", "{a}.com", "a b.com"])
def test_bad_host(host):
    d = propose([net_ev(host=host)])
    _assert_absent(d, host)


@pytest.mark.parametrize("binary", ["curl", "bin/curl", "/usr/bin/*", "/a/../b", "/b\n- x"])
def test_bad_binary(binary):
    d = propose([net_ev(binary=binary)])
    _assert_absent(d, "curl")


def test_good_binary_kept_bad_dropped():
    d = propose([net_ev(binary="/ok"), net_ev(binary="rel")])
    (e,) = d.network
    assert e.binaries == ("/ok",)
    assert d.skipped


def test_bad_rule_dropped_good_kept():
    d = propose([net_ev(path="/**"), net_ev(path="/good")])
    (e,) = d.network
    assert e.rules == (("GET", "/good"),)
    assert "/**" not in render_yaml(d)


def test_all_rules_bad_skips_entry_not_downgrade_to_tcp():
    d = propose([net_ev(path="/**")])
    assert d.network == ()


@pytest.mark.parametrize(
    "path", ["/etc/*", "/x/{a}", "/x/" + SECRET, "/x/***REDACTED***"]
)
def test_bad_fs_path(path):
    d = propose([fs_ev(path, "read")])
    _assert_absent(d, "REDACTED")
    assert SECRET not in render_yaml(d)


def test_skipped_subject_redacted():
    d = propose([fs_ev("/x/" + SECRET, "read"), net_ev(host=SECRET + "*")])
    assert d.skipped
    assert all(SECRET not in s.subject and SECRET not in s.reason for s in d.skipped)


@pytest.mark.parametrize("path", ["/data/../app/x", "/./app/x", "//app/x"])
def test_never_write_bypass(path):
    d = propose([fs_ev(path, "write")])
    assert d.filesystem == ()
    assert any("쓰기" in s.reason for s in d.skipped)
    assert "/app/x" not in render_yaml(d)


def test_normalized_fs_path_proposed_when_ok():
    d = propose([fs_ev("/data/../workspace//x", "write")])
    assert [f.path for f in d.filesystem] == ["/workspace/x"]


@pytest.mark.parametrize("host", ["Inference.Local", "inference.local.", " inference.local "])
def test_gateway_host_variants(host):
    d = propose([net_ev(host=host)])
    assert d.network == ()
    assert any(s.reason.startswith("D1") for s in d.skipped)


def test_host_normalized_and_merged():
    d = propose([net_ev(host="API.example.com."), net_ev(host="api.example.com")])
    (e,) = d.network
    assert e.host == "api.example.com" and e.evidence.count == 2


@pytest.mark.parametrize("ch", ["\x00", "\x01", "\x08", "\x0e", "\x1f", "\x7f"])
def test_comment_c0_controls_replaced(ch):
    log, s = _log()
    log.observe_net(
        "api.example.com", 443, binary="/b", raw=f"a{ch}b", decision="allowed"
    )
    out = render_yaml(propose(s.events))
    assert ch not in out
    assert "# 실측: a b" in out


# --- 3차 재작업 (B4·B5·W-a~W-f) ---


@pytest.mark.parametrize("path", ["/", "/sandbox/..", "//"])
def test_root_write_not_proposed(path):
    d = propose([fs_ev(path, "write")])
    assert d.filesystem == () and d.skipped
    assert "- /\n" not in render_yaml(d)


def test_root_read_not_proposed():
    d = propose([fs_ev("/", "read")])
    assert d.filesystem == () and d.skipped


def test_write_ancestor_of_never_write_rejected():
    d = propose([fs_ev("/", "write"), fs_ev("/workspace/x", "write")])
    assert [f.path for f in d.filesystem] == ["/workspace/x"]


def test_anonymous_binary_event_does_not_attach_rule_to_valid_binary():
    d = propose(
        [
            net_ev(binary="/usr/bin/curl", method="GET", path="/ok"),
            net_ev(binary="sh", method="POST", path="/admin"),
        ]
    )
    (e,) = d.network
    assert e.binaries == ("/usr/bin/curl",)
    assert e.rules == (("GET", "/ok"),)
    assert e.evidence.count == 1
    assert "/admin" not in render_yaml(d)
    assert d.skipped


def test_none_binary_event_does_not_attach_rule():
    d = propose(
        [
            net_ev(binary="/usr/bin/curl", method="GET", path="/ok"),
            net_ev(binary=None, method="POST", path="/admin"),
        ]
    )
    (e,) = d.network
    assert e.rules == (("GET", "/ok"),) and e.evidence.count == 1
    assert "/admin" not in render_yaml(d)
    assert d.skipped


def test_only_anonymous_events_skipped():
    d = propose([net_ev(binary=None, method="POST", path="/admin")])
    assert d.network == () and d.skipped


@pytest.mark.parametrize("raw", ["a\x9bb", "a\ufeffb", "a\x80b", "a\x9fb", "a\xa0b"])
def test_comment_c1_bom_replaced(raw):
    log, s = _log()
    log.observe_net("api.example.com", 443, binary="/b", raw=raw, decision="allowed")
    out = render_yaml(propose(s.events))
    assert "# 실측: a b" in out
    for ch in raw:
        if ch != "a" and ch != "b":
            assert ch not in out


def test_comment_lone_surrogate_replaced():
    log, s = _log()
    log.observe_net("api.example.com", 443, binary="/b", raw="a\ud800b", decision="allowed")
    out = render_yaml(propose(s.events))
    assert "\ud800" not in out and "# 실측: a b" in out


@pytest.mark.parametrize(
    "host", ["0.0.0.0/0", "a.com:1", "user@h", "a,b.com", "a_b.com", "999.1.1.1", "ａ.com",
             "-a.com", "a..com", "1.2.3"]
)
def test_host_allowlist_rejects(host):
    d = propose([net_ev(host=host)])
    assert d.network == () and d.skipped


@pytest.mark.parametrize("host", ["api.example.com", "10.0.0.1", "a-b.c1.io"])
def test_host_allowlist_accepts(host):
    d = propose([net_ev(host=host)])
    assert [n.host for n in d.network] == [host]


def test_evidence_counts_only_accepted_events():
    d = propose(
        [
            net_ev(binary="/b", path="/good"),
            net_ev(binary="/b", path="/**"),
            net_ev(binary="rel", path="/good"),
            net_ev(binary=None, path="/good"),
        ]
    )
    (e,) = d.network
    assert e.evidence.count == 1
    assert e.rules == (("GET", "/good"),)


def test_evidence_sample_raw_only_from_accepted():
    a = ext("net", host="api.example.com", port=443, binary="rel", method="GET", path="/x",
            raw="from-rejected", decision="allowed")
    b = ext("net", host="api.example.com", port=443, binary="/b", method="GET", path="/x",
            raw="from-accepted", decision="allowed")
    (e,) = propose([a, b]).network
    assert e.evidence.sample_raw == "from-accepted" and e.evidence.count == 1


def test_host_assertion_uses_lowercase_secret():
    d = propose([net_ev(host=SECRET.lower())])  # 정규화로 소문자가 되어도 거부돼야 한다
    assert d.network == ()
    assert SECRET.lower() not in render_yaml(d)
    assert all(SECRET.lower() not in s.subject + s.reason for s in d.skipped)


def test_trailing_slash_rule_rejected_by_design():
    # 끝 '/' 는 정규화되지 않은 경로로 보고 거부한다(의도): 서버가 /v1/models 와 /v1/models/ 를
    # 다르게 취급할 수 있어 추측으로 하나로 합치지 않는다.
    d = propose([net_ev(path="/v1/models/")])
    assert d.network == () and d.skipped


def test_query_only_path_becomes_root():
    # query 를 떼고 남은 값이 비면 '/' 로 본다(동작 고정). 관찰된 요청이 루트 요청과 같은 경로라
    # 새 권한을 만들지 않는다.
    for raw in ("?q=1", "/?q=1"):
        (e,) = propose([net_ev(path=raw)]).network
        assert e.rules == (("GET", "/"),)


def test_percent_encoding_passes_through():
    # 퍼센트 인코딩은 그대로 통과시킨다: '%' 는 glob/메타가 아니고 YAML 은 따옴표로 감싸 출력하며,
    # 디코딩하지 않으므로 관찰된 문자열 이상으로 넓어지지 않는다(최소 권한 유지).
    (e,) = propose([net_ev(path="/a%2Fb")]).network
    assert e.rules == (("GET", "/a%2Fb"),)


def test_invalid_event_raises_audit_format_error():
    bad = ext("net", host="api.example.com", port=443, binary="/b", method=None, path=None)
    bad.data["port"] = "x"  # 메모리에서 오염된 이벤트: 재검증이 잡아야 한다
    with pytest.raises(AuditFormatError):
        propose([bad])


# --- 4차 재작업 (B6·B7·W1~W8): 거부 목록 → 허용 목록 ---

@pytest.mark.parametrize(
    "path",
    ["/bin/x", "/sbin/x", "/lib64/x", "/lib32/x", "/sys/x", "/boot/x", "/root/x", "/run/x",
     "/var/run/docker.sock", "/var/x", "/home/u/.ssh/k", "/opt/x", "/mnt/x", "/data/x"],
)
def test_write_outside_allowed_roots_skipped(path):
    d = propose([fs_ev(path, "write")])
    assert d.filesystem == ()
    assert any("쓰기 허용 루트 밖" in s.reason for s in d.skipped)


@pytest.mark.parametrize("path", ["/sandbox/x", "/workspace/a/b"])
def test_write_inside_allowed_roots_proposed(path):
    d = propose([fs_ev(path, "write")])
    assert [(f.path, f.access) for f in d.filesystem] == [(path, "read_write")]


@pytest.mark.parametrize(
    "path", ["/root/.ssh/id", "/home/u/.ssh/k", "/var/run/docker.sock", "/mnt/x"]
)
def test_read_outside_allowed_roots_skipped(path):
    d = propose([fs_ev(path, "read")])
    assert d.filesystem == () and any("읽기 허용 루트 밖" in s.reason for s in d.skipped)


@pytest.mark.parametrize("path", ["/bin/ls", "/sandbox/x", "/lib64/ld.so"])
def test_read_inside_allowed_roots_proposed(path):
    d = propose([fs_ev(path, "read")])
    assert [(f.path, f.access) for f in d.filesystem] == [(path, "read_only")]


def test_never_write_second_level_still_blocks(monkeypatch):
    # 이중 방어: 허용 루트가 넓어지거나 잘못 설정돼도 NEVER_WRITE 가 쓰기를 막는다(W7)
    monkeypatch.setattr(baseline, "WRITE_PROPOSAL_ROOTS", ("/var", "/sandbox"))
    monkeypatch.setattr(baseline, "NEVER_WRITE", baseline.NEVER_WRITE + ("/var/lib/x",))
    d = propose([fs_ev("/var", "write"), fs_ev("/var/lib/x/y", "write"), fs_ev("/var/ok", "write")])
    assert [f.path for f in d.filesystem] == ["/var/ok"]


def test_allowed_roots_constants_are_sane():
    for r in baseline.WRITE_PROPOSAL_ROOTS:
        assert not any(r == n or r.startswith(n + "/") for n in baseline.NEVER_WRITE)
        assert r not in ("/", "/tmp")


def test_binaries_only_from_adopted_events():  # B7
    d = propose(
        [net_ev(binary="/bin/sh", path="/**"), net_ev(binary="/usr/bin/curl", path="/good")]
    )
    (e,) = d.network
    assert e.binaries == ("/usr/bin/curl",) and e.rules == (("GET", "/good"),)
    assert "/bin/sh" not in render_yaml(d)


def test_binary_split_no_cross_product():  # W1
    d = propose(
        [
            net_ev(binary="/usr/bin/curl", method="GET", path="/ok"),
            net_ev(binary="/usr/bin/wget", method="POST", path="/admin"),
        ]
    )
    got = {n.binaries: n.rules for n in d.network}
    assert got == {
        ("/usr/bin/curl",): (("GET", "/ok"),),
        ("/usr/bin/wget",): (("POST", "/admin"),),
    }
    assert len({n.key for n in d.network}) == 2


def test_binaries_with_same_rules_merged():
    d = propose(
        [net_ev(binary="/usr/bin/a", path="/ok"), net_ev(binary="/usr/bin/b", path="/ok")]
    )
    (e,) = d.network
    assert e.binaries == ("/usr/bin/a", "/usr/bin/b") and e.evidence.count == 2


def test_tcp_only_binary_not_added_to_l7_endpoint():
    d = propose(
        [
            net_ev(binary="/usr/bin/a", path="/ok"),
            net_ev(binary="/usr/bin/b", method=None, path=None),
        ]
    )
    (e,) = d.network
    assert e.binaries == ("/usr/bin/a",) and e.protocol == "rest"
    assert any("/usr/bin/b" in s.subject for s in d.skipped)


@pytest.mark.parametrize(
    "binary", ["/", "/tmp/evil", "/tmp", "/dev/null", "/sandbox/x", "/workspace/run"]
)
def test_binary_in_writable_location_rejected(binary):  # W2
    d = propose([net_ev(binary=binary)])
    assert d.network == () and d.skipped


def test_binary_under_proposed_rw_path_rejected(monkeypatch):
    monkeypatch.setattr(baseline, "WRITE_PROPOSAL_ROOTS", ("/srv",))
    d = propose([fs_ev("/srv/w", "write"), net_ev(binary="/srv/w/tool")])
    assert d.network == ()


@pytest.mark.parametrize(
    "host", ["0.0.0.0", "127.0.0.1", "127.9.9.9", "169.254.169.254", "169.254.0.1", "localhost",
             "a.localhost", "a.123", "a.0x7f", "0x7f.1", "0xa"]
)
def test_special_hosts_rejected(host):  # W3
    d = propose([net_ev(host=host)])
    assert d.network == () and d.skipped


@pytest.mark.parametrize("m", ["ß", "ı", "ſ", "poſt", "optıons", "get ", "TRACE", "FOO", "CONNECT", "G"])
def test_bad_method_rejected(m):  # W4
    d = propose([net_ev(method=m)])
    assert d.network == ()


def test_method_set_and_lowercase_ok():
    ms = ["get", "Head", "POST", "put", "patch", "delete", "options"]
    d = propose([net_ev(method=m, path=f"/{m}") for m in ms])
    assert {r[0] for n in d.network for r in n.rules} == {m.upper() for m in ms}


@pytest.mark.parametrize("path", ["/a;b", "/a\\b", "/é", "/a:b", "/a=b", "/a,b", "/a b", "/a'b"])
def test_rule_path_charset(path):  # W5
    d = propose([net_ev(path=path)])
    assert d.network == () and d.skipped


@pytest.mark.parametrize("binary", ["/usr/bin/é", "/a;b", "/a\\b"])
def test_binary_charset(binary):
    assert propose([net_ev(binary=binary)]).network == ()


@pytest.mark.parametrize("path", ["/sandbox/é", "/sandbox/a;b", "/sandbox/a\\b"])
def test_fs_charset(path):
    assert propose([fs_ev(path, "write")]).filesystem == ()


def test_charset_accepts_common():
    (e,) = propose([net_ev(path="/v1/a_b.c~d@e+f%2F-g")]).network
    assert e.rules == (("GET", "/v1/a_b.c~d@e+f%2F-g"),)


@pytest.mark.parametrize("kw", [{"method": "GET", "path": None}, {"method": None, "path": "/x"}])
def test_half_l7_events_skipped_not_tcp(kw):  # W6
    d = propose([net_ev(**kw)])
    assert d.network == () and d.skipped


def test_half_l7_not_attached_to_good_rule():
    d = propose([net_ev(path="/ok"), net_ev(method=None, path="/x")])
    (e,) = d.network
    assert e.rules == (("GET", "/ok"),) and e.evidence.count == 1


def test_invalid_event_index_in_message():  # W8
    good = net_ev()
    bad = net_ev()
    bad.data["port"] = "x"
    with pytest.raises(AuditFormatError, match=r"#3"):
        propose([good, good, bad])


def test_to_json_typeerror_wrapped():
    bad = net_ev()
    bad.data["raw"] = object()  # JSON 직렬화 불가
    with pytest.raises(AuditFormatError, match=r"#1"):
        propose([bad])
