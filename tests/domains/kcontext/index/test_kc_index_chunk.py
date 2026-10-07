import pytest

from domains.kcontext.index import chunk_text, make_chunk_id


def test_paragraphs_split_and_order():
    assert chunk_text("○○ 행차\n\n\n○○ 물길\n \n끝") == ["○○ 행차", "○○ 물길", "끝"]


def test_empty_and_blank():
    assert chunk_text("") == []
    assert chunk_text("  \n\n  ") == []


def test_sentence_boundary_packing():
    text = "가나다라다. 마바사아다. 자차카타다."
    out = chunk_text(text, max_chars=12)
    assert out == ["가나다라다.", "마바사아다.", "자차카타다."]
    assert all(len(c) <= 12 for c in out)


def test_hard_cut():
    out = chunk_text("가" * 25, max_chars=10)
    assert out == ["가" * 10, "가" * 10, "가" * 5]


def test_max_chars_invalid():
    with pytest.raises(ValueError):
        chunk_text("x", max_chars=0)


def test_chunk_id_stable_and_distinct():
    a = make_chunk_id("s", "loc", "t")
    assert a == make_chunk_id("s", "loc", "t")
    assert len(a) == 16
    assert a != make_chunk_id("s", "loc2", "t")
    assert make_chunk_id("ab", "c", "t") != make_chunk_id("a", "bc", "t")
