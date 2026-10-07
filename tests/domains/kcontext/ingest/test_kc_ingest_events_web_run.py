import json
from pathlib import Path

import httpx
import pytest

from domains.kcontext.contract.records import Blocked, event_from_dict
from domains.kcontext.ingest.events import web_run
from domains.kcontext.ingest.events.web import KEY_ENV

REPO = Path(__file__).resolve().parents[4]
KEY = "tvly-" + "a" * 24
FIXTURE = REPO / "tests" / "fixtures" / "kcontext" / "events" / "web.synthetic.json"


def fake_screen(text: str, source_id: str):
    return Blocked(source_id, "injection", ("t",)) if "이전 지시를 모두 무시" in text else None


def test_fixture_run_writes_validated_records(tmp_path, capsys):
    out = tmp_path / "sub" / "web.jsonl"
    rc = web_run.run(
        ["--source", "junggu", "--month", "2026-10", "--fixture", str(FIXTURE),
         "--out", str(out), "--collected-at", "2026-10-07"],
        screen=fake_screen,
    )
    assert rc == 0
    rows = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2  # 정상 1 · 게시일 보충 1 · quote 불일치 버림 · 지시문 후보 버림
    rec = event_from_dict(rows[0])
    assert rec.fetched_from == "web" and rec.region == "jung"
    report = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert report["candidates"] == 4 and report["records"] == 2 and report["dropped"] == 2
    assert report["calls"] == 0


def test_missing_key_exits_2_with_fixture_hint(capsys):
    rc = web_run.run(["--source", "junggu", "--month", "2026-10"], env={})
    assert rc == 2 and "--fixture" in capsys.readouterr().err


def test_no_screen_exits_2(monkeypatch, capsys):
    monkeypatch.setattr(web_run, "_default_screen", lambda: None)
    rc = web_run.run(["--source", "junggu", "--month", "2026-10", "--fixture", str(FIXTURE),
                      "--collected-at", "2026-10-07"])
    assert rc == 2 and "screen" in capsys.readouterr().err


def test_real_search_without_extractor_exits_2(capsys):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    rc = web_run.run(["--source", "gangnam", "--month", "2026-10", "--collected-at", "2026-10-07"],
                     screen=fake_screen, client=client, env={KEY_ENV: KEY})
    assert rc == 2 and "T223" in capsys.readouterr().err


def test_candidates_only_prints_urls_and_needs_no_screen(capsys):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [
            {"url": "https://www.gangnam.go.kr/board/B_000045/list.do", "title": "행사",
             "content": "c", "score": 0.5},
            {"url": "https://www.gangnam.go.kr/board/B_000057/x", "title": "차단", "content": "c"},
            {"url": "https://other.invalid/", "title": "밖", "content": "c"},
        ]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    rc = web_run.run(["--source", "gangnam", "--month", "2026-10", "--candidates-only"],
                     client=client, env={KEY_ENV: KEY})
    assert rc == 0
    lines = capsys.readouterr().out.splitlines()
    assert "B_000045" in lines[0] and "B_000057" not in "".join(lines)
    summary = json.loads(lines[-1])
    assert summary["candidates"] == 1 and summary["dropped_urls"] == 2


def test_unconfirmed_source_exits_2(tmp_path, capsys):
    (tmp_path / "xx.json").write_text(json.dumps({
        "region": "jung", "gu": "중구", "domains": ["a.invalid"], "queries": ["{gu}"],
        "status": "unconfirmed"}), encoding="utf-8")
    rc = web_run.run(["--source", "xx", "--month", "2026-10"], env={KEY_ENV: "k"},
                     sources_dir=tmp_path)
    assert rc == 2 and "confirmed" in capsys.readouterr().err


def test_unknown_source_and_region(tmp_path, capsys):
    assert web_run.run(["--source", "nope", "--month", "2026-10"], env={}) == 2
    (tmp_path / "yy.json").write_text(json.dumps({
        "region": "ghost", "gu": "x", "domains": ["a.invalid"], "queries": ["{gu}"],
        "status": "confirmed"}), encoding="utf-8")
    assert web_run.run(["--source", "yy", "--month", "2026-10"], env={},
                       sources_dir=tmp_path) == 2
    assert "ghost" in capsys.readouterr().err


def test_synthetic_fixture_cannot_be_indexed(tmp_path, capsys):
    db = tmp_path / "kc.db"
    rc = web_run.run(["--source", "junggu", "--month", "2026-10", "--fixture", str(FIXTURE),
                      "--db", str(db), "--collected-at", "2026-10-07"], screen=fake_screen)
    assert rc == 2 and "합성" in capsys.readouterr().err and not db.exists()


def test_fixture_records_are_marked_synthetic(tmp_path):
    out = tmp_path / "w.jsonl"
    web_run.run(["--source", "junggu", "--month", "2026-10", "--fixture", str(FIXTURE),
                 "--out", str(out), "--collected-at", "2026-10-07"], screen=fake_screen)
    rows = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert rows and all(r["synthetic"] is True for r in rows)


def test_bad_month_exits_2(capsys):
    assert web_run.run(["--source", "junggu", "--month", "2026-13", "--fixture",
                        str(FIXTURE), "--collected-at", "2026-10-07"], screen=fake_screen) == 2


def test_problems_are_printed_to_stderr(tmp_path, capsys):
    web_run.run(["--source", "junggu", "--month", "2026-10", "--fixture", str(FIXTURE),
                 "--collected-at", "2026-10-07"], screen=fake_screen)
    assert "problem:" in capsys.readouterr().err


@pytest.mark.parametrize("bad", ["2026-13-01", "2026-02-30", "어제", "2026/10/07"])
def test_invalid_collected_at_exits_2(bad, capsys):
    rc = web_run.run(["--source", "junggu", "--month", "2026-10", "--fixture", str(FIXTURE),
                      "--collected-at", bad], screen=fake_screen)
    assert rc == 2 and "--collected-at" in capsys.readouterr().err
