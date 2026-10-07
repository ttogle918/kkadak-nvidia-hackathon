import json
from datetime import date
from pathlib import Path

from domains.kcontext.ingest.events.__main__ import main
from domains.kcontext.ingest.events.manual import load_manual
from domains.kcontext.ingest.events.store import read_jsonl
from domains.kcontext.judge.now import judge_events
from domains.kcontext.regions import load_regions

REPO = Path(__file__).resolve().parents[4]
FIX = REPO / "tests" / "fixtures" / "kcontext" / "events" / "manual.synthetic.json"
SIT = {"trip": {"from": "2026-10-15", "to": "2026-10-18"}, "party": {"size": 2}}


def test_fixture_loads_with_region_inferred_from_text():
    res = load_manual(FIX, regions=load_regions())
    ids = {r.id for r in res.records}
    assert "m_elsewhere" not in ids and res.skipped_out_of_region == 1
    assert len(res.records) == 7
    assert {r.region for r in res.records} == {"jung"}
    assert all(r.fetched_from == "manual" and r.synthetic for r in res.records)
    assert res.problems == ()


def test_bad_inputs_become_problems(tmp_path: Path):
    p = tmp_path / "m.json"
    p.write_text("{}", encoding="utf-8")
    assert load_manual(p, regions=load_regions()).problems
    p.write_text("not json", encoding="utf-8")
    assert load_manual(p, regions=load_regions()).problems
    assert load_manual(tmp_path / "none.json", regions=load_regions()).problems
    rows = json.loads(FIX.read_text(encoding="utf-8"))
    bad_from = {**rows[0], "id": "x1", "fetched_from": "tourapi"}
    bad_region = {**rows[0], "id": "x2", "region": "ghost"}
    broken = {"id": "x3"}
    dup = {**rows[0], "title": "○○ 가을 야시장 (수정)"}
    p.write_text(json.dumps([bad_from, bad_region, broken, rows[0], dup], ensure_ascii=False),
                 encoding="utf-8")
    res = load_manual(p, regions=load_regions())
    assert len(res.records) == 1 and res.records[0].title == "○○ 가을 야시장 (수정)"
    assert len(res.problems) == 4 and res.skipped_out_of_region == 1


def test_explicit_region_is_kept(tmp_path: Path):
    rows = json.loads(FIX.read_text(encoding="utf-8"))
    rows[0]["region"] = "jongno"
    tmp = tmp_path / "m.json"
    tmp.write_text(json.dumps(rows[:1], ensure_ascii=False), encoding="utf-8")
    assert load_manual(tmp, regions=load_regions()).records[0].region == "jongno"


def test_manual_notices_feed_the_judge():
    res = load_manual(FIX, regions=load_regions())
    j = judge_events(res.records, SIT, now=date(2026, 10, 7))
    reasons = {r.target_id: r.reason for r in j.rejected}
    assert reasons["m_past"] == "기간 지남"
    assert reasons["m_inject"] == "지시문 포함"
    # 원 공지·시간 변경·취소 공지는 한 행사 — 가장 최근(취소)이 채택돼 전부 취소됨
    assert {reasons[i] for i in ("m_orig", "m_time", "m_cancel")} == {"취소됨"}
    by_id = {d.primary.id: d for d in j.decisions}
    assert by_id["m_ok"].badge == "확인됨"
    assert "날짜 불분명" in by_id["m_nodate"].caveats


def test_cli_manual_end_to_end(tmp_path: Path, capsys):
    out, db = tmp_path / "ev.jsonl", tmp_path / "idx" / "kc.db"
    rc = main(["--provider", "manual", "--fixture", str(FIX), "--from", "2026-10-15",
               "--to", "2026-10-18", "--out", str(out), "--db", str(db),
               "--collected-at", "2026-10-07"])
    assert rc == 0
    report = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert report == {"records": 6, "problems": 0, "skipped_out_of_region": 1,
                      "skipped_out_of_range": 1}
    assert len(read_jsonl(out)) == 6 and db.exists()


def test_cli_without_range_keeps_everything(tmp_path: Path, capsys):
    out = tmp_path / "ev.jsonl"
    assert main(["--provider", "manual", "--fixture", str(FIX), "--out", str(out),
                 "--collected-at", "2026-10-07"]) == 0
    assert len(read_jsonl(out)) == 7


def test_cli_api_provider_without_field_map_exits_2(tmp_path: Path, capsys):
    fx = tmp_path / "r.json"
    fx.write_text("{}", encoding="utf-8")
    rc = main(["--provider", "tourapi", "--fixture", str(fx), "--field-map-dir", str(tmp_path),
               "--collected-at", "2026-10-07"])
    assert rc == 2 and "--provider manual" in capsys.readouterr().err


def test_cli_api_provider_with_synthetic_field_map(tmp_path: Path, capsys):
    (tmp_path / "tourapi_festival.json").write_text(json.dumps({
        "items_path": ["items"], "fields": {"id": "○_id", "title": "○_title", "address": "○_addr",
                                            "start_date": "○_s", "end_date": "○_e"},
        "date_format": "%Y%m%d"}), encoding="utf-8")
    fx = tmp_path / "resp.json"
    fx.write_text(json.dumps({"items": [{"○_id": "1", "○_title": "○○ 축제", "○_addr": "중구 ○○",
                                          "○_s": "20261016", "○_e": "20261017"}]},
                             ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "o.jsonl"
    rc = main(["--provider", "tourapi", "--fixture", str(fx), "--field-map-dir", str(tmp_path),
               "--out", str(out), "--collected-at", "2026-10-07"])
    assert rc == 0 and read_jsonl(out)[0].region == "jung"


def test_cli_unreadable_fixture_exits_2(tmp_path: Path):
    (tmp_path / "tourapi_festival.json").write_text("{}", encoding="utf-8")
    rc = main(["--provider", "tourapi", "--fixture", str(tmp_path / "none.json"),
               "--field-map-dir", str(tmp_path), "--collected-at", "2026-10-07"])
    assert rc == 2


def test_cli_web_provider_is_forwarded(tmp_path: Path, capsys):
    web_fix = REPO / "tests" / "fixtures" / "kcontext" / "events" / "web.synthetic.json"
    out = tmp_path / "w.jsonl"
    rc = main(["--provider", "web", "--source", "junggu", "--month", "2026-10",
               "--fixture", str(web_fix), "--out", str(out), "--collected-at", "2026-10-07"])
    assert rc == 0  # 실제 inject.screen 이 연결돼 있다
    report = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert report["candidates"] == 3 and report["records"] == len(read_jsonl(out)) == 1
