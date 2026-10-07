import json

import pytest

from domains.kcontext.places import PlacesConfigError, default_path, load_places


def good(**kw):
    d = {"name": "○○궁", "aliases": ["○○ Palace"], "lat": 37.5, "lng": 127.0,
         "source": "합성", "verified_at": "2026-10-07", "note": ""}  # fmt: skip
    d.update(kw)
    return d


def write(tmp_path, rows):
    p = tmp_path / "p.json"
    p.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return p


def test_lookup_by_name_alias_and_normalization(tmp_path):
    book = load_places(write(tmp_path, [good()]))
    assert book.lookup("○○궁").lat == 37.5
    assert book.lookup("  ○○ palace ").lng == 127.0  # 공백·대소문자 무시
    assert book.lookup("없는곳") is None and book.lookup(None) is None


def test_default_file_loads_and_is_verified():
    book = load_places()
    assert len(book) >= 4 and default_path().is_file()
    for p in book.places:
        assert 33 <= p.lat <= 39 and 124 <= p.lng <= 132 and p.source and p.verified_at


@pytest.mark.parametrize(
    "row",
    [
        good(lat=91), good(lng=-181), good(lat="37.5"), good(lat=True), good(verified_at="어제"),
        good(extra=1), good(aliases="x"), good(name=""), good(aliases=[""]),
    ],
)  # fmt: skip
def test_bad_rows_rejected(tmp_path, row):
    with pytest.raises(PlacesConfigError):
        load_places(write(tmp_path, [row]))


def test_missing_key_duplicate_and_shape(tmp_path):
    row = good()
    del row["note"]
    with pytest.raises(PlacesConfigError, match="빠진"):
        load_places(write(tmp_path, [row]))
    with pytest.raises(PlacesConfigError, match="중복"):
        load_places(write(tmp_path, [good(), good(name="다른곳", aliases=["○○ PALACE"])]))
    with pytest.raises(PlacesConfigError, match="중복"):
        load_places(write(tmp_path, [good(), good()]))
    with pytest.raises(PlacesConfigError):
        load_places(write(tmp_path, {"a": 1}))
    with pytest.raises(PlacesConfigError, match="읽을 수 없다"):
        load_places(tmp_path / "none.json")
