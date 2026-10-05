"""PolicyDraft → OpenShell 정책 YAML 초안 문자열 (결정적 미니 에미터, 파일에 쓰지 않는다).

스키마 문서 미확인 가정: 정책 스키마 문서를 확인하지 못했다 — 근거: 선행 프로젝트의
`deploy/openshell/policy-nat.yaml` 실측(openshell 0.0.116, 프로젝트명은 D3 로 적지 않는다). 사람이 문서를 붙여 주면 대조한다.
(deploy/openshell/policy.yaml 주석의 스키마 URL 은 이 구현이 열어 본 것이 아니다.)
출력은 초안이며 자동 적용 경로가 없다(SCOPE 4).
"""

from __future__ import annotations

import json
import re

from core.audit import redact_text
from core.policy_proposer import baseline
from core.policy_proposer.model import Evidence, FsEntry, NetworkEntry, PolicyDraft

_BARE = re.compile(r"[A-Za-z_/][A-Za-z0-9_./@+-]*")
_RESERVED = {"true", "false", "null", "yes", "no", "on", "off", "y", "n"}
_COMMENT_MAX = 200


def _scalar(v: object) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        if _BARE.fullmatch(v) and v.lower() not in _RESERVED:
            return v
        return json.dumps(v, ensure_ascii=False)
    raise TypeError(f"지원하지 않는 스칼라 타입: {type(v).__name__}")


def _c(v: object) -> str:
    """주석에 들어가는 값: redact → 줄바꿈 제거 → 200자 절단 (순서 고정)."""
    s = redact_text(str(v))
    s = "".join(c if c.isprintable() else " " for c in s)  # C0/C1·BOM·서로게이트·줄바꿈
    return s[:_COMMENT_MAX]


def _ev_head(ev: Evidence) -> str:
    return f"run {_c(','.join(ev.run_ids))}"


def _fs_lines(base: tuple[str, ...], extra: list[FsEntry]) -> list[str]:
    lines = [f"    - {_scalar(p)}" for p in base]
    for f in extra:
        ev = f.evidence
        lines.append(f"    # 제안: 관찰 {ev.count}회, 첫 seq {ev.first_seq}, {_ev_head(ev)}")
        lines.append(f"    - {_scalar(f.path)}")
    return lines


def _net_lines(n: NetworkEntry) -> list[str]:
    ev = n.evidence
    head = (
        f"  # 근거: 관찰 {ev.count}회 (allowed {ev.allowed} / denied {ev.denied} / "
        f"observed {ev.observed}), 첫 seq {ev.first_seq}, {_ev_head(ev)}, "
        f"출처 {_c(','.join(ev.sources))}"
    )
    out = [head]
    if ev.sample_raw is not None:
        out.append(f"  # 실측: {_c(ev.sample_raw)}")
    out += [
        f"  {_scalar(n.key)}:",
        f"    name: {_scalar(n.name)}",
        "    endpoints:",
        f"      - host: {_scalar(n.host)}",
        f"        port: {_scalar(n.port)}",
        f"        protocol: {_scalar(n.protocol)}",
    ]
    if n.protocol == "rest":
        out += ["        enforcement: enforce", "        rules:"]
        for method, path in n.rules:
            out += [
                "          - allow:",
                f"              method: {_scalar(method)}",
                f"              path: {_scalar(path)}",
            ]
    out.append("    binaries:")
    out += [f"      - path: {_scalar(b)}" for b in n.binaries]
    return out


def render_yaml(draft: PolicyDraft) -> str:
    ro = [f for f in draft.filesystem if f.access == "read_only"]
    rw = [f for f in draft.filesystem if f.access == "read_write"]
    input_line = (
        f"# 입력: audit/v1 이벤트 {draft.event_count}건 (D4). "
        "filesystem_policy 변경은 샌드박스 재생성 필요"
    )
    lines = [
        "# DRAFT — core.policy_proposer 생성. 사람 승인 전 적용 금지 (D2·SCOPE 4)",
        input_line,
        f"version: {_scalar(baseline.VERSION)}",
        "",
        "filesystem_policy:",
        f"  include_workdir: {_scalar(baseline.INCLUDE_WORKDIR)}",
        "  read_only:",
        *_fs_lines(baseline.READ_ONLY, ro),
        "  read_write:",
        *_fs_lines(baseline.READ_WRITE, rw),
        "",
        "landlock:",
        f"  compatibility: {_scalar(baseline.LANDLOCK_COMPAT)}",
        "",
        "process:",
        f"  run_as_user: {_scalar(baseline.RUN_AS_USER)}",
        f"  run_as_group: {_scalar(baseline.RUN_AS_GROUP)}",
        "",
    ]
    if draft.network:
        lines.append("network_policies:")
        for n in draft.network:
            lines += _net_lines(n)
    else:
        lines.append("network_policies: {}")
    return "\n".join(lines) + "\n"
