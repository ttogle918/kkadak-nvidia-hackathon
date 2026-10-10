from types import SimpleNamespace

import pytest

from backend.session import (
    LOCAL_SESSION_ID,
    TOKEN_RE,
    SessionStore,
    session_from_request,
    token_tag,
)


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def _store(clock=None, ttl=100, mx=3):
    return SessionStore(ttl_s=ttl, max_sessions=mx, clock=clock or Clock())


def test_create_token_format_and_get():
    st = _store()
    s = st.create()
    assert TOKEN_RE.match(s.id) and len(s.id) == 43
    assert st.get(s.id) is s
    assert len(st) == 1


@pytest.mark.parametrize("bad", [None, "", "short", "a" * 42, "a" * 44, "a" * 42 + "!", "local"])
def test_bad_format_is_none(bad):
    assert _store().get(bad) is None


def test_ttl_expiry_and_touch():
    c = Clock()
    st = _store(c)
    a = st.create()
    c.t += 90
    assert st.get(a.id) is a  # touch
    c.t += 90
    assert st.get(a.id) is a
    c.t += 101
    assert st.get(a.id) is None
    assert len(st) == 0


def test_max_evicts_least_recently_used():
    c = Clock()
    st = _store(c, mx=2)
    a = st.create()
    b = st.create()
    c.t += 1
    st.get(a.id)  # a 를 최근으로
    d = st.create()
    assert st.get(b.id) is None
    assert st.get(a.id) is a and st.get(d.id) is d
    assert len(st) == 2


def test_local_is_stable_and_not_counted():
    st = _store()
    assert st.local() is st.local() and st.local().id == LOCAL_SESSION_ID
    assert len(st) == 0


def test_history_and_log_bounds():
    s = _store().create()
    for i in range(150):
        s.history.append(({"i": i}, True))
    for i in range(300):
        s.logs.append(i)
    assert len(s.history) == 100 and len(s.logs) == 200


def _req(store, public, header=None):
    h = {"X-KC-Session": header} if header else {}
    app = SimpleNamespace(state=SimpleNamespace(sessions=store, settings=SimpleNamespace(public_mode=public)))
    return SimpleNamespace(app=app, headers={k.lower(): v for k, v in h.items()}
                           if False else _Headers(h))


class _Headers:
    def __init__(self, d):
        self.d = {k.lower(): v for k, v in d.items()}

    def get(self, k, default=None):
        return self.d.get(k.lower(), default)


def test_session_from_request_modes():
    st = _store()
    s = st.create()
    assert session_from_request(_req(st, True, s.id)) is s
    assert session_from_request(_req(st, True)) is None
    assert session_from_request(_req(st, True, "x" * 43)) is None
    assert session_from_request(_req(st, False, s.id)) is s
    assert session_from_request(_req(st, False)) is st.local()
    assert session_from_request(_req(st, False, "bad")) is st.local()


def test_token_tag_hides_token():
    t = "A" * 43
    assert len(token_tag(t)) == 8 and t not in token_tag(t)
