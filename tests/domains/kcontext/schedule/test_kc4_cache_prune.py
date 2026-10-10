"""T436 — 일정 캐시 크기 상한(D27 ⑦). 의미는 그대로(D15 ④): 지워진 것은 미적중."""

import os

from domains.kcontext.schedule import ScheduleCache
from domains.kcontext.schedule import cache as cache_mod

RES = {"anchors": [], "free_slots": [], "problems": []}
META = {"source": "llm"}


def _key(i: int) -> str:
    return f"{i:064x}"


def _fill(c: ScheduleCache, n: int) -> None:
    for i in range(n):
        c.put(_key(i), RES, META)
        os.utime(c.root / f"{_key(i)}.json", (1000 + i, 1000 + i))  # i 가 클수록 최근


def test_file_count_limit_evicts_oldest_keeps_newest(tmp_path, monkeypatch):
    monkeypatch.setenv(cache_mod.MAX_FILES_ENV, "3")
    c = ScheduleCache(tmp_path)
    _fill(c, 3)
    c.put(_key(99), RES, META)  # mtime 은 지금 = 가장 최근
    assert c.get(_key(0)) is None  # 가장 오래된 것이 지워짐
    assert all(c.get(_key(i)) is not None for i in (1, 2, 99))
    assert len(list(tmp_path.glob("*.json"))) == 3


def test_byte_limit_and_just_written_survives(tmp_path, monkeypatch):
    c = ScheduleCache(tmp_path)
    _fill(c, 4)
    one = (tmp_path / f"{_key(0)}.json").stat().st_size
    monkeypatch.setenv(cache_mod.MAX_BYTES_ENV, str(one * 2 + 1))
    c.put(_key(50), RES, META)
    left = sorted(p.stem for p in tmp_path.glob("*.json"))
    assert _key(50) in left and len(left) == 2
    assert _key(3) in left  # 남은 하나는 그 다음으로 최근
    # 상한이 파일 하나보다 작아도 방금 쓴 것은 남는다
    monkeypatch.setenv(cache_mod.MAX_BYTES_ENV, "1")
    c.put(_key(51), RES, META)
    assert [p.stem for p in tmp_path.glob("*.json")] == [_key(51)]


def test_defaults_and_bad_env(tmp_path, monkeypatch):
    monkeypatch.setenv(cache_mod.MAX_FILES_ENV, "abc")
    monkeypatch.setenv(cache_mod.MAX_BYTES_ENV, "-5")
    assert cache_mod._limit(cache_mod.MAX_FILES_ENV, 500) == 500
    assert cache_mod._limit(cache_mod.MAX_BYTES_ENV, 7) == 7
    c = ScheduleCache(tmp_path)
    _fill(c, 5)
    assert len(list(tmp_path.glob("*.json"))) == 5  # 기본 상한 아래면 지우지 않음


def test_prune_ignores_foreign_files_and_vanished_entries(tmp_path, monkeypatch):
    monkeypatch.setenv(cache_mod.MAX_FILES_ENV, "1")
    c = ScheduleCache(tmp_path)
    (tmp_path / "notes.json").write_text("{}", encoding="utf-8")  # 키 모양이 아니면 건드리지 않음
    _fill(c, 2)
    assert (tmp_path / "notes.json").exists()
    assert len(list(tmp_path.glob("[0-9a-f]*.json"))) == 1
    # 읽는 쪽: 지워진 항목은 예외 없이 미적중
    assert c.get(_key(0)) is None


def test_get_after_concurrent_delete_is_miss(tmp_path):
    c = ScheduleCache(tmp_path)
    c.put(_key(1), RES, META)
    (tmp_path / f"{_key(1)}.json").unlink()
    assert c.get(_key(1)) is None
