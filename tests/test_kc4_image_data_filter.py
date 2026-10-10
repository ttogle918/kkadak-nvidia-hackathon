"""T423 — 이미지 데이터 필터: 서울 API 유래만 · 끝난 행사 보존 · 키 없음 · 자동 좌표 origin 필터. 값은 합성."""

import importlib.util
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from domains.kcontext.catalog.model import Evidence, Observation, Schedule, Venue
from domains.kcontext.catalog.rules import KST
from domains.kcontext.catalog.store import CatalogStore

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("snapshot_catalog", ROOT / "scripts" / "snapshot_catalog.py")
snap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(snap)

NOW = datetime(2026, 10, 10, 12, 0, tzinfo=KST)
FAKE_KEY = "FAKEKEYVALUE1234567890"
SOURCES = ("seoul_openapi", "junggu_site", "gangnam_site", "tourapi_kto", "report")


def _obs(obs_id, source_id, title, end="2026-10-16"):
    ev = Evidence(source_id=source_id, source_name=f"○○ {source_id}", kind="official_api",
                  url=f"https://example.invalid/{obs_id}?apikey={FAKE_KEY}&a=1", quote="인용",
                  origin=obs_id, collected_at="2026-10-09")
    return Observation(
        obs_id=obs_id, title=title, external_ids=(f"{source_id}:{obs_id}",), evidence=ev,
        venue=Venue(name="○○ 홀", district="중구", district_basis="source_gu", in_target="yes"),
        schedule=Schedule(start_date="2026-01-01" if end < "2026-10-10" else "2026-10-16", end_date=end))


def _wrap(o):
    return {"observation": o, "source_id": o.evidence.source_id,
            "first_seen_at": "2026-10-09T10:00", "last_seen_at": "2026-10-09T10:00"}


@pytest.fixture
def src(tmp_path):
    d = tmp_path / "catalog.all"
    items = [_obs(f"{s}:1", s, f"○○ {s} 행사") for s in SOURCES]
    items.append(_obs("seoul_openapi:2", "seoul_openapi", "○○ 끝난 서울 행사", end="2026-03-01"))
    CatalogStore(d).save_observations({o.obs_id: _wrap(o) for o in items})
    CatalogStore(d).save_runs({
        "seoul_openapi": {"last_success_at": "2026-10-09T10:00", "last_error": f"GET /{FAKE_KEY}/json"},
        "tourapi_kto": {"last_success_at": "2026-10-09T10:00"},
    })
    return d


def test_only_seoul_api_kept_and_ended_preserved(src, tmp_path, monkeypatch):
    monkeypatch.setenv("SEOUL_OPENAPI_KEY", FAKE_KEY)
    dst = tmp_path / "out"
    r = snap.make_snapshot(src, dst, now=NOW, command="c", keep_ended=True)
    assert r["observations"] == 2
    out = CatalogStore(dst)
    obs = out.load_observations()
    assert {v["observation"].evidence.source_id for v in obs.values()} == {"seoul_openapi"}
    entries = out.load_entries()
    assert {e.title for e in entries} == {"○○ seoul_openapi 행사", "○○ 끝난 서울 행사"}  # 끝난 행사 보존
    for e in entries:
        assert all(ev.source_id == "seoul_openapi" for ev in e.evidence)
    assert set(out.load_runs()) == {"seoul_openapi"}
    text = "".join(p.read_text(encoding="utf-8") for p in dst.glob("*.json"))
    assert '"web"' not in text and "fetched_from" not in text
    assert FAKE_KEY not in text and f"apikey={FAKE_KEY}" not in text
    for other in ("junggu_site", "gangnam_site", "tourapi_kto", "report"):
        assert other not in text


def test_default_still_drops_ended(src, tmp_path):
    snap.make_snapshot(src, tmp_path / "out", now=NOW, command="c")
    titles = {e.title for e in CatalogStore(tmp_path / "out").load_entries()}
    assert "○○ 끝난 서울 행사" not in titles


def test_keep_ended_cli_flag(src, tmp_path):
    dst = tmp_path / "out"
    assert snap.main(["--from", str(src), "--to", str(dst), "--keep-ended"]) == 0
    assert "--keep-ended" in (dst / "SNAPSHOT.md").read_text(encoding="utf-8")


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv 없음")
def test_build_script_filters_places_and_fails_without_catalog(src, tmp_path):
    index = tmp_path / "kcontext.db"
    index.write_bytes(b"x")
    places = tmp_path / "auto_places.json"
    base = {"aliases": [], "lat": 37.5, "lng": 127.0, "source": "s", "verified_at": "2026-10-10",
            "note": "n", "auto": True}
    places.write_text(json.dumps([
        {**base, "name": "서울만", "origin": ["seoul_openapi"]},
        {**base, "name": "섞임", "origin": ["seoul_openapi", "tourapi_kto"]},
        {**base, "name": "타출처", "origin": ["tourapi_kto"]},
        {**base, "name": "없음"},
    ]), encoding="utf-8")
    out = tmp_path / "image-data"
    env = {**os.environ, "KC_IMAGE_OUT": str(out), "KC_IMAGE_CATALOG_SRC": str(src),
           "KC_IMAGE_INDEX_SRC": str(index), "KC_IMAGE_PLACES_SRC": str(places)}
    r = subprocess.run(["bash", str(ROOT / "scripts" / "build_image_data.sh")], env=env,
                       capture_output=True, text=True, timeout=300, check=False)
    assert r.returncode == 0, r.stderr
    kept = json.loads((out / "places" / "auto_places.json").read_text(encoding="utf-8"))
    assert [p["name"] for p in kept] == ["서울만"]
    assert (out / "index" / "kcontext.db").read_bytes() == b"x"
    assert (out / "catalog" / "search_index.json").exists()
    assert not (out / "catalog" / "SNAPSHOT.md").exists()

    env["KC_IMAGE_CATALOG_SRC"] = str(tmp_path / "없음")
    r = subprocess.run(["bash", str(ROOT / "scripts" / "build_image_data.sh")], env=env,
                       capture_output=True, text=True, timeout=60, check=False)
    assert r.returncode != 0 and "조용히" in r.stderr
