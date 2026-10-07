"""실록 수집기. 실제 기사 발췌 fixture(tests/fixtures/kcontext/sillok) + tmp_path 합성 XML(거부 확인용)."""

import json
from pathlib import Path

import pytest

from domains.kcontext.index import LocalIndex
from domains.kcontext.ingest import sillok
from domains.kcontext.ingest.sillok import (
    SillokFormatError,
    doctype_problem,
    ingest,
    parse_file,
    to_chunks,
)
from domains.kcontext.regions import load_regions

FIX = Path(__file__).resolve().parents[3] / "fixtures" / "kcontext" / "sillok"
OK_HEAD = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE level2 SYSTEM "history.dtd">\n<level2 id="x">'
MIN = '<level4 id="a_1"><front><biblioData><date><dateOccured date="1400-01-02L0" type="서기"/><dateOccured type="재위연도">태종 1년 1월 2일</dateOccured></date></biblioData></front>{l5}</level4></level2>'
L5 = '<level5 id="a_1_001"><front><biblioData><title><mainTitle>합성 제목</mainTitle></title><date><dateOccured date="1400-01-02L0" type="서기"/></date></biblioData></front><text><content><paragraph>合成 本文 <index type="지명">甲乙</index> 끝。</paragraph></content></text></level5>'


def write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


# ---- D13: DOCTYPE ------------------------------------------------------------------------
@pytest.mark.parametrize(
    "head",
    [
        '<level2 id="x">',  # DOCTYPE 없음
        OK_HEAD,
        OK_HEAD.replace("\n<!DOCTYPE", "\n<!-- 주석 -->\n<!DOCTYPE"),
        '<!DOCTYPE level1 SYSTEM \'history.dtd\'>\n<level1 id="x">',
    ],
)
def test_doctype_allowed(head):
    assert doctype_problem(head) is None


@pytest.mark.parametrize(
    "head",
    [
        '<!DOCTYPE a [<!ENTITY x "y">]>\n<a/>',  # 내부 서브셋 + ENTITY
        '<!DOCTYPE a SYSTEM "history.dtd" [<!ELEMENT a ANY>]>\n<a/>',  # 외부 선언 + 내부 서브셋
        '<!DOCTYPE a PUBLIC "-//X//EN" "history.dtd">\n<a/>',
        '<!DOCTYPE a SYSTEM "http://example.invalid/x.dtd">\n<a/>',  # URL
        '<!DOCTYPE a SYSTEM "../x.dtd">\n<a/>',  # 경로
        '<!DOCTYPE a SYSTEM "history.dtd">\n<!DOCTYPE b SYSTEM "history.dtd">\n<a/>',  # 둘
        '<!-- <!DOCTYPE a SYSTEM "x.dtd"> -->\n<!DOCTYPE a [<!ENTITY x "y">]>\n<a/>',  # 주석에 숨긴 가짜 DOCTYPE
        "<!-- 닫히지 않음 " + "x" * 100,
        " " * 5000,  # 루트 요소가 4KB 안에 없다
        '<!DOCTYPE r SYSTEM "<!--" [<!ENTITY e "-->a.dtd">]><r>&e;</r>',  # 따옴표 안의 '<!--' 로 주석 제거를 속임
        '<!DOCTYPE r SYSTEM "<?" [<!ENTITY e "?>a.dtd">]><r>&e;</r>',
        '<?xml version="1.0" encoding="cp037"?>\n<a/>',  # UTF-8 이 아닌 인코딩 선언
        '<!DOCTYPE a SYSTEM "a..dtd">\n<a/>',
    ],
)
def test_doctype_rejected(head):
    assert doctype_problem(head) is not None


def test_oversized_file_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(sillok, "MAX_FILE_BYTES", 100)
    with pytest.raises(SillokFormatError, match="너무 크다"):
        list(parse_file(write(tmp_path, "a.xml", OK_HEAD + MIN.format(l5=L5))))


def test_bad_article_id_is_not_used(tmp_path):
    l5 = L5.replace('id="a_1_001"', 'id="../x?y#z"')
    [a] = list(parse_file(write(tmp_path, "a.xml", OK_HEAD + MIN.format(l5=l5))))
    assert a.article_id == "" and a.url == ""


def test_parse_file_rejects_entity_without_parsing(tmp_path):
    p = write(tmp_path, "evil.xml", '<?xml version="1.0"?>\n<!DOCTYPE a [<!ENTITY x "y">]>\n<a>&x;</a>')
    with pytest.raises(SillokFormatError, match="내부 서브셋"):
        list(parse_file(p))


def test_parse_file_never_reads_external_dtd(tmp_path):
    (tmp_path / "history.dtd").write_text('<!ENTITY lol "LOL">', encoding="utf-8")
    p = write(tmp_path, "a.xml", OK_HEAD + MIN.format(l5=L5.replace("끝", "&lol;")))
    with pytest.raises(SillokFormatError, match="구문"):  # 외부 DTD 를 읽지 않으니 &lol; 은 정의되지 않은 엔티티
        list(parse_file(p))


def test_parse_file_symlink_refused(tmp_path):
    real = write(tmp_path, "r.xml", OK_HEAD + MIN.format(l5=L5))
    link = tmp_path / "l.xml"
    link.symlink_to(real)
    with pytest.raises(SillokFormatError, match="심볼릭"):
        list(parse_file(link))


# ---- 파싱 -----------------------------------------------------------------------------------
def test_parse_fixture_article():
    a = next(parse_file(FIX / "sample.xml"))
    assert a.article_id == "waa_10107017_001"
    assert a.king == "태조"
    assert a.calendar == "lunar"  # 날짜 속성은 자식 없는 요소 — 'or' 로 읽으면 빈 값이 되던 자리
    assert a.date_label.startswith("태조 1년 7월 17일(음력)")
    assert a.url == "https://sillok.history.go.kr/id/waa_10107017_001"
    assert a.title and a.text_ko is None and a.text_orig and "壽昌宮" in a.text_orig
    assert "壽昌宮" in a.places


def test_parse_synthetic(tmp_path):
    p = write(tmp_path, "a.xml", OK_HEAD + MIN.format(l5=L5))
    [a] = list(parse_file(p))
    assert (a.article_id, a.king, a.title, a.calendar) == ("a_1_001", "태종", "합성 제목", "lunar")
    assert a.text_orig == "合成 本文 甲乙 끝。" and a.places == ("甲乙",)


def test_parse_marks_missing_id_and_unknown_calendar(tmp_path):
    l5 = L5.replace('id="a_1_001"', "").replace('date="1400-01-02L0"', 'date="이상한값"')
    [a] = list(parse_file(write(tmp_path, "a.xml", OK_HEAD + MIN.format(l5=l5))))
    assert a.article_id == ""
    l5b = L5.replace('date="1400-01-02L0"', 'date="이상한값"')
    [b] = list(parse_file(write(tmp_path, "b.xml", OK_HEAD + MIN.format(l5=l5b))))
    assert b.calendar == "unknown" and "역법 미확인" in b.date_label


# ---- 청크 -----------------------------------------------------------------------------------
def test_to_chunks_fields():
    regions = load_regions()
    a = next(parse_file(FIX / "sample_jongno.xml"))
    cs = to_chunks(a, collected_at="2026-10-07", regions=regions)
    assert cs and all(c.tier == "S" and c.name == "조선왕조실록" and c.source_id == f"sillok:{a.article_id}" for c in cs)
    assert "jongno" in cs[0].regions
    c = cs[0]
    assert c.text.startswith(a.title + "\n")  # 청크 텍스트 = 제목+본문
    assert not c.quote.startswith(a.title)  # 인용은 원문 구절만(제목은 편집 요약)
    assert c.meta["lang"] == "orig" and c.meta["title_is_summary"] == "true" and c.meta["calendar"] == "lunar"
    assert a.article_id in c.locator and "(음력)" in c.locator
    assert c.url.endswith(a.article_id)


def test_long_article_splits_with_numbered_locators(tmp_path):
    long = "。 ".join(f"合成文章{i}" * 12 for i in range(60))
    l5 = L5.replace("合成 本文 <index", long + " <index")
    [a] = list(parse_file(write(tmp_path, "a.xml", OK_HEAD + MIN.format(l5=l5))))
    cs = to_chunks(a, collected_at="2026-10-07", regions=load_regions())
    assert len(cs) > 1
    assert cs[0].locator.endswith(f"(1/{len(cs)})") and len({c.chunk_id for c in cs}) == len(cs)
    assert all(len(c.text) <= 900 for c in cs)


def test_to_chunks_empty_body_or_id():
    from domains.kcontext.ingest.sillok import SillokArticle

    base = {"king": None, "date_label": "x", "title": "t", "text_ko": None, "url": "", "calendar": "unknown"}
    assert to_chunks(SillokArticle("id", text_orig=None, **base), collected_at="2026-10-07", regions={}) == []
    assert to_chunks(SillokArticle("", text_orig="본문", **base), collected_at="2026-10-07", regions={}) == []


# ---- ingest ---------------------------------------------------------------------------------
def test_ingest_fixture_all_mode_and_search():
    with LocalIndex(":memory:") as idx:
        r = ingest(FIX, idx, collected_at="2026-10-07", regions=load_regions(), mode="all")
        assert (r.files, r.articles, r.skipped_files, r.skipped_articles) == (5, 5, (), 0)
        assert r.chunks == idx.count() and r.matched == 5
        hits = idx.search("鍾樓", regions=["jongno"])
        assert hits and hits[0].chunk.tier == "S" and "鍾樓" in hits[0].chunk.text
        # 지역 키워드와 같은 지명 태그만 사전에 들어간다
        assert {a.region for a in idx.aliases_for("鍾樓")} <= {"jongno"}


def test_ingest_regions_mode_skips_unmatched():
    with LocalIndex(":memory:") as idx:
        r = ingest(FIX, idx, collected_at="2026-10-07", regions=load_regions(), mode="regions")
        assert r.files == 5 and r.matched == 4 and r.skipped_articles == 1  # sample.xml(태조 즉위)은 어느 구와도 안 맞는다
        assert idx.search("壽昌宮") == []


def test_ingest_rerun_is_idempotent():
    with LocalIndex(":memory:") as idx:
        regions = load_regions()
        ingest(FIX, idx, collected_at="2026-10-07", regions=regions, mode="all")
        n = idx.count()
        ingest(FIX, idx, collected_at="2026-10-08", regions=regions, mode="all")
        assert idx.count() == n


def test_ingest_skips_bad_file_and_reports(tmp_path):
    write(tmp_path, "good.xml", OK_HEAD + MIN.format(l5=L5))
    write(tmp_path, "bad.xml", '<!DOCTYPE a [<!ENTITY x "y">]>\n<a/>')
    write(tmp_path, "broken.xml", OK_HEAD + "<level4><level5")
    with LocalIndex(":memory:") as idx:
        r = ingest(tmp_path, idx, collected_at="2026-10-07", regions=load_regions(), mode="all")
        assert r.files == 1 and r.chunks == 1
        assert {n for n, _ in r.skipped_files} == {"bad.xml", "broken.xml"}
        assert idx.count() == 1


def test_ingest_validates_args(tmp_path):
    with LocalIndex(":memory:") as idx:
        with pytest.raises(ValueError, match="YYYY"):
            ingest(tmp_path, idx, collected_at="2026-13-40", regions={})
        with pytest.raises(ValueError, match="폴더"):
            ingest(tmp_path / "없음", idx, collected_at="2026-10-07", regions={})
        with pytest.raises(ValueError):
            ingest(tmp_path, idx, collected_at="2026-10-07", regions={}, mode="x")  # type: ignore[arg-type]


# ---- CLI ------------------------------------------------------------------------------------
def test_cli_ok_and_exit_codes(tmp_path, capsys):
    db = str(tmp_path / "k.db")
    rc = sillok.main(["--src", str(FIX), "--db", db, "--collected-at", "2026-10-07", "--mode", "all"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["files"] == 5 and out["skipped_files"] == []
    empty = tmp_path / "empty"
    empty.mkdir()
    assert sillok.main(["--src", str(empty), "--db", db, "--collected-at", "2026-10-07"]) == 2
    assert sillok.main(["--src", str(FIX), "--db", db, "--collected-at", "어제"]) == 2


# ---- 원본의 서로게이트 쌍 문자 참조 ------------------------------------------------------------
def test_surrogate_pair_refs_are_joined(tmp_path):
    l5 = L5.replace("合成 本文", "李&#55381;&#56892; 本文")  # U+2014B 조합 쌍
    [a] = list(parse_file(write(tmp_path, "a.xml", OK_HEAD + MIN.format(l5=l5))))
    assert a.text_orig.startswith("李" + chr(0x10000 + ((55381 - 0xD800) << 10) + (56892 - 0xDC00)))


def test_unpaired_surrogate_ref_still_rejected(tmp_path):
    l5 = L5.replace("合成 本文", "李&#55381; 本文")
    with pytest.raises(SillokFormatError, match="구문"):
        list(parse_file(write(tmp_path, "a.xml", OK_HEAD + MIN.format(l5=l5))))
