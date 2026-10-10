"""T419 — TourAPI 실시간 클라이언트. httpx.MockTransport 만 쓴다(실호출 0회)."""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

import httpx
import pytest

from backend import tourapi_live as tl
from backend.settings import Settings

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "tourapi"
SECRET = "SECRETKEY+/=abc"


def fx(name: str) -> bytes:
    return (FIX / name).read_bytes()


def make(handler, *, key=SECRET, daily=300, today=lambda: date(2026, 10, 10), **kw):
    calls: list[httpx.Request] = []

    def h(req: httpx.Request) -> httpx.Response:
        calls.append(req)
        return handler(req)

    client = httpx.Client(transport=httpx.MockTransport(h))
    api = tl.TourApiLive(key_lookup=lambda: key, client=client, daily_calls=daily, today=today, **kw)
    return api, calls


def ok(name):
    return lambda req: httpx.Response(200, content=fx(name))


def fest(api, **kw):
    return api.festivals(date_from="2026-10-10", date_to="2026-12-31", **kw)


def test_list_ok_and_values_unchanged_and_seoul_only():
    api, calls = make(ok("list.json"))
    r = fest(api)
    assert r.status == "ok" and r.reason is None and r.total == 3
    assert len(r.items) == 2  # lDongRegnCd 26 항목 제외
    src = json.loads(fx("list.json"))["response"]["body"]["items"]["item"][0]
    for f, v in r.items[0].items():
        assert f in tl.SHOW_FIELDS and v == src[f]
    assert "mapx" not in r.items[0] and "firstimage" not in r.items[0]
    q = calls[0].url.params
    assert q["eventStartDate"] == "20261010" and q["eventEndDate"] == "20261231"
    assert q["lDongRegnCd"] == "11" and q["numOfRows"] == "20" and q["pageNo"] == "1"
    assert "lDongSignguCd" not in q


def test_single_object_item():
    api, _ = make(ok("single.json"))
    r = fest(api)
    assert r.status == "ok" and len(r.items) == 1 and r.total == 1


def test_empty_items():
    api, _ = make(ok("empty.json"))
    r = fest(api)
    assert r.status == "ok" and r.items == () and r.total == 0


@pytest.mark.parametrize("name,reason", [("gateway20.json", "gateway:20"), ("gateway30.json", "gateway:30"),
                                          ("result_err.json", "result:0010")])
def test_gateway_and_result_errors(name, reason):
    api, _ = make(ok(name))
    r = fest(api)
    assert (r.status, r.reason, r.items) == ("unavailable", reason, ())


def test_non_json_and_bad_shape_and_http_status():
    api, _ = make(lambda req: httpx.Response(200, content=b"<xml/>"))
    assert fest(api).reason == "bad_shape"
    api, _ = make(lambda req: httpx.Response(200, content=b'{"foo": 1}'))
    assert fest(api).reason == "bad_shape"
    api, _ = make(lambda req: httpx.Response(500, content=b"x"))
    assert fest(api).reason == "http"


def test_timeout_and_network_error():
    def boom(req):
        raise httpx.ReadTimeout("t", request=req)

    api, _ = make(boom)
    assert fest(api).reason == "timeout"

    def net(req):
        raise httpx.ConnectError(str(req.url), request=req)

    api, _ = make(net)
    assert fest(api).reason == "http"


def test_body_cap_1mb():
    api, _ = make(lambda req: httpx.Response(200, content=b" " * (tl.MAX_BODY_BYTES + 10)))
    assert fest(api).reason == "bad_shape"


def test_no_key_does_not_call():
    api, calls = make(ok("list.json"), key=None)
    assert fest(api).reason == "no_key" and calls == []
    api, calls = make(ok("list.json"), key="  ")
    assert fest(api).reason == "no_key" and calls == []


def test_daily_limit_and_kst_reset():
    day = [date(2026, 10, 10)]
    api, calls = make(ok("list.json"), daily=2, today=lambda: day[0])
    assert fest(api).status == "ok" and fest(api).status == "ok"
    r = fest(api)
    assert (r.status, r.reason) == ("unavailable", "limit") and len(calls) == 2
    day[0] = date(2026, 10, 11)
    assert fest(api).status == "ok" and len(calls) == 3


def test_limit_zero_never_calls():
    api, calls = make(ok("list.json"), daily=0)
    assert fest(api).reason == "limit" and calls == []


def _raw_query(req: httpx.Request) -> str:
    return req.url.raw_path.decode()


def test_key_encoding_no_double_encode():
    api, calls = make(ok("list.json"), key="abc%2Bdef%3D")
    fest(api)
    assert "serviceKey=abc%2Bdef%3D&" in _raw_query(calls[0]) and "%25" not in _raw_query(calls[0])
    api, calls = make(ok("list.json"), key="ab+c/d=")
    fest(api)
    assert "serviceKey=ab%2Bc%2Fd%3D&" in _raw_query(calls[0]) and "%25" not in _raw_query(calls[0])


def test_signgu_known_and_unknown():
    api, calls = make(ok("list.json"))
    fest(api, signgu="110")
    assert calls[0].url.params["lDongSignguCd"] == "110"
    fest(api, signgu="999")
    assert "lDongSignguCd" not in calls[1].url.params
    fest(api, signgu=None)
    assert "lDongSignguCd" not in calls[2].url.params


def test_codes_file_has_25_gu_with_provenance():
    raw = json.loads(tl.CODES_PATH.read_text(encoding="utf-8"))
    assert len(raw["signgu"]) == 25 and raw["checked"] and raw["source"]
    assert {"215", "305", "545"} <= set(raw["signgu"])


def test_bad_dates_do_not_call():
    api, calls = make(ok("list.json"))
    assert api.festivals(date_from="20261010", date_to="2026-12-31").reason == "bad_shape" and calls == []


def test_no_key_or_url_in_logs_and_results(caplog):
    caplog.set_level(logging.DEBUG)
    cases = [ok("list.json"), ok("gateway30.json"), lambda r: httpx.Response(500, content=b"x"),
             lambda r: (_ for _ in ()).throw(httpx.ConnectError(str(r.url), request=r)),
             lambda r: (_ for _ in ()).throw(httpx.ReadTimeout(str(r.url), request=r))]
    for h in cases:
        api, _ = make(h)
        res = fest(api)
        assert SECRET not in repr(res) and "apis.data.go.kr" not in repr(res)
    text = "\n".join(r.getMessage() for r in caplog.records)
    assert "tourapi status=" in text
    assert SECRET not in text and "SECRETKEY" not in text and "apis.data.go.kr" not in text and "serviceKey" not in text


def test_env_key_lookup_shell_then_dotenv(tmp_path):
    dot = tmp_path / ".env"
    dot.write_text("OTHER_SECRET=zzz\nDATA_GO_KR_SERVICE_KEY=fromfile\n", encoding="utf-8")
    env = {"APP_DOTENV_PATH": str(dot)}
    assert tl.env_key_lookup(env) == "fromfile"
    assert tl.env_key_lookup({**env, tl.KEY_ENV: "fromshell"}) == "fromshell"
    assert tl.env_key_lookup({"APP_DOTENV_PATH": str(tmp_path / "none")}) is None


def test_settings_fields():
    s = Settings.from_env({})
    assert s.tourapi_daily_calls == 300 and s.tourapi_timeout_s == 5.0
    s = Settings.from_env({"KC_TOURAPI_DAILY_CALLS": "5", "KC_TOURAPI_TIMEOUT_S": "2.5"})
    assert s.tourapi_daily_calls == 5 and s.tourapi_timeout_s == 2.5
    with pytest.raises(ValueError):
        Settings.from_env({"KC_TOURAPI_TIMEOUT_S": "0"})


def test_total_deadline_cuts_slow_trickle(monkeypatch):
    """httpx timeout 은 단계별이다 — 조금씩 흘려보내는 응답도 전체 timeout_s 안에서 끊는다(D29 ⑤)."""
    t = {"now": 0.0}
    monkeypatch.setattr(tl.time, "monotonic", lambda: t["now"])

    class Trickle(httpx.SyncByteStream):
        def __iter__(self):
            for _ in range(10):
                t["now"] += 1.0  # 조각마다 1초
                yield b" "

    api, _ = make(lambda req: httpx.Response(200, stream=Trickle()), timeout_s=5.0)
    assert fest(api).reason == "timeout"
