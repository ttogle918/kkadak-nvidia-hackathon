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
import os
import tempfile
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from domains.kcontext.paths import var_dir

from .model import EventEntry, Observation, entry_from_dict, observation_from_dict

__all__ = ["CatalogStore", "default_dir"]


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

    def _write_json(self, name: str, data: Any) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.dir, prefix=f".{name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
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
    def load_entries(self) -> list[EventEntry]:
        raw = self._read_json("entries.json", {"entries": []})
        return [entry_from_dict(e) for e in raw.get("entries", [])]

    def entries_built_at(self) -> str | None:
        return self._read_json("entries.json", {}).get("built_at")

    def save_entries(self, entries: Iterable[EventEntry], built_at: str) -> None:
        self._write_json("entries.json", {"built_at": built_at, "entries": [e.to_dict() for e in entries]})

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
