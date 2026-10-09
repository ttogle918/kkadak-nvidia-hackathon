"""언급 근거(rationale.py) — 고정 템플릿 + 데이터 값. 합성 입력."""

import json

from domains.kcontext.pipeline.rationale import COVERAGE_NOTE_EN, mention_rationale
from domains.kcontext.story import COVERAGE_NOTE

ROW = {"anchor": {"name": "○○궁"}, "terms": ["○○궁", "別名"], "found_articles": 7, "found_truncated": False}
M = {"matched_term": "○○궁", "matched_in": "title", "tier": "S", "lang": "orig", "locator": "L1", "date_label": "태종 1년 1월 2일(음력)",
     "url": "https://x.invalid/a", "source": {"id": "sillok:a1", "name": "조선왕조실록", "locator": "L1", "collected_at": "2026-10-07"}}  # fmt: skip


def bi(x):
    return isinstance(x, dict) and set(x) == {"ko", "en"} and all(isinstance(s, str) for s in x.values())


def test_shape_keys_tones_and_bilingual():
    r = mention_rationale("mention:story_a1", ROW, M, 2)
    assert r["card_id"] == "mention:story_a1"
    assert [(c["key"], c["tone"]) for c in r["chips"]] == [("match", "old"), ("pick", "now"), ("src", "old"), ("scope", "now")]
    assert set(r["items"]) == {"match", "pick", "src", "scope"}
    for c in r["chips"]:
        assert bi(c["label"])
    for it in r["items"].values():
        assert bi(it["title"]) and bi(it["text"]) and len(it["rows"]) <= 12
        assert all(bi(x["k"]) and bi(x["v"]) for x in it["rows"])
        assert all(len(s) <= 300 for s in (it["title"]["ko"], it["title"]["en"], it["text"]["ko"], it["text"]["en"]))
    json.dumps(r, ensure_ascii=False)


def test_chip_labels_and_rows():
    r = mention_rationale("mention:s", ROW, M, 2)
    lab = {c["key"]: c["label"] for c in r["chips"]}
    assert lab["match"] == {"ko": "◆ 검색어 일치: ○○궁", "en": "◆ Matched term: ○○궁"}
    assert lab["pick"]["ko"] == "● 후보 7건 중 선택" and lab["pick"]["en"] == "● Picked from 7 candidates"
    assert lab["src"]["ko"] == "◆ 출처 등급 S · 국역 없음"
    rows = {x["k"]["ko"]: x["v"] for x in r["items"]["match"]["rows"]}
    assert rows["일치 위치"]["ko"] == "한국사DB 한글 요약 제목" and rows["별칭 여부"]["ko"] == "아니오"
    assert rows["검색어"]["ko"] == "○○궁, 別名"
    pick = {x["k"]["ko"]: x["v"]["ko"] for x in r["items"]["pick"]["rows"]}
    assert pick == {"후보 수": "7", "검색 상한 도달": "아니오", "주입 검사 제외": "2"}
    src = {x["k"]["ko"]: x["v"] for x in r["items"]["src"]["rows"]}
    assert src["날짜 표기"]["ko"] == "태종 1년 1월 2일(음력)" == src["날짜 표기"]["en"]  # 그대로
    assert src["링크"]["ko"] == "있음" and src["수집일"]["ko"] == "2026-10-07"


def test_truncated_alias_body_and_no_link():
    row = {**ROW, "found_articles": 200, "found_truncated": True}
    m = {**M, "matched_term": "別名", "matched_in": "body", "url": ""}
    r = mention_rationale("mention:s", row, m, 0)
    assert r["chips"][1]["label"]["ko"] == "● 후보 200건 이상 중 선택"
    assert r["chips"][1]["label"]["en"] == "● Picked from 200+ candidates"
    rows = {x["k"]["ko"]: x["v"]["ko"] for x in r["items"]["match"]["rows"]}
    assert rows["일치 위치"] == "원문 본문" and rows["별칭 여부"] == "예"
    assert {x["k"]["ko"]: x["v"]["ko"] for x in r["items"]["pick"]["rows"]}["검색 상한 도달"] == "예"
    assert {x["k"]["ko"]: x["v"]["ko"] for x in r["items"]["src"]["rows"]}["링크"] == "없음"


def test_scope_is_coverage_note_and_empty_value_is_dash():
    r = mention_rationale("mention:s", ROW, {**M, "date_label": ""}, 0)
    assert r["items"]["scope"]["text"] == {"ko": COVERAGE_NOTE, "en": COVERAGE_NOTE_EN}
    assert len(COVERAGE_NOTE_EN) <= 300 and r["items"]["scope"]["rows"] == []
    assert {x["k"]["ko"]: x["v"]["ko"] for x in r["items"]["src"]["rows"]}["날짜 표기"] == "—"


def test_long_data_values_are_capped():
    r = mention_rationale("mention:s", ROW, {**M, "matched_term": "가" * 500}, 0)
    assert len(r["chips"][0]["label"]["ko"]) <= 300


def test_sillok_orig_gets_original_text_notice():
    r = mention_rationale("mention:s", ROW, M, 0)
    assert r["chips"][2]["label"]["ko"].endswith("국역 없음")
    assert "한문 원문" in r["items"]["src"]["text"]["ko"]


def test_non_sillok_gets_neutral_source_notice():
    ev = {**M, "source": {**M["source"], "id": "event:x"}}
    r = mention_rationale("mention:s", ROW, ev, 0)
    assert r["chips"][2]["label"] == {"ko": "◆ 출처 등급 S", "en": "◆ Source grade S"}
    assert r["items"]["src"]["text"]["ko"] == "출처 구절은 색인에 저장된 글에서 잘라 온 것입니다."
    assert "국역 없음" not in json.dumps(r["chips"][2], ensure_ascii=False)
    assert "국역 없음" not in json.dumps(r["items"]["src"], ensure_ascii=False)
    # 실록이어도 원문이 아니면 중립
    r2 = mention_rationale("mention:s", ROW, {**M, "lang": "ko"}, 0)
    assert "국역 없음" not in json.dumps(r2["items"]["src"], ensure_ascii=False)


def test_alias_is_judged_against_first_term_not_anchor_name():
    row = {"anchor": {"name": "별칭으로 부름"}, "terms": ["○○궁", "別名"], "found_articles": 1}
    assert {x["k"]["ko"]: x["v"]["ko"] for x in mention_rationale("m", row, M, 0)["items"]["match"]["rows"]}["별칭 여부"] == "아니오"
    m = {**M, "matched_term": "別名"}
    assert {x["k"]["ko"]: x["v"]["ko"] for x in mention_rationale("m", row, m, 0)["items"]["match"]["rows"]}["별칭 여부"] == "예"
