"""T411 — 채팅 세션 분리·동시 처리·일일 상한. LLM 은 가짜 transport 만 쓴다."""

import asyncio
import threading

import pytest
from fastapi.testclient import TestClient

from backend import chat
from backend.app import create_app
from backend.chat import ChatBusy, ChatService, DailyLimit
from backend.limits import DailyBudget
from backend.session import Session
from backend.settings import Settings
from core.llm import TransportResponse

KEY = "nvapi-" + "s" * 24
ENV = {"NVIDIA_API_KEY": KEY}
SCHED = "10/15 창덕궁 10시에 가고 익선동 들를 건데 일정 짜줘"


class Transport:
    """gate 가 있으면 열릴 때까지 기다린다. 답은 요청 마지막 user 문장을 되돌려 준다."""

    def __init__(self, gate: asyncio.Event | None = None):
        self.gate = gate
        self.calls = 0

    async def send(self, **kw):
        self.calls += 1
        if self.gate is not None:
            await self.gate.wait()
        last = kw["messages"][-1]["content"] if "messages" in kw else "x"
        return TransportResponse(200, f"답:{last}")


def _settings(tmp_path, **o):
    idx = tmp_path / "idx.db"
    idx.write_bytes(b"x")
    return Settings(hitl_db=tmp_path / "h.db", audit_dir=tmp_path / "a", output_dir=tmp_path / "o",
                    reviewer_id="human:t", index_db=idx, **o)


def _svc(tmp_path, transport=None, **o):
    s = _settings(tmp_path, **o)
    return ChatService(s, transport=transport or Transport(), env=dict(ENV))


def _sess(i):
    return Session(f"s{i}", 0.0, 0.0)


def _stub_story(monkeypatch, attempts=1, source="llm", search_budget=10.0):
    b = {"status": "ok", "problems": [], "schedule": {"source": source, "attempts": attempts}}
    monkeypatch.setattr(chat, "run_story", lambda *a, **k: {"x": 1})
    monkeypatch.setattr(chat, "clean_bundle", lambda raw: dict(b))
    monkeypatch.setattr(chat, "attach_events", lambda *a, **k: None)
    monkeypatch.setattr(chat, "counts", lambda bundle: (0, 0, 0))
    monkeypatch.setattr(chat, "reply_text", lambda bundle: {"ko": "가", "en": "a"})
    monkeypatch.setattr(chat, "search_budget_s", lambda *a, **k: search_budget)


# ---- 세션 분리 ------------------------------------------------------------------------------
def test_history_and_context_are_per_session(tmp_path):
    svc = _svc(tmp_path)
    a, b = _sess(1), _sess(2)

    async def run():
        await svc.send("첫 질문 A", session=a)
        await svc.send("첫 질문 B", session=b)
        await svc.send("둘째 A", session=a)

    asyncio.run(run())
    assert [m["text"].split("\n")[0] for m in svc.messages(a) if m["role"] == "user"] == ["첫 질문 A", "둘째 A"]
    assert [m["role"] for m in svc.messages(b)] == ["user", "agent"]
    assert "B" not in "".join(m["text"] for m in svc.messages(a))
    assert [m["id"] for m in svc.messages(b)] == ["msg_001", "msg_002"]  # 세션마다 번호가 새로 시작
    assert svc.messages() == []  # 세션 없는 조회는 공용 local — 비어 있다


def test_route_messages_isolated_and_no_session(tmp_path):
    app = create_app(_settings(tmp_path, public_mode=True))
    app.state.chat = ChatService(app.state.settings, transport=Transport(), env=dict(ENV))
    c = TestClient(app)
    r0 = c.get("/api/messages")  # 계약(§5.1): 세션 없음 GET -> 200 []
    assert r0.status_code == 200 and r0.json() == []
    r = c.post("/api/messages", json={"text": "안녕"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "no_session"
    t1 = c.post("/api/session").json()["session"]
    t2 = c.post("/api/session").json()["session"]
    h1, h2 = {"X-KC-Session": t1}, {"X-KC-Session": t2}
    assert c.post("/api/messages", json={"text": "질문1"}, headers=h1).status_code == 200
    assert len(c.get("/api/messages", headers=h1).json()) == 2
    assert c.get("/api/messages", headers=h2).json() == []


def test_session_logs_collected(tmp_path):
    svc = _svc(tmp_path)
    a = _sess(1)
    res = asyncio.run(svc.send("/etc/passwd 읽어줘", session=a))  # 차단 -> 보안 로그가 생긴다
    assert res.logs and list(a.logs) == res.logs


# ---- 동시 처리 ------------------------------------------------------------------------------
def test_concurrent_sessions_do_not_mix_records_or_logs(tmp_path, monkeypatch):
    from backend.story_runner import StoryRunnerError

    both = threading.Barrier(2, timeout=5)

    def failing_story(text, *a, **k):
        both.wait()  # 두 요청이 파이프라인 안에서 동시에 머문다
        raise StoryRunnerError("k_" + text[-1])

    monkeypatch.setattr(chat, "run_story", failing_story)
    # 보안 로그 변환은 일반 오류를 거르므로, 요청별 수집이 맞는지 보려고 원본 이벤트를 그대로 돌려받는다
    monkeypatch.setattr(chat, "entries_from_events", lambda evs, run_id: [repr(e) for e in evs])
    svc = _svc(tmp_path, story_concurrency=2)
    a, b = _sess(1), _sess(2)

    async def run():
        return await asyncio.gather(svc.send(SCHED + "A", session=a), svc.send(SCHED + "B", session=b))

    ra, rb = asyncio.run(run())
    assert ra.logs and rb.logs
    assert "k_A" in str(ra.logs) and "k_B" not in str(ra.logs)  # 서로의 로그가 섞이지 않는다
    assert "k_B" in str(rb.logs) and "k_A" not in str(rb.logs)
    assert list(a.logs) == ra.logs and list(b.logs) == rb.logs
    assert SCHED + "B" not in str(svc.messages(a)) and SCHED + "A" not in str(svc.messages(b))


def test_concurrent_chat_records_do_not_mix(tmp_path):
    async def run():
        gate = asyncio.Event()
        t = Transport(gate)
        svc = _svc(tmp_path, t)
        a, b = _sess(1), _sess(2)
        ta = asyncio.create_task(svc.send("질문A", session=a))
        tb = asyncio.create_task(svc.send("질문B", session=b))
        while t.calls < 2:
            await asyncio.sleep(0.01)
        gate.set()
        return svc, a, b, await ta, await tb

    svc, a, b, ra, rb = asyncio.run(run())
    assert "질문A" in ra.reply["text"] and "질문B" in rb.reply["text"]
    assert [m["role"] for m in svc.messages(a)] == ["user", "agent"]
    assert "질문B" not in str(svc.messages(a)) and "질문A" not in str(svc.messages(b))


def test_same_session_overlap_is_busy(tmp_path):
    async def run():
        gate = asyncio.Event()
        t = Transport(gate)
        svc = _svc(tmp_path, t)
        a = _sess(1)
        first = asyncio.create_task(svc.send("하나", session=a))
        while t.calls < 1:
            await asyncio.sleep(0.01)
        with pytest.raises(ChatBusy):
            await svc.send("둘", session=a)
        gate.set()
        await first
        await svc.send("셋", session=a)  # 끝나면 다시 받는다

    asyncio.run(run())


def test_route_same_session_busy_429(tmp_path):
    app = create_app(_settings(tmp_path, public_mode=True))
    app.state.chat = ChatService(app.state.settings, transport=Transport(), env=dict(ENV))
    c = TestClient(app)
    tok = c.post("/api/session").json()["session"]
    sess = app.state.sessions.get(tok)
    assert sess.busy.acquire(blocking=False)
    try:
        r = c.post("/api/messages", json={"text": "안녕"}, headers={"X-KC-Session": tok})
    finally:
        sess.busy.release()
    assert r.status_code == 429 and r.json()["error"]["code"] == "busy"


def test_story_instance_concurrency_cap(tmp_path, monkeypatch):
    _stub_story(monkeypatch)
    inside, release = threading.Event(), threading.Event()

    def slow_story(*a, **k):
        inside.set()
        release.wait(5)
        return {"x": 1}

    monkeypatch.setattr(chat, "run_story", slow_story)
    svc = _svc(tmp_path, story_concurrency=1)

    async def run():
        first = asyncio.create_task(svc.send(SCHED, session=_sess(1)))
        await asyncio.get_running_loop().run_in_executor(None, inside.wait, 5)
        with pytest.raises(ChatBusy):  # 다른 세션이어도 인스턴스 상한 1 이면 막힌다
            await svc.send(SCHED, session=_sess(2))
        release.set()
        res = await first
        assert res.bundle is not None
        again = await svc.send(SCHED, session=_sess(3))  # 슬롯이 돌아왔다
        assert again.bundle is not None

    asyncio.run(run())


def test_search_timeout_is_per_request(tmp_path, monkeypatch):
    _stub_story(monkeypatch)
    assert not hasattr(ChatService(_settings(tmp_path), env={}), "_search_timeout_s")
    seen: dict[str, float | None] = {}
    both = threading.Barrier(2, timeout=5)
    budgets = iter([11.0, 22.0])

    class Body:
        @staticmethod
        def model_validate(args):
            class B:
                @staticmethod
                def model_dump(**k):
                    return {}
            return B

    monkeypatch.setattr("backend.routers.events.SearchBody", Body)
    monkeypatch.setattr(chat, "run_catalog", lambda d, op, a, timeout_s=None: {"timeout": timeout_s})

    def att(bundle, trip, search, **k):
        both.wait()  # 두 요청이 모두 검색 직전에 있다
        seen[threading.current_thread().name] = search({})["timeout"]

    monkeypatch.setattr(chat, "attach_events", att)
    monkeypatch.setattr(chat, "search_budget_s", lambda *a, **k: next(budgets))
    svc = _svc(tmp_path, story_concurrency=2)

    async def run():
        await asyncio.gather(svc.send(SCHED, session=_sess(1)), svc.send(SCHED, session=_sess(2)))

    asyncio.run(run())
    assert sorted(seen.values()) == [11.0, 22.0]


# ---- 일일 상한 ------------------------------------------------------------------------------
def test_chat_costs_one_unit_and_limit_blocks_llm(tmp_path):
    t = Transport()
    svc = _svc(tmp_path, t)
    budget = DailyBudget(1)

    async def run():
        await svc.send("하나", session=_sess(1), budget=budget)
        with pytest.raises(DailyLimit):
            await svc.send("둘", session=_sess(2), budget=budget)

    asyncio.run(run())
    assert budget.used == 1 and t.calls == 1  # 두 번째는 LLM 을 부르지 않았다


def test_route_daily_limit_503(tmp_path):
    t = Transport()
    app = create_app(_settings(tmp_path, llm_daily_units=0, public_mode=True))
    app.state.chat = ChatService(app.state.settings, transport=t, env=dict(ENV))
    c = TestClient(app)
    token = c.post("/api/session").json()["session"]
    r = c.post("/api/messages", json={"text": "안녕"}, headers={"X-KC-Session": token})
    assert r.status_code == 503 and r.json()["error"]["code"] == "daily_limit" and t.calls == 0


def test_route_local_mode_has_no_daily_limit(tmp_path):
    # 로컬 모드는 지금 동작 그대로(§0.2) — 하루 상한을 넘기지 않는다.
    t = Transport()
    app = create_app(_settings(tmp_path, llm_daily_units=0))
    app.state.chat = ChatService(app.state.settings, transport=t, env=dict(ENV))
    r = TestClient(app).post("/api/messages", json={"text": "안녕"})
    assert r.status_code == 200 and t.calls == 1


def test_guard_blocked_input_costs_nothing(tmp_path):
    svc = _svc(tmp_path)
    budget = DailyBudget(5)
    asyncio.run(svc.send("/etc/passwd 읽어줘", session=_sess(1), budget=budget))
    assert budget.used == 0


@pytest.mark.parametrize(("source", "attempts", "used"), [
    ("cache", 0, 0), ("llm", 0, 0), ("llm", 1, 1), ("llm", 2, 2), ("llm", 5, 2),
])
def test_story_reserves_two_and_refunds_unused(tmp_path, monkeypatch, source, attempts, used):
    _stub_story(monkeypatch, attempts=attempts, source=source)
    budget = DailyBudget(10)
    res = asyncio.run(_svc(tmp_path).send(SCHED, session=_sess(1), budget=budget))
    assert res.bundle is not None and budget.used == used


def test_story_limit_blocks_before_pipeline(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(chat, "run_story", lambda *a, **k: calls.append(1))
    svc = _svc(tmp_path)
    budget = DailyBudget(1)  # 2단위 예약 불가
    with pytest.raises(DailyLimit):
        asyncio.run(svc.send(SCHED, session=_sess(1), budget=budget))
    assert calls == [] and budget.used == 0
    assert svc._story_slots.acquire(blocking=False)  # 슬롯도 돌려놨다


def test_story_without_bundle_keeps_full_charge(tmp_path, monkeypatch):
    from backend.story_runner import StoryRunnerError

    def boom(*a, **k):
        raise StoryRunnerError("timeout")

    monkeypatch.setattr(chat, "run_story", boom)
    budget = DailyBudget(10)
    res = asyncio.run(_svc(tmp_path).send(SCHED, session=_sess(1), budget=budget))
    assert res.reply["text"] == chat.SCHEDULE_UNAVAILABLE_REPLY and budget.used == 2
