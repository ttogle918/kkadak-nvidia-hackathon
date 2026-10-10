"""T434 — 묶음 `kto_live` 연결(D29): 가짜 TourApiLive 만 쓴다(실호출 0)."""

import asyncio
import copy
import json

import pytest

from backend.chat import ChatService
from backend.chat_story import KTO_MAX_ITEMS, kto_live_block
from backend.session import Session
from backend.settings import Settings
from backend.tourapi_live import LiveResult
from core.llm import TransportResponse

KEY = {"NVIDIA_API_KEY": "nvapi-" + "s" * 24}
SCHED = "10/15 10시에 창덕궁, 2시부터 5시까지 익선동, 숙소는 종로3가"
SECRET = "비밀행사제목-ZZ"


def item(**kw):
    d = {"contentid": "1", "title": SECRET, "addr1": "서울 종로구", "addr2": "1층", "eventstartdate": "20261015",
         "eventenddate": "20261020", "tel": "02-000", "progresstype": "", "lDongSignguCd": "110", "cpyrhtDivCd": "Type3"}
    d.update(kw)
    return d


class FakeLive:
    def __init__(self, result=None, exc=None):
        self.result = result or LiveResult("ok", None, (item(),), 1)
        self.exc = exc
        self.calls = []

    def festivals(self, **kw):
        self.calls.append(kw)
        if self.exc:
            raise self.exc
        return self.result


class Clock:
    now = 0.0

    def __call__(self):
        return self.now


class Transport:
    async def send(self, **kw):
        return TransportResponse(200, "x")


def bundle():
    return {
        "schema": "kc-chat-bundle/v2", "generated_at": "t", "status": "ok", "trip": None,
        "itinerary": {"anchors": [
            {"type": "visit", "name": "창덕궁", "day": "2026-10-15", "from": "2026-10-15T10:00:00",
             "to": "2026-10-15T12:00:00", "lat": None, "lng": None, "source_quote": "q"}], "free_slots": []},
        "mentions": {"anchors": []}, "cards": [], "problems": [], "coverage_note": "",
        "schedule": {"source": "llm"},
    }


@pytest.fixture
def make(tmp_path, monkeypatch):
    db = tmp_path / "idx.db"
    db.write_bytes(b"")
    clock = Clock()

    def go(live, *, elapsed=0.0, b=None):
        def fake_story(text, trip, dbp, **kw):
            clock.now += elapsed
            return copy.deepcopy(b or bundle())

        monkeypatch.setattr("backend.chat.run_story", fake_story)
        monkeypatch.setattr("backend.chat.run_catalog", lambda *a, **k: {"events": [], "excluded": [], "problems": []})
        s = Settings(hitl_db=tmp_path / "h.db", audit_dir=tmp_path / "audit", output_dir=tmp_path / "o",
                     reviewer_id="human:t", index_db=db)
        return ChatService(s, transport=Transport(), clock=clock, env=dict(KEY), tourapi=live)

    return go


def send(svc, sess=None):
    return asyncio.run(svc.send(SCHED, None, session=sess))


def test_ok_attaches_field_values_unchanged(make):
    live = FakeLive()
    res = send(make(live))
    k = res.bundle["kto_live"]
    assert k["status"] == "ok" and k["reason"] is None and k["total"] == 1
    assert k["items"] == [item()]
    assert k["source_url"].startswith("https://www.data.go.kr/") and set(k["attribution"]) == {"Type3", "Type1"}
    assert live.calls == [{"date_from": "2026-10-15", "date_to": "2026-10-15", "signgu": None}]


def test_failure_is_unavailable(make):
    res = send(make(FakeLive(LiveResult("unavailable", "no_key"))))
    k = res.bundle["kto_live"]
    assert k["status"] == "unavailable" and k["reason"] == "no_key" and k["items"] == []


def test_exception_is_unavailable_without_message(make):
    res = send(make(FakeLive(exc=RuntimeError("https://x?serviceKey=SECRETKEY"))))
    k = res.bundle["kto_live"]
    assert k["status"] == "unavailable" and "SECRETKEY" not in json.dumps(res.bundle)


def test_low_budget_does_not_call(make):
    live = FakeLive()
    res = send(make(live, elapsed=88))  # 100-5-88 = 7 < 8
    assert live.calls == [] and res.bundle["kto_live"]["reason"] == "budget"
    live2 = FakeLive()
    send(make(live2, elapsed=87))  # 정확히 8초
    assert len(live2.calls) == 1


def test_session_limit_10_per_day_resets_next_day(make):
    live = FakeLive()
    svc = make(live)
    sess = Session("t", 0.0, 0.0)
    for _ in range(10):
        assert send(svc, sess).bundle["kto_live"]["status"] == "ok"
    r = send(svc, sess)
    assert r.bundle["kto_live"]["reason"] == "limit" and len(live.calls) == 10
    from datetime import timedelta
    base = svc._today()
    svc._today = lambda: base + timedelta(days=1)
    assert send(svc, sess).bundle["kto_live"]["status"] == "ok" and len(live.calls) == 11


def test_cache_hit_schedule_still_calls_live_each_time(make):
    b = bundle()
    b["schedule"] = {"source": "cache"}
    live = FakeLive()
    svc = make(live, b=b)
    send(svc)
    send(svc)
    assert len(live.calls) == 2


def test_fixed_reply_has_no_field(make, monkeypatch):
    from backend import story_runner

    live = FakeLive()
    svc = make(live)

    def boom(*a, **k):
        raise story_runner.StoryRunnerError("timeout")

    monkeypatch.setattr("backend.chat.run_story", boom)
    res = send(svc)
    assert res.bundle is None and live.calls == []


def test_no_anchors_has_no_field(make):
    b = bundle()
    b["itinerary"]["anchors"] = []
    b["problems"] = [{"code": "X", "message": "m"}]
    live = FakeLive()
    res = send(make(live, b=b))
    assert not (res.bundle and "kto_live" in res.bundle) and live.calls == []


def test_value_not_in_llm_context_history_or_audit(make, tmp_path):
    svc = make(FakeLive())
    sess = Session("t", 0.0, 0.0)
    res = send(svc, sess)
    assert SECRET in json.dumps(res.bundle, ensure_ascii=False)
    assert SECRET not in json.dumps(res.reply, ensure_ascii=False)
    assert SECRET not in json.dumps(svc._context(), ensure_ascii=False)
    assert SECRET not in json.dumps([m for m, _ in sess.history], ensure_ascii=False, default=str)
    assert SECRET not in json.dumps(res.logs, ensure_ascii=False, default=str)
    for f in (tmp_path / "audit").glob("*.jsonl"):
        assert SECRET not in f.read_text(encoding="utf-8")


def test_long_item_dropped_others_byte_identical():
    ok1, ok2 = item(contentid="1"), item(contentid="2", title="가" * 200)
    long = item(contentid="3", title="가" * 201)
    odd = item(contentid="4", tel=5)
    k = kto_live_block("ok", None, (ok1, long, odd, ok2), 4, fetched_at="t")
    assert k["items"] == [ok1, ok2] and k["total"] == 4
    assert json.dumps(k["items"][1], ensure_ascii=False) == json.dumps(ok2, ensure_ascii=False)


def test_items_capped_at_20_and_bad_status():
    k = kto_live_block("ok", None, [item(contentid=str(i)) for i in range(30)], 30, fetched_at="t")
    assert len(k["items"]) == KTO_MAX_ITEMS == 20
    b = kto_live_block("weird", None, (), None, fetched_at="t")
    assert b["status"] == "unavailable" and b["reason"] == "bad_shape"


def test_signgu_only_when_anchors_share_known_gu(make):
    b = bundle()
    b["itinerary"]["anchors"][0]["gu"] = "종로구"
    live = FakeLive()
    send(make(live, b=b))
    assert live.calls[0]["signgu"] == "110"
    b2 = bundle()
    b2["itinerary"]["anchors"][0]["gu"] = "없는구"
    live2 = FakeLive()
    send(make(live2, b=b2))
    assert live2.calls[0]["signgu"] is None


def test_default_service_never_calls_real_network(tmp_path, monkeypatch):
    """테스트 환경에서는 키를 못 읽는다(tests/conftest.py) -> 기본 생성 TourApiLive 는 no_key."""
    s = Settings(hitl_db=tmp_path / "h.db", audit_dir=tmp_path / "a", output_dir=tmp_path / "o", reviewer_id="human:t")
    svc = ChatService(s, env={})
    r = svc._tourapi.festivals(date_from="2026-10-15", date_to="2026-10-15")
    assert r.status == "unavailable" and r.reason == "no_key"


def test_session_count_refunded_when_not_called(make):
    """키 없음·전역 상한은 네트워크에 닿지 않았다 — 세션 하루 10회 몫을 쓰지 않는다."""
    sess = Session("t", 0.0, 0.0)
    send(make(FakeLive(LiveResult("unavailable", "no_key"))), sess)
    send(make(FakeLive(LiveResult("unavailable", "limit"))), sess)
    assert sess.tourapi_calls == 0
    send(make(FakeLive(LiveResult("unavailable", "timeout"))), sess)  # 실제로 호출했으면 센다
    assert sess.tourapi_calls == 1


def test_pipeline_kto_live_is_dropped(make):
    """kto_live 는 backend 만 만든다 — 파이프라인 출력에 들어 있어도 내보내지 않는다."""
    b = bundle()
    b["kto_live"] = kto_live_block("ok", None, (item(title="자식이-만든-값"),), 1, fetched_at="t")
    b["itinerary"]["anchors"] = []
    b["problems"] = [{"code": "X", "message": "m"}]
    res = send(make(FakeLive(), b=b))
    assert "자식이-만든-값" not in json.dumps(res.bundle or {}, ensure_ascii=False)
