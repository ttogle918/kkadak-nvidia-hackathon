"""audit/v1 이벤트 모델 — D4(policy_proposer)의 입력 계약.

필드를 바꾸려면 SCHEMA 버전을 올린다.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Literal

SCHEMA = "audit/v1"
SOURCES = ("core.audit", "openshell")
Phase = Literal["call", "result", "error", "observe"]
Kind = Literal["tool", "net", "file"]
ALLOWED_COMBOS = {
    ("call", "tool"),
    ("result", "tool"),
    ("error", "tool"),
    ("observe", "net"),
    ("observe", "file"),
}
REQUIRED_KEYS = (
    "seq", "ts", "run_id", "actor", "phase", "kind", "name", "call_id", "data", "source", "schema",
)
DECISIONS = ("allowed", "denied", "observed")
FILE_MODES = ("read", "write")

_DATA_KEYS: dict[tuple[str, str], frozenset[str]] = {
    ("call", "tool"): frozenset({"args"}),
    ("result", "tool"): frozenset({"ok", "summary"}),
    ("error", "tool"): frozenset({"ok", "error_type", "message"}),
    ("observe", "net"): frozenset(
        {"host", "port", "binary", "method", "path", "decision", "raw"}
    ),
    ("observe", "file"): frozenset({"path", "mode"}),
}


class AuditError(Exception):
    pass


class AuditFormatError(AuditError, ValueError):
    pass


class AuditWriteError(AuditError):
    pass


def _nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _opt_str(v: Any) -> bool:
    return v is None or isinstance(v, str)


def _check_data(phase: str, kind: str, data: Any) -> None:
    if not isinstance(data, dict):
        raise AuditFormatError("data 가 dict 가 아니다")
    expected = _DATA_KEYS[(phase, kind)]
    if set(data) != expected:
        raise AuditFormatError(
            f"data 키 집합 불일치: 기대 {sorted(expected)}, 실제 {sorted(data)}"
        )
    combo = (phase, kind)
    if combo == ("call", "tool"):
        if not isinstance(data["args"], dict):
            raise AuditFormatError("data.args 가 dict 가 아니다")
    elif combo == ("result", "tool"):
        if data["ok"] is not True or not isinstance(data["summary"], str):
            raise AuditFormatError("result data 는 ok=True, summary=str 이어야 한다")
    elif combo == ("error", "tool"):
        if (
            data["ok"] is not False
            or not isinstance(data["error_type"], str)
            or not isinstance(data["message"], str)
        ):
            raise AuditFormatError("error data 는 ok=False, error_type·message=str 이어야 한다")
    elif combo == ("observe", "net"):
        if not _nonempty_str(data["host"]):
            raise AuditFormatError("net host 가 비어 있다")
        port = data["port"]
        if not _is_int(port) or not 1 <= port <= 65535:
            raise AuditFormatError("net port 는 1..65535 정수여야 한다")
        if data["decision"] not in DECISIONS:
            raise AuditFormatError("net decision 이 허용값이 아니다")
        for key in ("binary", "method", "path", "raw"):
            if not _opt_str(data[key]):
                raise AuditFormatError(f"net {key} 는 str 또는 null 이어야 한다")
    else:  # observe/file
        path = data["path"]
        if not isinstance(path, str) or not path.startswith("/"):
            raise AuditFormatError("file path 는 / 로 시작해야 한다")
        if data["mode"] not in FILE_MODES:
            raise AuditFormatError("file mode 가 허용값이 아니다")


@dataclass(frozen=True)
class AuditEvent:
    seq: int
    ts: str
    run_id: str
    actor: str
    phase: Phase
    kind: Kind
    name: str
    call_id: str | None
    data: dict[str, Any]
    source: str = "core.audit"
    schema: str = SCHEMA

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, line: str) -> AuditEvent:
        try:
            obj = json.loads(line)
        except (ValueError, TypeError) as exc:
            raise AuditFormatError(f"JSON 파싱 실패: {exc}") from exc
        if not isinstance(obj, dict):
            raise AuditFormatError("최상위가 dict 가 아니다")
        keys = set(obj)
        required = set(REQUIRED_KEYS)
        if keys != required:
            missing = sorted(required - keys)
            extra = sorted(keys - required)
            raise AuditFormatError(f"키 집합 불일치: 빠짐 {missing}, 여분 {extra}")
        if obj["schema"] != SCHEMA:
            raise AuditFormatError(f"알 수 없는 schema: {obj['schema']!r}")
        if obj["source"] not in SOURCES:
            raise AuditFormatError(f"알 수 없는 source: {obj['source']!r}")
        if not _is_int(obj["seq"]) or obj["seq"] < 1:
            raise AuditFormatError("seq 는 1 이상의 정수여야 한다")
        for key in ("ts", "run_id", "actor", "name"):
            if not _nonempty_str(obj[key]):
                raise AuditFormatError(f"{key} 는 비어 있지 않은 str 이어야 한다")
        phase, kind = obj["phase"], obj["kind"]
        if not (isinstance(phase, str) and isinstance(kind, str)) or (
            phase,
            kind,
        ) not in ALLOWED_COMBOS:
            raise AuditFormatError(f"허용되지 않는 phase/kind 조합: {phase!r}/{kind!r}")
        if kind == "tool":
            if not _nonempty_str(obj["call_id"]):
                raise AuditFormatError("tool 이벤트는 call_id 가 필요하다")
        elif obj["call_id"] is not None:
            raise AuditFormatError("observe 이벤트의 call_id 는 null 이어야 한다")
        _check_data(phase, kind, obj["data"])
        return cls(**{k: obj[k] for k in REQUIRED_KEYS})
