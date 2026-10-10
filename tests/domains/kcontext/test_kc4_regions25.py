"""실제 지역 폴더 25개 검사 (T414, D28). 기존 4개 구 기대값은 fixtures/regions4 로 따로 고정."""
from pathlib import Path

from domains.kcontext.regions import load_regions

REPO = Path(__file__).resolve().parents[3]
OLD4 = {"gangnam", "jongno", "jung", "mapo"}


def test_real_folder_has_25_unique_gu(monkeypatch):
    monkeypatch.delenv("KC_DATA_DIR", raising=False)
    regs = load_regions()
    assert len(regs) == 25
    gus = [g for r in regs.values() for g in r.gu]
    assert len(gus) == len(set(gus)) == 25
    assert all(g.endswith("구") for g in gus)
    assert OLD4 <= set(regs)


def test_new_regions_have_no_sillok_keywords_and_name_keyword(monkeypatch):
    monkeypatch.delenv("KC_DATA_DIR", raising=False)
    for rid, r in load_regions().items():
        if rid in OLD4:
            continue
        assert r.sillok_keywords == [] or r.sillok_keywords == ()
        assert list(r.keywords) == list(r.gu)
        assert r.bbox is None and r.center is None


def test_old4_files_identical_to_fixture():
    for rid in OLD4:
        a = (REPO / "domains/kcontext/data/regions" / f"{rid}.json").read_bytes()
        b = (REPO / "tests/fixtures/regions4" / f"{rid}.json").read_bytes()
        assert a == b


def test_empty_sillok_keywords_region_not_indexed():
    from domains.kcontext.ingest import sillok
    regs = load_regions()
    empty = [r for r in regs.values() if not r.sillok_keywords]
    assert len(empty) == 21
    assert sillok.regions_in_text("강동구 강동", {r.id: r for r in empty}, field="sillok_keywords") == []
