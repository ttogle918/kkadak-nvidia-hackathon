"""T417 — 서울 API 좌표 자동 부착(D25): 빌더 이상치 규칙 · 사람 우선 · 깨진 파일 · COORD_AUTO. 로컬 파일만."""

from __future__ import annotations

import json
import warnings

import pytest

from domains.kcontext.pipeline.run import _attach_coords
from domains.kcontext.places import load_places
from domains.kcontext.places_build import build_from_observations, load_rules, main

RULES = {"max_spread_m": 150, "max_gu_dist_km": 8}
GU_PTS = [(37.50, 127.00), (37.51, 127.01), (37.49, 126.99)]


def rec(name, lat, lng, gu="가구", basis="source_gu", source="seoul_openapi"):
    return {"source_id": source, "observation": {"venue": {
        "name": name, "lat": lat, "lng": lng, "district": gu, "district_basis": basis}}}  # fmt: skip


def filler(gu="가구"):  # 구 표본 3개 이상 + 중앙값 고정
    return [rec(f"채움{i}", a, b, gu) for i, (a, b) in enumerate(GU_PTS)]


def build(recs, manual=None):
    return build_from_observations(recs, RULES, manual, "2026-10-10")


def manual_book(tmp_path, name="경복궁"):
    p = tmp_path / "m.json"
    p.write_text(json.dumps([{"name": name, "aliases": ["별칭"], "lat": 37.5, "lng": 127.0, "source": "사람",
                              "verified_at": "2026-10-07", "note": ""}], ensure_ascii=False), encoding="utf-8")
    return load_places(p, auto=None)


def test_accepts_median_and_marks_auto():
    items, s = build([*filler(), rec("A홀", 37.5000, 127.0000), rec("a홀", 37.5005, 127.0004)])
    a = next(i for i in items if i["name"] in ("A홀", "a홀"))
    assert a["auto"] is True and a["origin"] == ["seoul_openapi"] and a["aliases"] == []
    assert a["verified_at"] == "2026-10-10" and "행 2건" in a["source"]
    assert abs(a["lat"] - 37.50025) < 1e-6
    assert s["accepted"] == len(items) == 4
    assert [i["name"] for i in items] == sorted(i["name"] for i in items)


def test_gu_median_outlier_dropped():
    # 같은 구 중앙값에서 8km 넘게 떨어진 좌표(부산 등)는 버리고, 그 이름만 있으면 far_from_gu
    items, s = build([*filler(), rec("먼곳", 35.1, 129.0)])
    assert "먼곳" not in {i["name"] for i in items}
    assert s["far_from_gu"] == 1


def test_far_point_dropped_but_name_kept_when_others_ok():
    items, s = build([*filler(), rec("B관", 37.50, 127.0), rec("B관", 35.1, 129.0)])
    b = next(i for i in items if i["name"] == "B관")
    assert b["lat"] == 37.5 and s["far_from_gu"] == 0


def test_ambiguous_when_spread_exceeds():
    items, s = build([*filler(), rec("동명", 37.500, 127.000), rec("동명", 37.505, 127.000)])  # 약 550m
    assert "동명" not in {i["name"] for i in items}
    assert s["ambiguous"] == 1


def test_no_gu_and_inferred_gu_not_used():
    items, s = build([*filler(), rec("무구", 37.5, 127.0, gu=""), rec("추정", 37.5, 127.0, basis="coords")])
    assert not {"무구", "추정"} & {i["name"] for i in items}
    assert s["no_gu"] == 2


def test_small_sample_gu_dropped():
    items, s = build([rec("외딴", 37.5, 127.0, gu="나구"), rec("외딴2", 37.5, 127.0, gu="나구")])
    assert items == [] and s["far_from_gu"] == 2


def test_other_sources_and_long_names_ignored():
    items, s = build([*filler(), rec("타출처", 37.5, 127.0, source="tavily"), rec("긴" * 201, 37.5, 127.0)])
    assert "타출처" not in {i["name"] for i in items} and len(items) == 3
    assert s["names_seen"] == 3


def test_manual_wins_in_builder_and_loader(tmp_path):
    book = manual_book(tmp_path)
    items, s = build([*filler(), rec("경복궁", 37.51, 127.01), rec("별칭", 37.5, 127.0)], book)
    assert "경복궁" not in {i["name"] for i in items} and s["shadowed_by_manual"] == 2
    auto = tmp_path / "a.json"
    auto.write_text(json.dumps([
        {**items[0], "name": "경복궁", "lat": 1.0, "lng": 2.0}, items[0]], ensure_ascii=False), encoding="utf-8")
    b = load_places(tmp_path / "m.json", auto=auto)
    assert b.lookup("경복궁").auto is False and b.lookup("경복궁").lat == 37.5
    assert b.lookup(items[0]["name"]).auto is True


def test_auto_file_via_env_default(tmp_path, monkeypatch):
    items, _ = build(filler())
    auto = tmp_path / "a.json"
    auto.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("KC_AUTO_PLACES", str(auto))
    assert load_places().lookup("채움0").auto is True
    monkeypatch.setenv("KC_AUTO_PLACES", str(tmp_path / "없음.json"))
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # 파일이 없는 기본 상태는 조용하다
        assert load_places().lookup("채움0") is None


def test_broken_auto_file_warns_and_manual_only(tmp_path):
    bad = tmp_path / "a.json"
    bad.write_text("{깨짐", encoding="utf-8")
    with pytest.warns(UserWarning, match="자동 장소 사전을 쓰지 않음"):
        b = load_places(auto=bad)
    assert len(b) > 0 and all(not p.auto for p in b.places)
    bad.write_text(json.dumps([{"name": "x", "aliases": [], "lat": 1, "lng": 1, "source": "s",
                                "verified_at": "2026-10-10", "note": ""}]), encoding="utf-8")  # auto 표시 없음
    with pytest.warns(UserWarning):
        load_places(auto=bad)


def test_human_file_rejects_auto_keys(tmp_path):
    from domains.kcontext.places import PlacesConfigError

    p = tmp_path / "m.json"
    p.write_text(json.dumps([{"name": "x", "aliases": [], "lat": 1, "lng": 1, "source": "s", "verified_at": "2026-10-10",
                              "note": "", "auto": True, "origin": ["seoul_openapi"]}]), encoding="utf-8")
    with pytest.raises(PlacesConfigError):
        load_places(p, auto=None)


def test_coord_auto_problem(tmp_path):
    items, _ = build(filler())
    auto = tmp_path / "a.json"
    auto.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    m = tmp_path / "m.json"
    m.write_text(json.dumps([{"name": "사람곳", "aliases": [], "lat": 37.5, "lng": 127.0, "source": "s",
                              "verified_at": "2026-10-07", "note": ""}], ensure_ascii=False), encoding="utf-8")
    book = load_places(m, auto=auto)
    anchors = [{"name": "채움0"}, {"name": "사람곳"}, {"name": "모름"}]
    problems: list[dict] = []
    _attach_coords(anchors, book, problems)
    assert [p["code"] for p in problems] == ["COORD_AUTO", "COORD_UNKNOWN"]
    assert problems[0]["message"] == "채움0: 공공 데이터 좌표(사람 확인 전)"
    assert anchors[0]["lat"] is not None and anchors[1]["lat"] == 37.5 and anchors[2]["lat"] is None


def test_cli_writes_only_out(tmp_path, capsys):
    cat = tmp_path / "cat"
    cat.mkdir()
    (cat / "observations.json").write_text(
        json.dumps({f"seoul:{i}": r for i, r in enumerate(filler())}, ensure_ascii=False), encoding="utf-8")
    rules = tmp_path / "r.json"
    rules.write_text(json.dumps(RULES), encoding="utf-8")
    out = tmp_path / "x" / "auto.json"
    assert main(["--catalog", str(cat), "--rules", str(rules), "--out", str(out), "--collected-at", "2026-10-10"]) == 0
    assert json.loads(capsys.readouterr().out)["accepted"] == 3
    assert len(json.loads(out.read_text(encoding="utf-8"))) == 3


def test_shipped_rules_have_no_human_ranges():
    r = load_rules("domains/kcontext/data/places/auto_rules.json")
    assert r == {"max_spread_m": 150.0, "max_gu_dist_km": 8.0}
