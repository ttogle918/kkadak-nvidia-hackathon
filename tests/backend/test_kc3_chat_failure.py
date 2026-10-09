"""T310 — 일정 흐름 실패 시 고정 문구(D15 ⑤, sprint-3 §6.5 #3~#8). run_story 는 monkeypatch, LLM 은 부르면 실패."""

import asyncio

import pytest

from backend import chat
from backend.chat import (
    NO_SCHEDULE_REPLY,
    SCHEDULE_UNAVAILABLE_REPLY,
    ChatService,
)
from backend.settings import Settings
from backend.story_runner import LLM_BUDGET_S, TIMEOUT_S, StoryRunnerError
from core.llm import TransportResponse

SCHED = "10/15 10시에 창덕궁, 2시부터 5시까지 익선동, 숙소는 종로3가"
KEY = {"NVIDIA_API_KEY": "nvapi-" + "s" * 24}


class ForbiddenTransport:
    """호출되면 실패 — 일반 챗봇(LLM)이 불리지 않았음을 단언한다."""

    def __init__(self):
        self.calls = 0

    async def send(self, **kw):
        self.calls += 1
        raise AssertionError("일반 챗봇이 불렸다")


class OkTransport:
    def __init__(self):
        self.calls = []

    async def send(self, **kw):
        self.calls.append(kw)
        return TransportResponse(200, "일반 답이에요.")


def _bundle(n=0, problems=()):
    anchors = [{"type": "visit", "name": f"곳{i}", "day": 1, "lat": None, "lng": None,
                "from": f"2026-10-15T{9 + i:02d}:00", "to": None, "source_quote": "q"} for i in range(n)]
    return {"schema": "kc-chat-bundle/v1", "trip": {"from": "2026-10-15", "to": "2026-10-16"},
            "itinerary": {"anchors": anchors, "free_slots": []},
            "mentions": {"anchors": [{"anchor": a, "mentions": [], "reason": "ok"} for a in anchors]},
            "cards": [], "problems": [{"code": c, "message": "m"} for c in problems]}


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def _yaml(tmp_path, timeout_s):
    f = tmp_path / "llm.yaml"
    f.write_text(
        "providers:\n"
        f"  nvidia: {{api_key_envs: [NVIDIA_API_KEY], base_url: \"https://x.invalid/v1\", "
        f"max_concurrency: 2, timeout_s: {timeout_s}}}\n"
        "features:\n  chat: {provider: nvidia, model: \"m\"}\n", encoding="utf-8")
    return f


@pytest.fixture
def svc(tmp_path, monkeypatch):
    db = tmp_path / "idx.db"
    db.write_bytes(b"")
    clock = Clock()
    seen = {}

    def build(story, *, transport=None, timeout_s=40, elapsed=0.0, with_db=True):
        def fake_story(text, trip, dbp, **kw):
            seen["kw"] = kw
            clock.now += elapsed
            if isinstance(story, Exception):
                raise story
            return story

        monkeypatch.setattr("backend.chat.run_story", fake_story)
        s = Settings(hitl_db=tmp_path / "h.db", audit_dir=tmp_path / "audit", output_dir=tmp_path / "o",
                     reviewer_id="human:t", index_db=db if with_db else tmp_path / "none.db")
        t = transport or ForbiddenTransport()
        return (ChatService(s, transport=t, clock=clock, env=dict(KEY),
                            config_path=_yaml(tmp_path, timeout_s)), t, s, seen)

    return build


def _send(service, text=SCHED):
    return asyncio.run(service.send(text, None))


def _audit(s):
    return "".join(p.read_text(encoding="utf-8") for p in s.audit_dir.glob("*.jsonl"))


def test_budget_constants_match_spec():
    assert TIMEOUT_S == 90 and LLM_BUDGET_S == 75 and chat.FRONT_LIMIT_S == 100


def test_pipeline_receives_llm_budget(svc):
    service, _, _, seen = svc(_bundle(n=0, problems=["LLM_FAILED"]))
    _send(service)
    assert seen["kw"] == {"llm_budget_s": 75}


@pytest.mark.parametrize("code", ["LLM_FAILED", "LLM_EMPTY", "LLM_BAD_JSON", "LLM_UNEXPECTED_SHAPE"])
def test_row4_llm_failure_gives_fixed_reply_without_chat(svc, code):
    service, t, s, _ = svc(_bundle(n=0, problems=[code]))
    res = _send(service)
    assert res.reply["text"] == SCHEDULE_UNAVAILABLE_REPLY and res.bundle is None and t.calls == 0
    log = _audit(s)
    assert "llm_failed" in log and "창덕궁" not in log and "익선동" not in log


def test_row5_llm_unavailable_gives_fixed_reply_without_chat(svc):
    service, t, s, _ = svc(_bundle(n=0, problems=["LLM_UNAVAILABLE"]))
    res = _send(service)
    assert res.reply["text"] == SCHEDULE_UNAVAILABLE_REPLY and t.calls == 0
    assert "llm_unavailable" in _audit(s)


@pytest.mark.parametrize("kind", ["timeout", "exit", "no_output", "bad_json", "bad_schema", "too_large", "spawn"])
def test_row6_runner_failure_gives_fixed_reply_without_chat(svc, kind):
    service, t, s, _ = svc(StoryRunnerError(kind))
    res = _send(service)
    assert res.reply["text"] == SCHEDULE_UNAVAILABLE_REPLY and res.bundle is None and t.calls == 0
    assert kind in _audit(s)


def test_row6_bad_bundle_shape_gives_fixed_reply(svc):
    service, t, s, _ = svc({"schema": "kc-chat-bundle/v1", "itinerary": 1})
    res = _send(service)
    assert res.reply["text"] == SCHEDULE_UNAVAILABLE_REPLY and t.calls == 0 and "bad_shape" in _audit(s)


def test_fixed_reply_and_user_text_stay_out_of_llm_context(svc):
    service, _, _, _ = svc(_bundle(n=0, problems=["LLM_FAILED"]))
    _send(service)
    assert service._context() == []
    assert [m["role"] for m in service.messages()] == ["user", "agent"]  # 화면 기록에는 남는다


def test_row3_not_a_schedule_with_budget_goes_to_chat(svc):
    service, t, _, _ = svc(_bundle(n=0), transport=OkTransport(), timeout_s=40, elapsed=55)  # 55+40 <= 95
    res = _send(service)
    assert len(t.calls) == 1 and "일반 답이에요." in res.reply["text"]


def test_row3_no_budget_gives_no_schedule_reply_without_chat(svc):
    service, t, s, _ = svc(_bundle(n=0), timeout_s=40, elapsed=56)  # 56+40 > 95
    res = _send(service)
    assert res.reply["text"] == NO_SCHEDULE_REPLY and t.calls == 0 and "no_budget" in _audit(s)
    assert service._context() == []


def test_row7_injection_blocked_problem_is_not_llm_failure(svc):
    service, t, _, _ = svc(_bundle(n=0, problems=["INJECTION_BLOCKED"]), transport=OkTransport())
    res = _send(service)
    assert len(t.calls) == 1 and res.reply["text"] != SCHEDULE_UNAVAILABLE_REPLY


def test_row8_missing_index_still_falls_back_to_chat(svc):
    service, t, _, _ = svc(_bundle(n=0, problems=["LLM_FAILED"]), transport=OkTransport(), with_db=False)
    res = _send(service)
    assert len(t.calls) == 1 and res.reply["text"] != SCHEDULE_UNAVAILABLE_REPLY


def test_llm_timeout_read_from_config_with_default(svc, tmp_path):
    service, *_ = svc(_bundle(n=0), timeout_s=40)
    assert service._llm_timeout_s() == 40
    service._config_path = tmp_path / "missing.yaml"
    assert service._llm_timeout_s() == 40  # 한 번만 읽어 저장한다(요청마다 다시 읽지 않는다)
    other, *_ = svc(_bundle(n=0), timeout_s=40)
    other._config_path = tmp_path / "missing.yaml"
    assert other._llm_timeout_s() == chat.DEFAULT_LLM_TIMEOUT_S


def test_llm_timeout_readable_without_api_key(svc):
    service, *_ = svc(_bundle(n=0), timeout_s=40)
    service._env = {}  # 키 없음
    assert service._llm_timeout_s() == 40


def test_cache_hit_adds_fixed_reused_note_only_for_cache(svc, monkeypatch):
    monkeypatch.setattr(ChatService, "_search_events",
                        lambda self, a: {"events": [], "excluded": [], "problems": [], "coverage": {}})
    hit = {**_bundle(n=1), "schedule": {"source": "cache", "attempts": 0}}
    service, *_ = svc(hit)
    text = _send(service).reply["text"]
    assert text["ko"].endswith(chat.CACHE_REUSED_NOTE["ko"] + ".")
    assert text["en"].endswith(chat.CACHE_REUSED_NOTE["en"] + ".")
    assert chat.CACHE_REUSED_NOTE == {"ko": "이전 결과 재사용", "en": "Reused a previous result"}
    for sched in ({"source": "llm", "attempts": 1}, None):
        b = _bundle(n=1)
        if sched:
            b["schedule"] = sched
        service, *_ = svc(b)
        text = _send(service).reply["text"]
        assert chat.CACHE_REUSED_NOTE["ko"] not in text["ko"]
        assert chat.CACHE_REUSED_NOTE["en"] not in text["en"]


def test_row2_normal_bundle_unchanged(svc, monkeypatch):
    monkeypatch.setattr(ChatService, "_search_events",
                        lambda self, a: {"events": [], "excluded": [], "problems": [], "coverage": {}})
    service, t, _, _ = svc(_bundle(n=2))
    res = _send(service)
    assert res.bundle is not None and res.bundle["status"] == "ok" and t.calls == 0
