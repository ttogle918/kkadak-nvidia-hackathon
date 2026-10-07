import dataclasses
import json
from datetime import datetime, timedelta

import pytest
from kc_catalog_helpers import NOW, obs, session

from domains.kcontext.catalog.__main__ import main as cli_main
from domains.kcontext.catalog.changes import diff_catalog, diff_entries
from domains.kcontext.catalog.merge import build_entries
from domains.kcontext.catalog.model import Reservation
from domains.kcontext.catalog.runlog import backoff_minutes, due, record_failure, record_success
from domains.kcontext.catalog.sources import SourceError, load_sources, make_fetcher
from domains.kcontext.catalog.store import CatalogStore
from domains.kcontext.catalog.updater import run_due, run_source

LATER = NOW + timedelta(hours=26)


def store(tmp_path):
    return CatalogStore(tmp_path / "cat")


def ok(*o):
    return lambda: list(o)


def boom(msg="연결 실패"):
    def f():
        raise RuntimeError(msg)

    return f


# ---- 수집 성공: 신규 등록·마지막 검증 시각 ---------------------------------------------------
def test_first_run_registers_new_events_and_records_success(tmp_path):
    st = store(tmp_path)
    r = run_source(st, "src", ok(obs("s:1", external_ids=("k1",))), now=NOW)
    assert r.ok and r.fetched == 1 and r.new_entries == 1
    (e,) = st.load_entries()
    assert e.last_verified_at == "2026-10-07T12:00"
    run = st.load_runs()["src"]
    assert run["last_success_at"] == "2026-10-07T12:00" and run["last_error"] is None
    assert run["consecutive_failures"] == 0 and run["last_counts"]["fetched"] == 1
    assert [c["field"] for c in st.load_changes()] == ["__new__"]


# ---- 실패해도 기존 데이터를 유지한다 ----------------------------------------------------------
def test_failure_keeps_existing_data_and_records_error(tmp_path):
    st = store(tmp_path)
    run_source(st, "src", ok(obs("s:1")), now=NOW)
    before_entries = [e.to_dict() for e in st.load_entries()]
    before_obs = json.loads((st.dir / "observations.json").read_text(encoding="utf-8"))
    r = run_source(st, "src", boom("서버 응답 없음"), now=LATER)
    assert not r.ok and "서버 응답 없음" in r.error
    assert [e.to_dict() for e in st.load_entries()] == before_entries
    assert json.loads((st.dir / "observations.json").read_text(encoding="utf-8")) == before_obs
    run = st.load_runs()["src"]
    assert run["consecutive_failures"] == 1 and run["last_success_at"] == "2026-10-07T12:00"
    assert run["next_retry_at"] == (LATER + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M")
    assert len(st.load_changes()) == 1  # 실패는 변경을 만들지 않는다


def test_error_text_is_redacted(tmp_path):
    st = store(tmp_path)
    key = "nvapi-" + "A" * 24
    r = run_source(st, "src", boom(f"failed Authorization: Bearer {key}"), now=NOW)
    assert key not in r.error and key not in json.dumps(st.load_runs())


def test_retry_backoff_grows_and_resets_on_success(tmp_path):
    runs: dict = {}
    for n in range(1, 5):
        record_failure(runs, "s", NOW, "x")
    assert runs["s"]["consecutive_failures"] == 4
    assert [backoff_minutes(n) for n in (1, 2, 3, 4, 20)] == [5, 10, 20, 40, 360]
    record_success(runs, "s", NOW, {"fetched": 3})
    assert runs["s"]["consecutive_failures"] == 0 and runs["s"]["next_retry_at"] is None


def test_due_follows_cadence_and_retry_time():
    runs: dict = {}
    assert due(runs, "s", NOW, 24)
    record_success(runs, "s", NOW, {"fetched": 1})
    assert not due(runs, "s", NOW + timedelta(hours=23), 24)
    assert due(runs, "s", NOW + timedelta(hours=24), 24)
    record_failure(runs, "s", NOW + timedelta(hours=1), "x")
    assert not due(runs, "s", NOW + timedelta(hours=1, minutes=4), 24)
    assert due(runs, "s", NOW + timedelta(hours=1, minutes=5), 24)


# ---- 사라진 게시글·빈 결과로 취소하지 않는다 --------------------------------------------------
def test_event_missing_from_a_later_fetch_is_kept_and_not_cancelled(tmp_path):
    st = store(tmp_path)
    a = obs("s:1", external_ids=("k1",))
    b = obs("s:2", title="○○ 다른 행사", venue_name="△△ 극장", external_ids=("k2",))
    run_source(st, "src", ok(a, b), now=NOW)
    run_source(st, "src", ok(a), now=LATER)  # b 가 목록에서 빠졌다
    by = {e.title: e for e in st.load_entries()}
    gone = by["○○ 다른 행사"]
    assert gone.lifecycle != "cancelled" and gone.last_verified_at == "2026-10-07T12:00"
    assert by["○○ 가을 음악회"].last_verified_at == LATER.strftime("%Y-%m-%dT%H:%M")


def test_empty_successful_fetch_keeps_everything_with_a_warning(tmp_path):
    st = store(tmp_path)
    run_source(st, "src", ok(obs("s:1")), now=NOW)
    r = run_source(st, "src", ok(), now=LATER)
    assert r.ok and r.fetched == 0 and len(st.load_entries()) == 1
    assert st.load_runs()["src"]["last_warning"] == "빈 결과"


# ---- 변경 이력 --------------------------------------------------------------------------------
def test_changes_are_recorded_for_date_time_place_price_reservation_and_cancel(tmp_path):
    st = store(tmp_path)
    a = obs("s:1", external_ids=("k1",), sessions=(session(start="19:30"),), price_kind="free")
    run_source(st, "src", ok(a), now=NOW)
    a2 = dataclasses.replace(
        a,
        schedule=dataclasses.replace(a.schedule, start_date="2026-10-17", end_date="2026-10-17",
                                     sessions=(session("2026-10-17", "20:00"),)),
        venue=dataclasses.replace(a.venue, name="△△ 극장"),
        price=dataclasses.replace(a.price, kind="paid", text="1만원"),
        reservation=Reservation(required="yes", link="https://example.invalid/r", deadline="2026-10-15"),
        lifecycle="cancelled",
        evidence=dataclasses.replace(a.evidence, kind="official_site"),
    )
    run_source(st, "src", ok(a2), now=LATER)
    changes = [c for c in st.load_changes() if c["field"] != "__new__"]
    fields = {c["field"] for c in changes}
    assert {"start_date", "end_date", "sessions", "venue", "price", "reservation", "lifecycle"} <= fields
    by = {c["field"]: c for c in changes}
    assert by["start_date"]["old"] == "2026-10-16" and by["start_date"]["new"] == "2026-10-17"
    assert by["lifecycle"]["new"] == "cancelled" and by["lifecycle"]["importance"] == "major"
    assert all(c["detected_at"] == LATER.strftime("%Y-%m-%dT%H:%M") for c in changes)


def test_time_passing_alone_is_not_a_change():
    (e1,) = build_entries([obs("s:1")], now=NOW)
    (e2,) = build_entries([obs("s:1")], now=NOW + timedelta(days=30))  # 예정 → 종료
    assert e1.lifecycle != e2.lifecycle
    assert [c for c in diff_entries(e1, e2, "x") if c.field == "lifecycle"] == []


def test_minor_vs_major_importance_and_new_entries():
    (a,) = build_entries([obs("s:1", title="○○ 가을 음악회")], now=NOW)
    (b,) = build_entries([obs("s:1", title="○○ 가을 음악회 (앵콜)")], now=NOW)
    (c,) = diff_entries(a, b, "t")
    assert c.field == "title" and c.importance == "minor"
    ch = diff_catalog([a], [a, dataclasses.replace(a, id="ev:new", title="○○ 새 행사")], "t")
    assert [(x.field, x.importance) for x in ch] == [("__new__", "new")]


# ---- 주기 실행·출처 레지스트리 ----------------------------------------------------------------
def test_run_due_skips_sources_without_fetchers_and_not_due(tmp_path):
    st = store(tmp_path)
    sources = [{"id": "a", "cadence_hours": 24}, {"id": "b", "cadence_hours": 24}]
    res = run_due(st, sources, {"a": ok(obs("s:1"))}, now=NOW)
    assert [r.source_id for r in res] == ["a"]
    assert run_due(st, sources, {"a": ok(obs("s:1"))}, now=NOW + timedelta(hours=1)) == []
    assert len(run_due(st, sources, {"a": ok(obs("s:1"))}, now=NOW + timedelta(hours=1), force=True)) == 1


def test_source_registry_is_valid_and_honest_about_what_is_implemented():
    by = {s["id"]: s for s in load_sources()}
    assert {"seoul_openapi", "tourapi_kto", "junggu_site", "junggu_sns", "caci", "hanokmaeul",
            "jeongdong"} <= set(by)
    assert by["seoul_openapi"]["status"] == "implemented" and by["seoul_openapi"]["cadence_hours"] == 24
    for sid in ("junggu_sns", "caci", "jeongdong"):
        assert by[sid]["status"] == "manual_only" and by[sid]["method"] == "manual"
    assert by["tourapi_kto"]["status"] == "configurable_unverified"
    assert "확인 필요" in by["tourapi_kto"]["notes"]
    assert all(s["url"].startswith("https://") for s in by.values())


def test_unimplemented_sources_raise_in_make_fetcher():
    from kc_catalog_helpers import REGION

    with pytest.raises(SourceError):
        make_fetcher("caci", region=REGION, now=NOW)
    f = make_fetcher("seoul_openapi", region=REGION, now=NOW, env={})
    with pytest.raises(Exception, match="SEOUL_OPENAPI_KEY"):
        f()


def test_cli_status_and_update_without_key(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("SEOUL_OPENAPI_KEY", raising=False)
    monkeypatch.setattr("domains.kcontext.catalog.__main__._env", dict)
    d = str(tmp_path / "c")
    assert cli_main(["--dir", d, "status"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["entries"] == 0 and len(out["sources"]) >= 7
    assert cli_main(["--dir", d, "update", "--source", "seoul_openapi"]) == 2
    assert "SEOUL_OPENAPI_KEY" in capsys.readouterr().err
    assert cli_main(["--dir", d, "update", "--source", "caci"]) == 2


def test_naive_now_is_treated_as_seoul_time(tmp_path):
    st = store(tmp_path)
    naive = datetime(2026, 10, 7, 12, 0)  # noqa: DTZ001
    run_source(st, "src", ok(obs("s:1")), now=naive)
    assert st.load_runs()["src"]["last_success_at"] == "2026-10-07T12:00"


# ---- 2차 검토(reviewer) 재발 방지 ----------------------------------------------------------
def test_sample_collection_requires_an_explicit_scratch_dir(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("domains.kcontext.catalog.__main__._env", dict)
    assert cli_main(["update", "--source", "seoul_openapi", "--sample"]) == 2
    assert "--dir" in capsys.readouterr().err


def test_concurrent_writers_do_not_lose_updates(tmp_path):
    """제보 제출이 여러 프로세스에서 동시에 일어나도 한 건도 사라지지 않는다(파일 잠금)."""
    import subprocess
    import sys
    from pathlib import Path

    repo = Path(__file__).resolve().parents[4]
    code = (
        "import sys\n"
        "from datetime import datetime\n"
        "from domains.kcontext.catalog.reports import submit\n"
        "from domains.kcontext.catalog.rules import KST\n"
        "from domains.kcontext.catalog.store import CatalogStore\n"
        "st = CatalogStore(sys.argv[1])\n"
        "for i in range(5):\n"
        "    submit(st, {'kind': 'other', 'official_link': 'https://a.invalid/x', "
        "'reason': f'동시 제출 {sys.argv[2]}-{i} 사유입니다'}, now=datetime(2026, 10, 7, 12, i, tzinfo=KST))\n"
    )
    d = str(tmp_path / "cat")
    procs = [subprocess.Popen([sys.executable, "-c", code, d, str(n)], cwd=repo,
                              env={"PYTHONPATH": str(repo), "PATH": __import__("os").environ["PATH"]})
             for n in range(6)]
    assert all(p.wait(timeout=60) == 0 for p in procs)
    assert len(CatalogStore(d).load_reports()) == 30


def test_lock_is_reentrant_within_a_process(tmp_path):
    st = store(tmp_path)
    with st.lock(), st.lock():
        st.save_runs({"a": {}})
    assert st.load_runs() == {"a": {}}
