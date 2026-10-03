"""호출 직전 발행·순서 보존 감사 로그.

락 안에서 seq 부여와 sink 쓰기를 함께 하므로 파일 줄 순서와 seq 순서가 같다.
"""

from __future__ import annotations

import functools
import inspect
import posixpath
import threading
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol, TypeVar
from uuid import uuid4

from core.audit.events import (
    DECISIONS,
    SOURCES,
    AuditEvent,
    AuditFormatError,
    AuditWriteError,
)
from core.audit.redact import redact, redact_text, truncate

F = TypeVar("F", bound=Callable[..., Any])


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Sink(Protocol):
    def write(self, event: AuditEvent) -> None: ...


class MemorySink:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def write(self, event: AuditEvent) -> None:
        self.events.append(event)


class JsonlSink:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: AuditEvent) -> None:
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(event.to_json() + "\n")
            f.flush()


def _scrub(v: Any) -> Any:
    """모든 str 값에 redact_text 를 다시 적용하는 마지막 방어선. 키도 같이 처리한다."""
    if isinstance(v, str):
        return redact_text(v)
    if isinstance(v, dict):
        return {(redact_text(k) if isinstance(k, str) else k): _scrub(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_scrub(x) for x in v]
    return v


class AuditLog:
    def __init__(
        self,
        sink: Sink,
        *,
        run_id: str,
        actor: str,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("run_id 가 비어 있다")
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError("actor 가 비어 있다")
        self._sink = sink
        self._run_id = run_id
        self._actor = actor
        self._clock = clock
        self._lock = threading.Lock()
        self._seq = 0
        self._open: dict[str, str] = {}

    def _emit(
        self,
        phase: str,
        kind: str,
        name: str,
        call_id: str | None,
        data: dict[str, Any],
        source: str = "core.audit",
    ) -> AuditEvent:
        with self._lock:
            seq = self._seq + 1
            event = AuditEvent(
                seq=seq,
                ts=self._clock().astimezone(UTC).isoformat(timespec="milliseconds"),
                run_id=self._run_id,
                actor=self._actor,
                phase=phase,  # type: ignore[arg-type]
                kind=kind,  # type: ignore[arg-type]
                name=redact_text(name),
                call_id=call_id,
                data=_scrub(data),
                source=source,
            )
            AuditEvent.from_json(event.to_json())  # 기록 전 검증: 읽을 수 없는 줄을 남기지 않는다
            try:
                self._sink.write(event)
            except Exception as exc:
                raise AuditWriteError(f"감사 이벤트 기록 실패: {exc}") from exc
            self._seq = seq
            return event

    def call(self, name: str, args: Mapping[str, Any]) -> str:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name 이 비어 있다")
        if not isinstance(args, Mapping):
            raise TypeError("args 는 Mapping 이어야 한다")
        call_id = uuid4().hex
        self._emit("call", "tool", name, call_id, {"args": redact(args)})
        with self._lock:
            self._open[call_id] = name
        return call_id

    def _check_open(self, call_id: str) -> None:
        with self._lock:
            if call_id not in self._open:
                raise ValueError("unknown or closed call_id")

    def _close(self, call_id: str) -> None:
        with self._lock:
            self._open.pop(call_id, None)

    def _names_get(self, call_id: str) -> str:
        with self._lock:
            return self._open[call_id]

    def result(self, call_id: str, value: Any) -> AuditEvent:
        self._check_open(call_id)
        summary = truncate(redact_text(repr(value)))
        event = self._emit(
            "result", "tool", self._names_get(call_id), call_id, {"ok": True, "summary": summary}
        )
        self._close(call_id)
        return event

    def error(self, call_id: str, exc: BaseException) -> AuditEvent:
        self._check_open(call_id)
        message = truncate(redact_text(str(exc)))
        event = self._emit(
            "error",
            "tool",
            self._names_get(call_id),
            call_id,
            {"ok": False, "error_type": type(exc).__name__, "message": message},
        )
        self._close(call_id)
        return event

    def observe_net(
        self,
        host: str,
        port: int,
        *,
        binary: str | None = None,
        method: str | None = None,
        path: str | None = None,
        decision: str = "observed",
        raw: str | None = None,
        source: str = "core.audit",
    ) -> AuditEvent:
        if not isinstance(host, str) or not host.strip():
            raise ValueError("host 가 비어 있다")
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            raise ValueError("port 는 1..65535 정수여야 한다")
        if decision not in DECISIONS:
            raise ValueError(f"decision 이 허용값이 아니다: {decision!r}")
        if source not in SOURCES:
            raise ValueError(f"source 가 허용값이 아니다: {source!r}")
        for label, val in (("binary", binary), ("method", method), ("path", path), ("raw", raw)):
            if val is not None and not isinstance(val, str):
                raise TypeError(f"{label} 는 str 또는 None 이어야 한다")
        host = host.strip().lower()
        data = {
            "host": host,
            "port": port,
            "binary": binary,
            "method": method.upper() if method is not None else None,
            "path": path,
            "decision": decision,
            "raw": raw,
        }
        return self._emit("observe", "net", f"{host}:{port}", None, data, source)

    def observe_file(self, path: str, mode: Literal["read", "write"]) -> AuditEvent:
        if mode not in ("read", "write"):
            raise ValueError(f"mode 가 허용값이 아니다: {mode!r}")
        if not isinstance(path, str) or not path.startswith("/"):
            raise ValueError("path 는 절대 경로여야 한다")
        norm = posixpath.normpath(path)
        if norm.startswith("//"):  # normpath 는 선행 // 를 유지한다
            norm = "/" + norm.lstrip("/")
        return self._emit("observe", "file", norm, None, {"path": norm, "mode": mode})


def audited(log: AuditLog, name: str | None = None) -> Callable[[F], F]:
    def deco(fn: F) -> F:
        if inspect.iscoroutinefunction(fn):
            raise TypeError("audited: async 함수는 아직 지원하지 않는다")
        tool_name = name or fn.__name__
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*a: Any, **kw: Any) -> Any:
            try:
                bound = sig.bind(*a, **kw)
                args = dict(bound.arguments)
            except TypeError:
                args = {"args": list(a), "kwargs": dict(kw)}
            call_id = log.call(tool_name, args)  # 실패하면 본문을 실행하지 않는다
            try:
                value = fn(*a, **kw)
            except BaseException as exc:
                log.error(call_id, exc)
                raise
            log.result(call_id, value)
            return value

        return wrapper  # type: ignore[return-value]

    return deco


def read_jsonl(path: str | Path) -> list[AuditEvent]:
    events: list[AuditEvent] = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                events.append(AuditEvent.from_json(line))
            except AuditFormatError as exc:
                raise AuditFormatError(f"{lineno}번째 줄: {exc}") from exc
    return events
