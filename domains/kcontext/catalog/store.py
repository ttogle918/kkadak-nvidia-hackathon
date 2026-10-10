"""카탈로그 파일 저장소(JSON). 쓰기는 임시 파일 → 교체라서 도중에 죽어도 이전 파일이 남는다.

``dir/``
  observations.json  {obs_id: {"observation", "source_id", "first_seen_at", "last_seen_at"}}
  entries.json       {"built_at", "entries": [...]}
  changes.jsonl      변경 이력(추가만)
  runs.json          출처별 수집 실행 기록
  reports.json       제보·수정 요청(검토 전에는 공개 데이터에 들어가지 않는다)
  link_checks.json   자동 수집이 안 되는 공식 링크의 관리자 확인 기록
"""

from __future__ import annotations

import fcntl
import json
import logging
import os
import re
import tempfile
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from domains.kcontext.paths import var_dir

from .model import EventEntry, Observation, entry_from_dict, observation_from_dict
from .query import pre_exclusion_reason
from .rules import KST, event_lifecycle, to_kst

__all__ = ["SEARCH_INDEX", "SEARCH_INDEX_SCHEMA", "CatalogStore", "default_dir"]

SEARCH_INDEX = "search_index.json"
SEARCH_INDEX_SCHEMA = "kc-search-index/v1"
_BUILT_AT_HEAD = re.compile(rb'"built_at"\s*:\s*(null|"([^"]*)")')
_log = logging.getLogger("kc.catalog.index")


def default_dir() -> Path:
    env = os.environ.get("KC_CATALOG_DIR")
    return Path(env) if env else var_dir() / "catalog"


class CatalogStore:
    def __init__(self, directory: Path | None = None) -> None:
        self.dir = Path(directory) if directory is not None else default_dir()
        self._depth = 0

    @contextmanager
    def lock(self) -> Iterator[None]:
        """카탈로그 쓰기 구간의 프로세스 간 잠금(제보 제출·승인·재수집이 동시에 일어나도 갱신이 사라지지 않게).
        같은 프로세스 안에서는 중첩해서 잡아도 된다."""
        if self._depth:
            self._depth += 1
            try:
                yield
            finally:
                self._depth -= 1
            return
        self.dir.mkdir(parents=True, exist_ok=True)
        with (self.dir / ".lock").open("a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            self._depth = 1
            try:
                yield
            finally:
                self._depth = 0
                fcntl.flock(f, fcntl.LOCK_UN)

    # ---- 공통 ----
    def _path(self, name: str) -> Path:
        return self.dir / name

    def _read_json(self, name: str, default: Any) -> Any:
        p = self._path(name)
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return default

    def _write_json(self, name: str, data: Any, indent: int | None = 1) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.dir, prefix=f".{name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            os.replace(tmp, self._path(name))
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    # ---- 관찰값 ----
    def load_observations(self) -> dict[str, dict]:
        """{obs_id: {"observation": Observation, "source_id", "first_seen_at", "last_seen_at"}}."""
        raw = self._read_json("observations.json", {})
        return {k: {**v, "observation": observation_from_dict(v["observation"])} for k, v in raw.items()}

    def save_observations(self, items: dict[str, dict]) -> None:
        self._write_json("observations.json", {
            k: {**v, "observation": _plain(v["observation"])} for k, v in sorted(items.items())})

    # ---- 항목 ----
    def read_entries_raw(self) -> dict:
        """entries.json 을 한 번 읽은 dict(``built_at``·``entries``). 없으면 빈 항목."""
        return self._read_json("entries.json", {"entries": []})

    def load_entries(self) -> list[EventEntry]:
        return [entry_from_dict(e) for e in self.read_entries_raw().get("entries", [])]

    def entries_built_at(self) -> str | None:
        """파일 앞부분만 읽어 ``built_at`` 을 꺼낸다(23MB 를 다시 파싱하지 않는다). 앞부분에 없으면 전체 파싱."""
        try:
            with self._path("entries.json").open("rb") as f:
                head = f.read(512)
        except FileNotFoundError:
            return None
        m = _BUILT_AT_HEAD.search(head)
        if m:
            return m.group(2).decode("utf-8") if m.group(2) is not None else None
        return self._read_json("entries.json", {}).get("built_at")

    def save_entries(self, entries: Iterable[EventEntry], built_at: str, *, index: bool = True) -> None:
        entries = list(entries)
        self._path(SEARCH_INDEX).unlink(missing_ok=True)  # 항목을 바꾸는 동안 낡은 색인이 남지 않게
        self._write_json("entries.json", {"built_at": built_at, "entries": [e.to_dict() for e in entries]})
        if index:
            try:
                at = to_kst(datetime.fromisoformat(built_at))
            except (ValueError, TypeError):
                at = datetime.now(KST)
            self.save_search_index(entries, built_at, indexed_at=at)

    # ---- 검색 색인(T433) ----
    def save_search_index(self, entries: Iterable[EventEntry], built_at: str, *, indexed_at: datetime) -> dict:
        """요청과 무관하게 제외되는 항목(대상 밖·미확인·취소·종료)은 변환 없이 ``{pos,id,title,reason}`` 만,
        나머지(demo 포함)는 후보로 전체 dict 를 남긴다. 종료는 시간이 지나도 종료라 ``now >= indexed_at`` 에서 유효하다."""
        indexed_at = to_kst(indexed_at)
        cands: list[dict] = []
        pre: list[dict] = []
        total = 0
        for pos, e in enumerate(entries):
            total += 1
            reason = None if e.demo else pre_exclusion_reason(e, event_lifecycle(e, indexed_at))
            if reason:
                pre.append({"pos": pos, "id": e.id, "title": e.title, "reason": reason})
            else:
                cands.append({"pos": pos, "entry": e.to_dict()})
        data = {"schema": SEARCH_INDEX_SCHEMA, "built_at": built_at,
                "indexed_at": indexed_at.strftime("%Y-%m-%dT%H:%M"), "total": total,
                "candidates": cands, "pre_excluded": pre}
        self._write_json(SEARCH_INDEX, data, indent=None)
        return {"total": total, "candidates": len(cands), "pre_excluded": len(pre)}

    def reindex(self, *, now: datetime) -> dict:
        """entries.json 에서 색인을 다시 만든다(entries.json 이 없으면 빈 카탈로그로 본다)."""
        raw = self.read_entries_raw()
        entries = [entry_from_dict(e) for e in raw.get("entries", [])]
        info = self.save_search_index(entries, raw.get("built_at"), indexed_at=now)
        return {**info, "bytes": self._path(SEARCH_INDEX).stat().st_size}

    def load_search_index(self, now: datetime) -> dict | None:
        """유효한 색인(schema·``built_at`` 일치·``now >= indexed_at``)이면 dict, 아니면 None(경고 로그 — 전체 경로로 폴백)."""
        try:
            idx = json.loads(self._path(SEARCH_INDEX).read_text(encoding="utf-8"))
            if not isinstance(idx, dict):
                raise TypeError("object 가 아님")
            problem = None
            if idx.get("schema") != SEARCH_INDEX_SCHEMA:
                problem = "schema 가 다르다"
            elif idx.get("built_at") != self.entries_built_at():
                problem = "built_at 이 entries.json 과 다르다"
            elif to_kst(now) < to_kst(datetime.fromisoformat(idx["indexed_at"])):
                problem = "색인보다 이전 시각의 검색이다"
            elif not (isinstance(idx["candidates"], list) and isinstance(idx["pre_excluded"], list)
                      and isinstance(idx["total"], int)):
                problem = "구조가 올바르지 않다"
        except FileNotFoundError:
            problem, idx = "색인 파일이 없다", None
        except (ValueError, KeyError, TypeError, OSError) as e:
            problem, idx = f"색인을 읽을 수 없다 ({type(e).__name__})", None
        if problem:
            _log.warning("검색 색인을 쓰지 않고 전체 경로로 검색한다: %s", problem)
            return None
        return idx

    # ---- 변경 이력 ----
    def append_changes(self, changes: Iterable[dict]) -> int:
        rows = [json.dumps(c, ensure_ascii=False) + "\n" for c in changes]
        if rows:
            self.dir.mkdir(parents=True, exist_ok=True)
            with self._path("changes.jsonl").open("a", encoding="utf-8") as f:
                f.writelines(rows)
        return len(rows)

    def load_changes(self) -> list[dict]:
        p = self._path("changes.jsonl")
        if not p.exists():
            return []
        return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]

    # ---- 실행 기록·제보·링크 확인 ----
    def load_runs(self) -> dict[str, dict]:
        return self._read_json("runs.json", {})

    def save_runs(self, runs: dict[str, dict]) -> None:
        self._write_json("runs.json", runs)

    def load_reports(self) -> list[dict]:
        return self._read_json("reports.json", [])

    def save_reports(self, reports: list[dict]) -> None:
        self._write_json("reports.json", reports)

    def load_link_checks(self) -> dict[str, dict]:
        return self._read_json("link_checks.json", {})

    def save_link_checks(self, checks: dict[str, dict]) -> None:
        self._write_json("link_checks.json", checks)


def _plain(o: Observation) -> dict:
    from .model import _plain as plain

    return plain(o)
