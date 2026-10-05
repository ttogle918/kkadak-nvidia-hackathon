"""policy_proposer 출력 모델 — 모두 불변. 결과는 항상 초안이다(SCOPE 4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Evidence:
    count: int
    allowed: int
    denied: int
    observed: int
    first_seq: int  # 묶인 이벤트들의 최소 seq
    run_ids: tuple[str, ...]  # 정렬, 중복 제거
    sources: tuple[str, ...]  # 정렬, 중복 제거 ("core.audit"|"openshell")
    sample_raw: str | None


@dataclass(frozen=True)
class NetworkEntry:
    key: str
    name: str  # key.replace("_", "-")
    host: str
    port: int
    protocol: Literal["rest", "tcp"]
    rules: tuple[tuple[str, str], ...]  # (METHOD, path) 정렬. tcp 이면 ()
    binaries: tuple[str, ...]  # 정렬. 항상 1개 이상
    evidence: Evidence


@dataclass(frozen=True)
class FsEntry:
    path: str
    access: Literal["read_only", "read_write"]
    evidence: Evidence


@dataclass(frozen=True)
class ToolUse:
    name: str
    calls: int
    errors: int


@dataclass(frozen=True)
class Skipped:
    subject: str
    reason: str


@dataclass(frozen=True)
class PolicyDraft:
    network: tuple[NetworkEntry, ...]  # key 순 정렬
    filesystem: tuple[FsEntry, ...]  # (access, path) 순 정렬
    skipped: tuple[Skipped, ...]  # (subject, reason) 순 정렬
    event_count: int
    tools: tuple[ToolUse, ...] = ()  # T202-opt 전에는 항상 ()
    status: Literal["draft"] = "draft"  # 사람이 승인하기 전에는 항상 draft
