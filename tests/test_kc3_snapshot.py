"""T322 — 데모 스냅샷: 서울 출처만 남기기 · 키 흔적 없음 · 되돌리기. 값은 전부 합성(○○), tmp 폴더만 쓴다."""

import dataclasses
import importlib.util
import json
from datetime import datetime
from pathlib import Path

import pytest

from domains.kcontext.catalog.model import Evidence, Observation, Schedule, Venue
from domains.kcontext.catalog.rules import KST
from domains.kcontext.catalog.store import CatalogStore

_spec = importlib.util.spec_from_file_location(
    "snapshot_catalog", Path(__file__).resolve().parent.parent / "scripts" / "snapshot_catalog.py")
snap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(snap)

NOW = datetime(2026, 10, 10, 12, 0, tzinfo=KST)
FAKE_KEY = "FAKEKEYVALUE1234567890"


def _obs(obs_id, source_id, title, url="https://example.invalid/x", end="2026-10-16"):
    ev = Evidence(source_id=source_id, source_name=f"○○ {source_id}", kind="official_api", url=url,
                  quote="인용", origin=obs_id, collected_at="2026-10-09")
    return Observation(
        obs_id=obs_id, title=title, external_ids=(f"{source_id}:{obs_id}",), evidence=ev,
        venue=Venue(name="○○ 홀", district="중구", district_basis="source_gu", in_target="yes"),
        schedule=Schedule(start_date="2026-10-16", end_date=end))


def _wrap(o):
    return {"observation": o, "source_id": o.evidence.source_id,
            "first_seen_at": "2026-10-09T10:00", "last_seen_at": "2026-10-09T10:00"}


@pytest.fixture
def src(tmp_path):
    d = tmp_path / "catalog"
    st = CatalogStore(d)
    items = [
        _obs("s:1", "seoul_openapi", "○○ 서울 음악회", url=f"https://example.invalid/x?apikey={FAKE_KEY}&a=1"),
        _obs("s:2", "seoul_openapi", "○○ 서울 전시"),
        _obs("t:1", "tavily_web", "○○ 검색 유래 행사"),
        _obs("r:1", "report", "○○ 제보 행사"),
    ]
    st.save_observations({o.obs_id: _wrap(o) for o in items})
    st.save_runs({
        "seoul_openapi": {"last_success_at": "2026-10-09T10:00", "last_error": f"GET /{FAKE_KEY}/json?key={FAKE_KEY}",
                          "last_counts": {"fetched": 2}},
        "tavily_web": {"last_success_at": "2026-10-09T10:00"},
    })
    st.save_reports([{"id": "rep1", "note": "제보"}])
    return d


def test_only_seoul_observations_and_runs_remain(src, tmp_path):
    dst = tmp_path / "snap"
    r = snap.make_snapshot(src, dst, now=NOW, command="cmd")
    assert r["observations"] == 2
    out = CatalogStore(dst)
    obs = out.load_observations()
    assert {v["observation"].evidence.source_id for v in obs.values()} == {"seoul_openapi"}
    assert "t:1" not in obs and "r:1" not in obs
    titles = {e.title for e in out.load_entries()}
    assert titles == {"○○ 서울 음악회", "○○ 서울 전시"}
    assert set(out.load_runs()) == {"seoul_openapi"}
    assert not (dst / "reports.json").exists()
    text = "".join(p.read_text(encoding="utf-8") for p in dst.iterdir())
    assert "tavily" not in text and "검색 유래" not in text and "제보 행사" not in text


def test_no_key_traces_in_any_file(src, tmp_path, monkeypatch):
    monkeypatch.setenv("SEOUL_OPENAPI_KEY", FAKE_KEY)
    dst = tmp_path / "snap"
    snap.make_snapshot(src, dst, now=NOW, command="cmd")
    for p in dst.rglob("*"):
        if p.is_file():
            t = p.read_text(encoding="utf-8")
            assert FAKE_KEY not in t, p.name
            assert f"={FAKE_KEY}" not in t and f"/{FAKE_KEY}" not in t


def test_secret_guard_blocks_when_scrub_misses(src, tmp_path, monkeypatch):
    """정리가 놓쳐도 마지막 검사가 막는다: 정리를 끄면 만들지 않고 폴더도 남기지 않는다."""
    monkeypatch.setenv("SEOUL_OPENAPI_KEY", FAKE_KEY)
    monkeypatch.setattr(snap, "_scrub", lambda v: v)
    dst = tmp_path / "snap"
    with pytest.raises(snap.SnapshotError):
        snap.make_snapshot(src, dst, now=NOW, command="cmd")
    assert not dst.exists() and not (tmp_path / "snap.tmp").exists()


def test_key_value_in_title_is_scrubbed(src, tmp_path, monkeypatch):
    monkeypatch.setenv("SEOUL_OPENAPI_KEY", FAKE_KEY)
    st = CatalogStore(src)
    items = st.load_observations()
    items["s:9"] = _wrap(_obs("s:9", "seoul_openapi", f"제목 {FAKE_KEY}"))
    st.save_observations(items)
    snap.make_snapshot(src, tmp_path / "snap", now=NOW, command="cmd")
    assert FAKE_KEY not in (tmp_path / "snap" / "entries.json").read_text(encoding="utf-8")


def test_snapshot_md_contents(src, tmp_path):
    dst = tmp_path / "snap"
    snap.make_snapshot(src, dst, now=NOW, command="python scripts/snapshot_catalog.py --from A --to B")
    md = (dst / "SNAPSHOT.md").read_text(encoding="utf-8")
    for needle in ("서울 열린데이터광장", "공공누리 제1유형", "2026-10-09", "2건",
                   "스냅샷은 수집 시점 자료이며 이후 바뀌었을 수 있다",
                   "python scripts/snapshot_catalog.py --from A --to B"):
        assert needle in md


def test_refuses_when_no_seoul_observations(tmp_path):
    d = tmp_path / "c"
    CatalogStore(d).save_observations({"t:1": _wrap(_obs("t:1", "tavily_web", "○○"))})
    with pytest.raises(snap.SnapshotError):
        snap.make_snapshot(d, tmp_path / "snap", now=NOW, command="c")


def test_restore_refuses_existing_and_force_replaces(src, tmp_path):
    s = tmp_path / "snap"
    snap.make_snapshot(src, s, now=NOW, command="c")
    target = tmp_path / "var_catalog"
    snap.restore_snapshot(s, target)
    assert len(CatalogStore(target).load_entries()) == 2
    (target / "stale.txt").write_text("x", encoding="utf-8")
    with pytest.raises(snap.SnapshotError):
        snap.restore_snapshot(s, target)
    assert (target / "stale.txt").exists()
    snap.restore_snapshot(s, target, force=True)
    assert not (target / "stale.txt").exists()
    assert json.loads((target / "observations.json").read_text(encoding="utf-8"))


def test_cli_roundtrip(src, tmp_path, capsys):
    s, t = tmp_path / "snap", tmp_path / "restored"
    assert snap.main(["--from", str(src), "--to", str(s)]) == 0
    assert snap.main(["--restore", "--from", str(s), "--to", str(t)]) == 0
    assert snap.main(["--restore", "--from", str(s), "--to", str(t)]) == 1
    assert snap.main(["--restore", "--force", "--from", str(s), "--to", str(t)]) == 0


def test_generic_params_are_preserved_secret_params_are_not(src, tmp_path):
    st = CatalogStore(src)
    items = st.load_observations()
    url = f"https://example.invalid/e?uidKey=77&bnkey=123&key=123&Key=abc12345&serviceKey={FAKE_KEY}"
    items["s:7"] = _wrap(_obs("s:7", "seoul_openapi", "○○ 링크", url=url))
    st.save_observations(items)
    snap.make_snapshot(src, tmp_path / "snap", now=NOW, command="c")
    t = (tmp_path / "snap" / "observations.json").read_text(encoding="utf-8")
    assert "uidKey=77" in t and "bnkey=123" in t
    assert "key=123" in t  # 서울시 행사 페이지 게시물 번호(view.do?key=…) — 링크가 깨지면 안 된다
    assert "serviceKey=REDACTED" in t and FAKE_KEY not in t


def test_since_filters_ended_events_keeps_open_ended(src, tmp_path):
    st = CatalogStore(src)
    items = st.load_observations()
    items["e:old"] = _wrap(_obs("e:old", "seoul_openapi", "○○ 끝난 행사", end="2026-09-01"))
    items["e:open"] = _wrap(_obs("e:open", "seoul_openapi", "○○ 종료일 없음", end=None))
    st.save_observations(items)
    dst = tmp_path / "snap"
    r = snap.make_snapshot(src, dst, now=NOW, command="c", since="2026-10-10")
    out = CatalogStore(dst)
    titles = {e.title for e in out.load_entries()}
    assert "○○ 끝난 행사" not in titles and "○○ 종료일 없음" in titles
    assert "e:old" not in out.load_observations() and "e:open" in out.load_observations()
    assert r["dropped_entries"] == 1
    md = (dst / "SNAPSHOT.md").read_text(encoding="utf-8")
    assert "스냅샷 날짜에 끝나지 않은 행사만" in md and "1건" in md


def test_default_since_is_snapshot_day(src, tmp_path):
    st = CatalogStore(src)
    items = st.load_observations()
    items["e:old"] = _wrap(_obs("e:old", "seoul_openapi", "○○ 끝난 행사", end="2026-10-09"))
    st.save_observations(items)
    r = snap.make_snapshot(src, tmp_path / "snap", now=NOW, command="c")
    assert r["since"] == "2026-10-10" and r["dropped_entries"] == 1


def test_bare_key_param_kept_but_env_key_value_in_path_is_erased(src, tmp_path, monkeypatch):
    monkeypatch.setenv("SEOUL_OPENAPI_KEY", FAKE_KEY)
    st = CatalogStore(src)
    items = st.load_observations()
    url = f"https://example.invalid/{FAKE_KEY}/view.do?key=123"
    items["s:8"] = _wrap(_obs("s:8", "seoul_openapi", "○○ 게시물", url=url))
    st.save_observations(items)
    snap.make_snapshot(src, tmp_path / "snap", now=NOW, command="c")
    t = (tmp_path / "snap" / "observations.json").read_text(encoding="utf-8")
    assert "view.do?key=123" in t and FAKE_KEY not in t and "REDACTED/view.do" in t


def test_since_drops_open_ended_older_than_a_year_d23(src, tmp_path):
    st = CatalogStore(src)
    items = st.load_observations()
    for oid, start in (("e:old", "2025-10-09"), ("e:edge", "2025-10-10"), ("e:new", "2026-01-01")):
        o = _obs(oid, "seoul_openapi", f"○○ {oid}", end=None)
        items[oid] = _wrap(dataclasses.replace(o, schedule=Schedule(start_date=start, end_date=None)))
    st.save_observations(items)
    snap.make_snapshot(src, tmp_path / "snap", now=NOW, command="c", since="2026-10-10")
    titles = {e.title for e in CatalogStore(tmp_path / "snap").load_entries()}
    assert "○○ e:old" not in titles and {"○○ e:edge", "○○ e:new"} <= titles
