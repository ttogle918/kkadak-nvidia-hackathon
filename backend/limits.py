"""요청 제한·일일 상한 기반(D24 ③④, sprint-4 §6.2). 전부 프로세스 메모리 — 재시작하면 초기화된다(소프트 상한)."""

from __future__ import annotations

import ipaddress
import math
import threading
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Literal

KST = timezone(timedelta(hours=9))
Scope = Literal["ip", "session", "global"]


@dataclass(frozen=True)
class Rule:
    name: str
    limit: int
    window_s: int
    scope: Scope


_MIN, _HOUR, _DAY = 60, 3600, 86400

# 숫자는 보수적 시작값이다(§6.2). 조정은 이 표 한 곳만 바꾼다.
RULES: dict[str, tuple[Rule, ...]] = {
    "session_create": (
        Rule("ip_hour", 10, _HOUR, "ip"),
        Rule("global_hour", 600, _HOUR, "global"),
    ),
    "messages": (
        Rule("ip_min", 5, _MIN, "ip"),
        Rule("ip_day", 40, _DAY, "ip"),
        Rule("session_min", 3, _MIN, "session"),
        Rule("session_day", 30, _DAY, "session"),
        Rule("global_min", 30, _MIN, "global"),
    ),
    "events": (
        Rule("ip_min", 20, _MIN, "ip"),
        Rule("session_min", 20, _MIN, "session"),
        Rule("global_min", 120, _MIN, "global"),
    ),
    "read": (
        Rule("ip_min", 60, _MIN, "ip"),
        Rule("global_min", 600, _MIN, "global"),
    ),
}


def kst_today() -> date:
    return datetime.now(KST).date()


class RateLimiter:
    """고정 창 카운터. 한 요청이 어느 규칙에든 걸리면 아무 카운터도 올리지 않고 Retry-After(초)를 돌려준다."""

    def __init__(self, *, clock: Callable[[], float] = time.time):
        self._clock = clock
        self._lock = threading.Lock()
        self._counts: dict[tuple[str, str, str], tuple[int, int]] = {}  # key -> (창 번호, 횟수)
        self._calls = 0

    def hit(self, bucket: str, keys: Mapping[str, str | None], rules: Iterable[Rule]) -> int | None:
        """허용이면 None, 제한이면 다음 창까지 남은 초(>=1)."""
        now = self._clock()
        with self._lock:
            self._calls += 1
            if self._calls % 1000 == 0:
                self._sweep(now)
            todo: list[tuple[tuple[str, str, str], int]] = []
            wait = 0
            for r in rules:
                k = keys.get(r.scope)
                if k is None:
                    continue  # 키를 알 수 없는 scope(예: hops 미설정의 ip)는 건너뛴다
                idx = int(now // r.window_s)
                ck = (bucket, r.name, k)
                prev = self._counts.get(ck)
                count = prev[1] if prev and prev[0] == idx else 0
                if count >= r.limit:
                    wait = max(wait, math.ceil((idx + 1) * r.window_s - now))
                todo.append((ck, idx))
            if wait:
                return max(1, wait)
            for ck, idx in todo:
                prev = self._counts.get(ck)
                self._counts[ck] = (idx, (prev[1] if prev and prev[0] == idx else 0) + 1)
            return None

    def _sweep(self, now: float) -> None:
        windows = {(b, r.name): r.window_s for b, rs in RULES.items() for r in rs}
        for ck in list(self._counts):
            w = windows.get((ck[0], ck[1]))
            if w is None or self._counts[ck][0] < int(now // w):
                del self._counts[ck]


class DailyBudget:
    """하루(KST) 단위 소프트 상한. 날짜가 바뀌면 0 으로 돌아간다."""

    def __init__(self, units: int, *, today: Callable[[], date] = kst_today):
        self._units = units
        self._today = today
        self._lock = threading.Lock()
        self._day = today()
        self.used = 0

    def _roll(self) -> None:
        d = self._today()
        if d != self._day:
            self._day, self.used = d, 0

    def reserve(self, n: int) -> bool:
        with self._lock:
            self._roll()
            if n < 0 or self.used + n > self._units:
                return False
            self.used += n
            return True

    def refund(self, n: int) -> None:
        with self._lock:
            self._roll()
            self.used = max(0, self.used - max(0, n))


class AdminGuard:
    """관리자 토큰 실패 5회 -> 15분 차단(로컬 모드 전용, T412 가 쓴다). ip 가 None 이면 키는 "unknown" 하나."""

    def __init__(self, *, max_fails: int = 5, block_s: float = 900, clock: Callable[[], float] = time.monotonic):
        self._max, self._block, self._clock = max_fails, block_s, clock
        self._lock = threading.Lock()
        self._fails: dict[str, int] = {}
        self._until: dict[str, float] = {}

    @staticmethod
    def _key(ip: str | None) -> str:
        return ip or "unknown"

    def blocked(self, ip: str | None) -> bool:
        k = self._key(ip)
        with self._lock:
            until = self._until.get(k)
            if until is None:
                return False
            if self._clock() >= until:
                del self._until[k]
                self._fails.pop(k, None)
                return False
            return True

    def fail(self, ip: str | None) -> None:
        k = self._key(ip)
        with self._lock:
            self._fails[k] = self._fails.get(k, 0) + 1
            if self._fails[k] >= self._max:
                self._until[k] = self._clock() + self._block

    def ok(self, ip: str | None) -> None:
        k = self._key(ip)
        with self._lock:
            self._fails.pop(k, None)


def client_ip(request, trusted_hops: int | None) -> str | None:
    """XFF 를 오른쪽에서 hops 번째로 읽는다. hops 없음·짧은 XFF·IP 형식 아님 -> None(IP 제한 끔, D24 ④)."""
    if not trusted_hops:
        return None
    raw = request.headers.get("x-forwarded-for", "")
    parts = [p.strip() for p in raw.split(",")]
    if not raw.strip() or len(parts) < trusted_hops:
        return None
    try:
        return str(ipaddress.ip_address(parts[-trusted_hops]))
    except ValueError:
        return None


def classify(path: str, method: str) -> str | None:
    """요청이 속한 제한 묶음. 닫힌 API(관리자·제보·승인)와 제한 대상 아닌 요청은 None."""
    m = method.upper()
    if m not in ("GET", "POST"):
        return None
    if path == "/api/session":
        return "session_create" if m == "POST" else None
    if path == "/api/messages":
        return "messages" if m == "POST" else "read"
    if path.startswith(("/api/admin", "/api/reports")):
        return None
    if path == "/api/events" or path.startswith("/api/events/"):
        return "events"
    if m == "POST":
        return None
    if path.startswith("/api/"):
        return "read"
    return None
