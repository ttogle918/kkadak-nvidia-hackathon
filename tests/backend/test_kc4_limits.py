from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from backend.limits import (
    RULES,
    AdminGuard,
    DailyBudget,
    RateLimiter,
    Rule,
    classify,
    client_ip,
)
from backend.settings import Settings


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


def _req(xff=None):
    h = {"x-forwarded-for": xff} if xff is not None else {}
    return SimpleNamespace(headers=h)


R = (Rule("s_min", 2, 60, "session"), Rule("g_min", 5, 60, "global"), Rule("ip_min", 1, 60, "ip"))


def test_window_boundary_and_retry_after():
    c = Clock(1200.0 + 10)  # 창 [1200, 1260)
    lim = RateLimiter(clock=c)
    k = {"ip": None, "session": "s1", "global": "all"}
    assert lim.hit("b", k, R) is None
    assert lim.hit("b", k, R) is None
    wait = lim.hit("b", k, R)
    assert wait == 50
    c.t = 1260.0
    assert lim.hit("b", k, R) is None


def test_denied_request_does_not_count_other_rules():
    lim = RateLimiter(clock=Clock())
    rules = (Rule("a", 1, 60, "session"), Rule("g", 2, 60, "global"))
    assert lim.hit("b", {"session": "x", "global": "all"}, rules) is None
    assert lim.hit("b", {"session": "x", "global": "all"}, rules) is not None  # 세션 한도, 전역은 안 올림
    assert lim.hit("b", {"session": "y", "global": "all"}, rules) is None  # 전역 2번째
    assert lim.hit("b", {"session": "z", "global": "all"}, rules) is not None


def test_ip_rule_skipped_when_ip_unknown_and_global_still_applies():
    lim = RateLimiter(clock=Clock())
    k = {"ip": None, "session": None, "global": "all"}
    for _ in range(5):
        assert lim.hit("b", k, R) is None  # ip(1회)·session 규칙 건너뜀
    assert lim.hit("b", k, R) is not None  # 전역 5회


def test_ip_rule_applies_when_known():
    lim = RateLimiter(clock=Clock())
    k = {"ip": "1.2.3.4", "session": None, "global": "all"}
    assert lim.hit("b", k, R) is None
    assert lim.hit("b", k, R) is not None


def test_sweep_does_not_break():
    c = Clock()
    lim = RateLimiter(clock=c)
    for i in range(1500):
        c.t += 100
        lim.hit("messages", {"ip": f"10.0.{i}.1", "session": None, "global": "all"}, RULES["messages"])
    assert len(lim._counts) < 3000


def test_rules_table_shape():
    assert {r.scope for rs in RULES.values() for r in rs} <= {"ip", "session", "global"}
    assert any(r.scope == "global" for rs in RULES.values() for r in rs)


def test_daily_budget_kst_reset_and_refund_floor():
    day = [date(2026, 10, 10)]
    b = DailyBudget(3, today=lambda: day[0])
    assert b.reserve(2) and b.used == 2
    assert not b.reserve(2) and b.used == 2
    b.refund(5)
    assert b.used == 0  # 하한 0
    assert b.reserve(3)
    day[0] += timedelta(days=1)
    assert b.reserve(3) and b.used == 3


def test_daily_budget_zero_units_blocks_all():
    assert not DailyBudget(0, today=lambda: date(2026, 1, 1)).reserve(1)


@pytest.mark.parametrize("hops,xff,want", [
    (None, "1.1.1.1", None),
    (1, "9.9.9.9, 1.1.1.1", "1.1.1.1"),
    (2, "9.9.9.9, 1.1.1.1", "9.9.9.9"),
    (2, "1.1.1.1", None),  # 짧은 XFF
    (1, None, None),
    (1, "not-an-ip", None),  # 위조 형식
    (1, "1.1.1.1, <script>", None),
    (1, "2001:db8::1", "2001:db8::1"),
])
def test_client_ip(hops, xff, want):
    assert client_ip(_req(xff), hops) == want


def test_classify():
    assert classify("/api/session", "POST") == "session_create"
    assert classify("/api/messages", "POST") == "messages"
    assert classify("/api/messages", "GET") == "read"
    assert classify("/api/events/search", "POST") == "events"
    assert classify("/api/events/coverage", "GET") == "events"
    assert classify("/api/cards", "GET") == "read"
    assert classify("/api/meta", "GET") == "read"
    assert classify("/api/admin/review", "GET") is None
    assert classify("/api/reports", "POST") is None
    assert classify("/api/audit/1/decision", "POST") is None
    assert classify("/api/messages", "OPTIONS") is None
    assert classify("/x", "GET") is None


def test_admin_guard_blocks_after_5():
    c = Clock()
    g = AdminGuard(clock=c)
    for _ in range(4):
        g.fail(None)
    assert not g.blocked(None)
    g.fail(None)
    assert g.blocked(None) and not g.blocked("1.1.1.1")
    c.t += 901
    assert not g.blocked(None)


def _kw(tmp_path, **o):
    return Settings(hitl_db=tmp_path / "h.db", audit_dir=tmp_path, output_dir=tmp_path,
                    reviewer_id="human:t", **o)


def test_settings_defaults_and_env(tmp_path):
    s = _kw(tmp_path)
    assert (s.public_mode, s.trusted_proxy_hops, s.llm_daily_units, s.story_concurrency,
            s.catalog_concurrency, s.session_ttl_s, s.session_max) == (False, None, 300, 2, 2, 7200, 1000)
    e = Settings.from_env({"KC_PUBLIC_MODE": "1", "KC_TRUSTED_PROXY_HOPS": "2", "KC_CATALOG_CONCURRENCY": "3"})
    assert e.public_mode and e.trusted_proxy_hops == 2 and e.catalog_concurrency == 3
    assert Settings.from_env({}).trusted_proxy_hops is None


@pytest.mark.parametrize("env", [
    {"KC_TRUSTED_PROXY_HOPS": "0"}, {"KC_TRUSTED_PROXY_HOPS": "4"}, {"KC_STORY_CONCURRENCY": "9"},
    {"KC_CATALOG_CONCURRENCY": "0"}, {"KC_LLM_DAILY_UNITS": "-1"}, {"KC_SESSION_MAX": "0"},
    {"KC_PUBLIC_MODE": "true"}, {"KC_SESSION_TTL_S": "abc"},
])
def test_settings_out_of_range_fails(env):
    with pytest.raises(ValueError):
        Settings.from_env(env)
