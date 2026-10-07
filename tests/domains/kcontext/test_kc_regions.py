import json
import re
from pathlib import Path

import pytest

from domains.kcontext import paths
from domains.kcontext.regions import (
    RegionConfigError,
    load_regions,
    regions_at,
    regions_in_text,
)

REPO = Path(__file__).resolve().parents[3]


def _write(d: Path, rid: str, **over):
    body = {
        "id": rid, "name": {"ko": "가나", "en": "Ga"}, "gu": ["다구"], "bbox": None,
        "center": None, "keywords": ["가나"], "sillok_keywords": [],
    }
    body.update(over)
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{rid}.json").write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")


def test_real_regions_load(monkeypatch):
    monkeypatch.delenv("KC_DATA_DIR", raising=False)
    regs = load_regions()
    assert set(regs) == {"gangnam", "jongno", "jung", "mapo"}
    assert all(r.bbox is None and r.center is None for r in regs.values())


def test_synthetic_bbox_and_lookup(tmp_path):
    _write(tmp_path, "region_a", bbox=[10, 20, 11, 21], center=[10.5, 20.5], synthetic=True)
    _write(tmp_path, "region_b")
    regs = load_regions(tmp_path)
    assert list(regs) == ["region_a", "region_b"]
    assert regions_at(10.5, 20.5, regs) == ["region_a"]
    assert regions_at(10, 20, regs) == ["region_a"]  # 경계 포함
    assert regions_at(12, 20.5, regs) == []


def test_text_match(tmp_path):
    _write(tmp_path, "region_a", keywords=["가나"], sillok_keywords=["라마"])
    _write(tmp_path, "region_b", keywords=["바사", "가나"])
    regs = load_regions(tmp_path)
    assert regions_in_text("ｘ가나ｘ", regs) == ["region_a", "region_b"]
    assert regions_in_text("바사", regs) == ["region_b"]
    assert regions_in_text("라마", regs) == []
    assert regions_in_text("라마", regs, field="sillok_keywords") == ["region_a"]


@pytest.mark.parametrize(
    "over",
    [
        {"id": "other"},
        {"id": "Bad-Id"},
        {"bbox": [11, 20, 10, 21]},
        {"bbox": [1, 2, 3]},
        {"center": [1]},
        {"extra": 1},
        {"keywords": []},
        {"keywords": [""]},
        {"name": {"ko": "가"}},
    ],
)
def test_bad_config(tmp_path, over):
    _write(tmp_path, "region_a", **over)
    with pytest.raises(RegionConfigError, match=r"region_a\.json"):
        load_regions(tmp_path)


def test_empty_and_missing_dir(tmp_path):
    with pytest.raises(RegionConfigError):
        load_regions(tmp_path)
    with pytest.raises(RegionConfigError):
        load_regions(tmp_path / "none")


def test_kc_data_dir_env(tmp_path, monkeypatch):
    monkeypatch.setenv("KC_DATA_DIR", str(tmp_path / "none"))
    assert paths.data_dir() == tmp_path / "none"
    with pytest.raises(RegionConfigError):
        load_regions()


def test_paths_defaults(monkeypatch, tmp_path):
    monkeypatch.delenv("KC_VAR_DIR", raising=False)
    monkeypatch.delenv("KC_DATA_DIR", raising=False)
    assert paths.var_dir() == paths.repo_root() / "var"
    assert paths.repo_root() == REPO
    monkeypatch.setenv("KC_VAR_DIR", str(tmp_path))
    assert paths.var_dir() == tmp_path


def test_demo_situation_shape():
    d = json.loads((REPO / "domains/kcontext/data/situations/demo_day1.json").read_text("utf-8"))
    assert d["trip"] == {"from": "2026-10-15", "to": "2026-10-18"}
    assert all(a["lat"] is None and a["lng"] is None for a in d["anchors"])
    assert d["free_slots"][0]["near"] == "익선동"


def test_no_region_literals_in_py():
    pat = re.compile("중구|마포|강남|종로|을지로")
    for p in (REPO / "domains").rglob("*.py"):
        assert not pat.search(p.read_text("utf-8")), p
