from pathlib import Path

import pytest

from core.audit import AuditEvent, AuditLog, MemorySink
from core.policy_proposer import propose, render_yaml
from core.policy_proposer.render import _scalar

REPO = Path(__file__).resolve().parents[3]


def mk():
    s = MemorySink()
    return AuditLog(s, run_id="r1", actor="agent:t"), s


def norm(text):
    lines = [x.rstrip() for x in text.splitlines()]
    return [x for x in lines if x and not x.startswith("#")]


def test_empty_matches_deploy_baseline():
    deploy = (REPO / "deploy/openshell/policy.yaml").read_text(encoding="utf-8")
    assert norm(render_yaml(propose([]))) == norm(deploy)


def test_golden_rest_entry():
    log, s = mk()
    for m, p in (("GET", "/v1/items"), ("GET", "/v1/items"), ("POST", "/v1/items")):
        log.observe_net(
            "api.example.com", 443, binary="/usr/bin/curl", method=m, path=p,
            decision="allowed", raw="L7 line",
        )
    out = render_yaml(propose(s.events))
    expected = """network_policies:
  # 근거: 관찰 3회 (allowed 3 / denied 0 / observed 0), 첫 seq 1, run r1, 출처 core.audit
  # 실측: L7 line
  api_example_com_443:
    name: api_example_com_443
    endpoints:
      - host: api.example.com
        port: 443
        protocol: rest
        enforcement: enforce
        rules:
          - allow:
              method: GET
              path: /v1/items
          - allow:
              method: POST
              path: /v1/items
    binaries:
      - path: /usr/bin/curl
"""
    assert out.endswith(expected)
    assert out.endswith("\n") and not out.endswith("\n\n")


def test_tcp_entry_has_no_l7_fields():
    log, s = mk()
    log.observe_net("db.example.com", 5432, binary="/usr/bin/psql")
    out = render_yaml(propose(s.events))
    block = out[out.index("network_policies:"):]
    assert "protocol: tcp" in block
    assert "enforcement" not in block and "rules" not in block


def test_fs_proposal_rendered_with_comment():
    log, s = mk()
    log.observe_file("/sandbox/a", "write")
    out = render_yaml(propose(s.events))
    assert "    # 제안: 관찰 1회, 첫 seq 1, run r1\n    - /sandbox/a\n" in out
    assert out.index("/sandbox/a") > out.index("read_write:")


def test_scalar_quoting():
    for v in ("/usr/local/bin/python3.13", "best_effort", "api_example_com_443", "GET"):
        assert _scalar(v) == v
    for v in ("1000", "true", "y", "-x", "a b", "a:b", "1.5", "2026-10-04", "10.0.0.1"):
        assert _scalar(v) == f'"{v}"'
    assert _scalar(True) == "true" and _scalar(443) == "443"
    with pytest.raises(TypeError):
        _scalar(1.5)
    with pytest.raises(TypeError):
        _scalar(None)


def test_comment_injection_neutralized():
    log, s = mk()
    log.observe_net(
        "a.example.com", 443, binary="/b", raw="x\nnetwork_policies: {evil: 1}\r y: 2"
    )
    out = render_yaml(propose(s.events))
    for line in out.splitlines():
        if "evil" in line:
            assert line.lstrip().startswith("#")
    keys = [x for x in out.splitlines() if x.startswith("network_policies:")]
    assert keys == ["network_policies:"]


def test_comment_truncated_to_200():
    log, s = mk()
    log.observe_net("a.example.com", 443, binary="/b", raw="z" * 500)
    out = render_yaml(propose(s.events))
    line = next(x for x in out.splitlines() if "실측" in x)
    assert line == "  # 실측: " + "z" * 200


def test_sample_raw_redacted_in_render():
    secret = "nvapi-" + "A" * 20
    log, _ = mk()
    e = log.observe_net("a.example.com", 443, binary="/b")
    d = e.to_json().replace('"raw": null', f'"raw": "key {secret}"')
    ext = AuditEvent.from_json(d)
    assert secret in ext.data["raw"]  # 외부 파일 경로 재현: audit 단계 치환이 없었다
    out = render_yaml(propose([ext]))
    assert "nvapi-AAAA" not in out and "***REDACTED***" in out


def test_header_marks_draft():
    out = render_yaml(propose([]))
    assert out.startswith("# DRAFT")
    assert "사람 승인 전 적용 금지" in out.splitlines()[0]
    assert "이벤트 0건" in out.splitlines()[1]
    assert propose([]).status == "draft"


def _key_name_pairs(out):
    """렌더된 network_policies 의 (항목 키, name) 쌍. 외부 YAML 의존성 없이 줄 단위로 읽는다."""
    block = out[out.index("network_policies:"):].splitlines()[1:]
    pairs, key = [], None
    for ln in block:
        if ln.startswith("  ") and not ln.startswith("   ") and ln.strip().endswith(":"):
            if not ln.lstrip().startswith("#"):
                key = ln.strip()[:-1].strip('"')
        elif ln.startswith("    name: ") and key is not None:
            pairs.append((key, ln[len("    name: "):].strip('"')))
    return pairs


def test_network_entry_name_equals_key():
    # 문서: "name ... Must match the policy key it is nested under" (밑줄 허용, 하이픈 변환 금지)
    # https://docs.nvidia.com/nemoclaw/user-guide/openclaw/network-policy/configure-policies/change-baseline-network-policy
    log, s = mk()
    log.observe_net("api.example.com", 443, binary="/usr/bin/curl", method="GET", path="/a")
    log.observe_net("db.example.com", 5432, binary="/usr/bin/psql")
    log.observe_net("a.b", 443, binary="/usr/bin/curl")  # 키 충돌 -> 해시 접미사
    log.observe_net("a-b", 443, binary="/usr/bin/curl")
    log.observe_net("x.example.com", 443, binary="/usr/bin/curl", method="GET", path="/a")
    log.observe_net("x.example.com", 443, binary="/usr/bin/wget", method="GET", path="/a")
    log.observe_net("x.example.com", 443, binary="/usr/bin/wget", method="POST", path="/b")
    draft = propose(s.events)
    pairs = _key_name_pairs(render_yaml(draft))
    assert len(pairs) == len(draft.network) >= 6
    assert any("_" in k and k.rsplit("_", 1)[1] != "443" for k, _ in pairs)  # 해시 접미사 포함
    for key, name in pairs:
        assert name == key
        assert "-" not in name
    assert all(n.name == n.key for n in draft.network)
