import pytest

from core.llm import KeyPool, LlmUnavailable


class Clock:
    def __init__(self):
        self.t = 100.0
        self.sleeps = []

    def __call__(self):
        return self.t

    async def sleep(self, s):
        self.sleeps.append(s)
        self.t += s


def _pool(clock, n=3, cooldown=10.0, timeout=30.0):
    keys = [(f"K{i}", "v" + str(i)) for i in range(n)]
    return KeyPool(keys, cooldown_s=cooldown, timeout_s=timeout, clock=clock, sleep=clock.sleep)


async def test_round_robin_order():
    p = _pool(Clock())
    got = [(await p.acquire()).name for _ in range(7)]
    assert got == ["K0", "K1", "K2", "K0", "K1", "K2", "K0"]


async def test_cooldown_skips_and_returns():
    c = Clock()
    p = _pool(c)
    assert (await p.acquire()).name == "K0"
    p.cool_down("K1")
    assert [(await p.acquire()).name for _ in range(3)] == ["K2", "K0", "K2"]
    c.t += 10.0  # 쿨다운 끝
    names = {(await p.acquire()).name for _ in range(3)}
    assert "K1" in names


async def test_all_cooling_waits_for_earliest():
    c = Clock()
    p = _pool(c, n=2, cooldown=10.0, timeout=30.0)
    p.cool_down("K0")
    c.t += 3
    p.cool_down("K1")
    lease = await p.acquire()
    assert lease.name == "K0"  # 먼저 풀리는 키
    assert c.sleeps == [7.0]


async def test_all_cooling_beyond_timeout_raises():
    c = Clock()
    p = _pool(c, n=2, cooldown=100.0, timeout=5.0)
    p.cool_down("K0")
    p.cool_down("K1")
    with pytest.raises(LlmUnavailable):
        await p.acquire()
    assert c.sleeps == []


async def test_cool_down_keeps_later_deadline_and_unknown_name():
    c = Clock()
    p = _pool(c, n=1, cooldown=10.0, timeout=1000.0)
    p.cool_down("K0", 50)
    p.cool_down("K0", 5)
    await p.acquire()
    assert c.sleeps == [50.0]
    with pytest.raises(KeyError):
        p.cool_down("nope")


def test_lease_repr_hides_value_and_empty_pool_rejected():
    c = Clock()
    p = _pool(c, n=1)
    import asyncio

    lease = asyncio.run(p.acquire())
    assert "v0" not in repr(lease)
    with pytest.raises(ValueError):
        KeyPool([], cooldown_s=1, timeout_s=1)
    with pytest.raises(ValueError):
        KeyPool([("a", "1"), ("a", "2")], cooldown_s=1, timeout_s=1)
