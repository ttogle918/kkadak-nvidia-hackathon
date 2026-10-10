"""실록 키워드 도구. 합성 XML·합성 동 목록·합성 독음 표만 쓴다(실데이터·네트워크 없음)."""

import json

import pytest

from domains.kcontext.ingest import sillok_keywords as sk
from domains.kcontext.regions import Region

HEAD = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE level2 SYSTEM "history.dtd">\n<level2 id="x">'


def l5(n, title, body, places=()):
    idx = "".join(f'<index type="지명">{p}</index>' for p in places)
    return (
        f'<level5 id="a_1_{n:03d}"><front><biblioData><title><mainTitle>{title}</mainTitle></title>'
        f'<date><dateOccured date="1400-01-02L0" type="서기"/></date></biblioData></front>'
        f"<text><content><paragraph>{body} {idx}</paragraph></content></text></level5>"
    )


def xml(*articles):
    return HEAD + '<level4 id="a_1"><front><biblioData><date></date></biblioData></front>' + "".join(articles) + "</level4></level2>"


@pytest.fixture
def src(tmp_path):
    d = tmp_path / "xml"
    d.mkdir()
    (d / "a.xml").write_text(xml(
        l5(1, "○○ 제목", "甲乙 丙丁 甲乙", ["甲乙", "丙丁"]),
        l5(2, "다른 제목", "甲乙 만", ["甲乙"]),
        l5(3, "甲乙 제목", "없음", ["戊己"]),
    ), encoding="utf-8")
    (d / "b.xml").write_text(xml(l5(1, "t", "丙丁", ["丙丁"])), encoding="utf-8")
    (d / "bad.xml").write_text(  # D14: ENTITY 선언 → 파일 통째로 건너뜀
        HEAD.replace('SYSTEM "history.dtd"', '[<!ENTITY e "x">]') + "</level2>", encoding="utf-8"
    )
    return d


def test_count_title_body_articles_and_meta(src):
    r = sk.count_keywords(src, {"r1": ["甲乙", "없는말"], "r2": ["丙丁"]})
    assert r["r1"]["甲乙"] == {"title": 1, "body": 2, "articles": 3}
    assert r["r1"]["없는말"] == {"title": 0, "body": 0, "articles": 0}
    assert r["r2"]["丙丁"] == {"title": 0, "body": 2, "articles": 2}
    assert r["_meta"]["articles"] == 4
    assert r["_meta"]["files"] == 3 and r["_meta"]["files_read"] == 2
    assert [f for f, _ in r["_meta"]["skipped_files"]] == ["bad.xml"]


def test_places_top_counts_articles(src):
    assert sk.top_place_tags(src, 2) == [("丙丁", 2), ("甲乙", 2)]
    assert sk.top_place_tags(src / "b.xml", 5) == [("丙丁", 1)]
    with pytest.raises(ValueError):
        sk.top_place_tags(src, 0)


def test_bad_src(tmp_path):
    with pytest.raises(ValueError):
        sk.top_place_tags(tmp_path / "없음")


# ---- 독음·후보 ----------------------------------------------------------------------------
READINGS = {"甲": ("가",), "乙": ("을", "일"), "丙": ("병",), "丁": ("정",), "戊": ("무",), "己": ("기",), "庚": ("경",)}


def region(rid, gu):
    return Region(rid, {"ko": gu, "en": rid}, (gu,), None, None, (gu,), ())


REGIONS = {"r1": region("r1", "○○구")}


def test_unihan_parse(tmp_path):
    f = tmp_path / "u.txt"
    f.write_text(
        "# 주석\nU+4E00\tkHangul\t일:0E\nU+4E01\tkHangul\t정:0E 딩:0N\nU+4E02\tkJapaneseOn\tX\nU+4E03\tkHangul\t???\n",
        encoding="utf-8",
    )
    assert sk.load_unihan_hangul(f) == {"一": ("일",), "丁": ("정", "딩")}


def test_combos_cap_and_missing():
    assert sk.reading_combos("甲乙", READINGS) == ["가을", "가일"]
    assert sk.reading_combos("甲辛", READINGS) == []  # 독음 없는 글자
    many = {c: ("a", "b") for c in "ABCDEF"}
    assert len(sk.reading_combos("ABCDEF", many)) == sk.MAX_COMBOS


@pytest.mark.parametrize(
    ("dong", "root"),
    [("가을동", "가을"), ("병1동", "병"), ("정1·2·3·4가동", "정"), ("정제2동", "정"), ("무", "무")],
)
def test_dong_root(dong, root):
    assert sk.dong_root(dong) == root


def test_candidates_match_ambiguous_and_missing():
    dongs = {"○○구": ["가을동", "병1동", "병2동"], "△△구": ["병동"], "□□구": ["가을3동"]}
    tags = [("甲乙", 10), ("丙", 5), ("戊己", 3), ("甲辛", 9), ("庚", 1)]
    out = sk.make_candidates(tags, dongs, READINGS, REGIONS)
    # 甲乙 → 가을/가일: ○○구(r1) 가을동 + □□구 가을3동. 두 구에 걸리므로 모호.
    assert out["r1"][0] == {"tag": "甲乙", "reading": "가을", "dong": "가을동", "articles": 10, "ambiguous": True}
    assert out["□□구"] == [{"tag": "甲乙", "reading": "가을", "dong": "가을3동", "articles": 10, "ambiguous": True}]
    # 丙 → 병: ○○구 병1동·병2동 + △△구 병동
    assert {(r["dong"], r.get("ambiguous")) for r in out["r1"] if r["tag"] == "丙"} == {
        ("병1동", True), ("병2동", True),
    }
    assert out["△△구"][0]["tag"] == "丙"
    # 독음 없음(辛)·일치 없음(戊己, 庚)은 후보가 아니다
    assert not [r for rows in out.values() for r in rows if r["tag"] in ("甲辛", "戊己", "庚")]
    # 건수 내림차순
    assert [r["articles"] for r in out["r1"]] == sorted((r["articles"] for r in out["r1"]), reverse=True)


def test_candidates_unambiguous_has_no_flag():
    out = sk.make_candidates([("丙", 2)], {"○○구": ["병동"]}, READINGS, REGIONS)
    assert out == {"r1": [{"tag": "丙", "reading": "병", "dong": "병동", "articles": 2}]}


# ---- CLI ----------------------------------------------------------------------------------
def test_cli_count_places_candidates(src, tmp_path, capsys):
    cand = tmp_path / "c.json"
    cand.write_text(json.dumps({"r1": ["甲乙"]}), encoding="utf-8")
    out = tmp_path / "out" / "count.json"
    assert sk.main(["count", "--src", str(src), "--candidates", str(cand), "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["r1"]["甲乙"]["articles"] == 3

    assert sk.main(["places", "--src", str(src), "--top", "1"]) == 0
    assert json.loads(capsys.readouterr().out) == [{"tag": "丙丁", "articles": 2}]

    dongs, rd = tmp_path / "d.json", tmp_path / "u.txt"
    dongs.write_text(json.dumps({"○○구": ["병정동"]}), encoding="utf-8")
    rd.write_text("U+4E19\tkHangul\t병:0E\nU+4E01\tkHangul\t정:0E\n", encoding="utf-8")
    # 합성 독음 표의 글자(丙=U+4E19, 丁=U+4E01)
    assert sk.main(["candidates", "--src", str(src), "--dongs", str(dongs), "--readings", str(rd)]) == 0
    got = json.loads(capsys.readouterr().out)
    (rows,) = got.values()
    assert rows[0]["tag"] == "丙丁" and rows[0]["dong"] == "병정동" and rows[0]["count"]["articles"] == 2


def test_cli_errors_and_never_writes_region_files(src, tmp_path, capsys):
    assert sk.main(["count", "--src", str(src), "--candidates", str(tmp_path / "없음.json")]) == 2
    bad = tmp_path / "bad.json"
    bad.write_text('["x"]', encoding="utf-8")
    assert sk.main(["count", "--src", str(src), "--candidates", str(bad)]) == 2
    ok = tmp_path / "ok.json"
    ok.write_text("{}", encoding="utf-8")
    target = tmp_path / "data" / "regions" / "jongno.json"
    assert sk.main(["count", "--src", str(src), "--candidates", str(ok), "--out", str(target)]) == 2
    assert not target.exists()
    capsys.readouterr()


# ---- dongs 변환 -----------------------------------------------------------------------------
CODES = {"11110": "종로구", "11680": "강남구", "11440": "마포구", "11140": "중구"}


def test_dongs_from_rows_latest_quarter_only():
    rows = [
        {"STDR_YYQU_CD": "20262", "ADSTRD_CD": "11110001", "ADSTRD_CD_NM": "○동"},
        {"STDR_YYQU_CD": "20262", "ADSTRD_CD": "11110002", "ADSTRD_CD_NM": "○동"},  # 중복
        {"STDR_YYQU_CD": "20262", "ADSTRD_CD": "11680003", "ADSTRD_CD_NM": "△동"},
        {"STDR_YYQU_CD": "20262", "ADSTRD_CD": "99999001", "ADSTRD_CD_NM": "서울 밖"},
        {"STDR_YYQU_CD": "20261", "ADSTRD_CD": "11140004", "ADSTRD_CD_NM": "옛 분기"},
    ]
    assert sk.dongs_from_seoul_rows(rows, CODES) == {"종로구": ["○동"], "강남구": ["△동"]}


def test_cli_dongs(tmp_path, capsys):
    f = tmp_path / "s.json"
    f.write_text(json.dumps({"Svc": {"row": [{"ADSTRD_CD": "11440001", "ADSTRD_CD_NM": "○동"}]}}), encoding="utf-8")
    g = tmp_path / "g.json"
    g.write_text(json.dumps(CODES), encoding="utf-8")
    assert sk.main(["dongs", "--from-seoul", str(f), "--gu-codes", str(g)]) == 0
    assert json.loads(capsys.readouterr().out) == {"마포구": ["○동"]}
    f.write_text("{}", encoding="utf-8")
    assert sk.main(["dongs", "--from-seoul", str(f), "--gu-codes", str(g)]) == 2
