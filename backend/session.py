"""방문자 세션(D24 ①). 프로세스 메모리에만 두고, 토큰은 로그에 남기지 않는다. core 만 import 한다(D3·D10)."""

from __future__ import annotations

import hashlib
import re
import secrets
import threading
import time
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
SESSION_HEADER = "X-KC-Session"
LOCAL_SESSION_ID = "local"


def token_tag(token: str) -> str:
    """로그에 쓸 수 있는 토큰 꼬리표(sha256 앞 8자). 토큰 자체는 로그에 남기지 않는다."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:8]


@dataclass
class Session:
    id: str
    created: float
    last_seen: float
    history: deque = field(default_factory=lambda: deque(maxlen=100))  # (message dict, in_llm_context: bool)
    logs: deque = field(default_factory=lambda: deque(maxlen=200))
    seq: int = 0
    busy: threading.Lock = field(default_factory=threading.Lock)
    lock: threading.Lock = field(default_factory=threading.Lock)
    tourapi_calls: int = 0  # D29 ⑤ 세션당 하루 10회(T434 가 사용)
    tourapi_day: date | None = None


class SessionStore:
    def __init__(self, *, ttl_s: float, max_sessions: int, clock: Callable[[], float] = time.monotonic):
        if ttl_s <= 0 or max_sessions < 1:
            raise ValueError("ttl_s 와 max_sessions 는 양수여야 한다")
        self._ttl = ttl_s
        self._max = max_sessions
        self._clock = clock
        self._lock = threading.Lock()
        self._items: OrderedDict[str, Session] = OrderedDict()  # 오래 안 쓴 순서(앞이 가장 오래됨)
        now = clock()
        self._local = Session(LOCAL_SESSION_ID, now, now)

    def _expire(self, now: float) -> None:
        while self._items:
            token, s = next(iter(self._items.items()))
            if now - s.last_seen <= self._ttl:
                break
            del self._items[token]

    def create(self) -> Session | None:
        """새 세션. 상한이면 가장 오래 안 쓴 세션을 지우고 만든다(D24 ①). 항상 만들어지지만 계약상 None 도 허용한다."""
        with self._lock:
            now = self._clock()
            self._expire(now)
            while len(self._items) >= self._max:
                self._items.popitem(last=False)
            token = secrets.token_urlsafe(32)
            s = Session(token, now, now)
            self._items[token] = s
            return s

    def get(self, token: str | None) -> Session | None:
        if not isinstance(token, str) or not TOKEN_RE.match(token):
            return None
        with self._lock:
            now = self._clock()
            self._expire(now)
            s = self._items.get(token)
            if s is None:
                return None
            s.last_seen = now
            self._items.move_to_end(token)
            return s

    def local(self) -> Session:
        return self._local

    @property
    def ttl_s(self) -> float:
        return self._ttl

    def __len__(self) -> int:
        with self._lock:
            self._expire(self._clock())
            return len(self._items)


def session_from_request(request) -> Session | None:
    """공개 모드: 헤더 -> store.get (없으면 None). 로컬 모드: 유효하면 그 세션, 아니면 공용 `local`."""
    store: SessionStore = request.app.state.sessions
    found = store.get(request.headers.get(SESSION_HEADER))
    if found is not None:
        return found
    if request.app.state.settings.public_mode:
        return None
    return store.local()
