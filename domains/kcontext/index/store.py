"""로컬 색인 저장소 — 청크 + 출처 메타 + SQLite FTS5(trigram), D8.

보안 주의: 저장되는 text·quote 는 신뢰할 수 없는 입력(웹·문서)이다. 원문 그대로 저장하며
여기서 프롬프트 주입을 판정하지 않는다. 소비자(T211b)가 `core.guard` 로 판정한다.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Protocol, Self

# T201 을 import 하지 않는다(병렬). 값이 같아야 한다 — T216a 테스트에서 일치 확인.
TIERS = ("S", "A", "B", "C", "D")

MAX_TEXT = 20_000
MAX_QUOTE = 500
DEFAULT_QUOTE = 300
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks(
  chunk_id TEXT PRIMARY KEY, source_id TEXT NOT NULL, tier TEXT NOT NULL, name TEXT NOT NULL,
  locator TEXT NOT NULL, url TEXT NOT NULL, published TEXT, collected_at TEXT NOT NULL,
  text TEXT NOT NULL, quote TEXT NOT NULL, regions_json TEXT NOT NULL, meta_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunk_regions(chunk_id TEXT NOT NULL, region TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_chunk_regions ON chunk_regions(region, chunk_id);
"""
_FTS = (
    "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING "
    "fts5(chunk_id UNINDEXED, text, tokenize='trigram')"
)
_COLS = (
    "chunk_id, source_id, tier, name, locator, url, published, collected_at, "
    "text, quote, regions_json, meta_json"
)
_TIER_RANK = {t: i for i, t in enumerate(TIERS)}


class IndexStoreError(Exception):
    """색인 저장소 오류의 기반."""


class ChunkValidationError(IndexStoreError, ValueError):
    """청크 검증 실패. 배치 전체가 거부된다."""


class ChunkNotFound(IndexStoreError, KeyError):
    """chunk_id 가 없다."""


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source_id: str
    tier: str
    name: str
    locator: str
    url: str
    published: str | None
    collected_at: str
    text: str
    quote: str
    regions: tuple[str, ...] = ()
    meta: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


class Retriever(Protocol):
    def search(
        self,
        query: str,
        *,
        regions: Collection[str] | None = None,
        tiers: Collection[str] | None = None,
        limit: int = 20,
    ) -> list[Hit]: ...


def _blank(value: object) -> bool:
    return not isinstance(value, str) or not value.strip()


def _validate(chunk: Chunk) -> Chunk:
    """통과하면 quote 가 채워진 청크를 돌려준다. 실패하면 ChunkValidationError."""

    def fail(reason: str) -> ChunkValidationError:
        return ChunkValidationError(f"chunk {chunk.chunk_id!r}: {reason}")

    if _blank(chunk.chunk_id):
        raise fail("chunk_id 가 비어 있다")
    if chunk.tier not in TIERS:
        raise fail(f"tier 는 {TIERS} 중 하나여야 한다")
    for name in ("source_id", "name", "locator", "collected_at", "text"):
        if _blank(getattr(chunk, name)):
            raise fail(f"{name} 가 비어 있다")
    if not isinstance(chunk.url, str):
        raise fail("url 은 문자열이어야 한다")
    if not _DATE.match(chunk.collected_at):
        raise fail("collected_at 은 YYYY-MM-DD 여야 한다")
    try:
        date.fromisoformat(chunk.collected_at)
    except ValueError:
        raise fail("collected_at 이 올바른 날짜가 아니다") from None
    if len(chunk.text) > MAX_TEXT:
        raise fail(f"text 가 {MAX_TEXT}자를 넘는다")
    quote = chunk.quote if not _blank(chunk.quote) else chunk.text[:DEFAULT_QUOTE]
    if len(quote) > MAX_QUOTE:
        raise fail(f"quote 가 {MAX_QUOTE}자를 넘는다")
    if any(not isinstance(r, str) or not r for r in chunk.regions):
        raise fail("regions 항목은 비어 있지 않은 문자열이어야 한다")
    if any(not isinstance(k, str) or not isinstance(v, str) for k, v in chunk.meta.items()):
        raise fail("meta 는 문자열 쌍이어야 한다")
    if quote == chunk.quote:
        return chunk
    return Chunk(**{**chunk.__dict__, "quote": quote})


def _like_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _row_to_chunk(row: tuple) -> Chunk:
    return Chunk(
        chunk_id=row[0], source_id=row[1], tier=row[2], name=row[3], locator=row[4],
        url=row[5], published=row[6], collected_at=row[7], text=row[8], quote=row[9],
        regions=tuple(json.loads(row[10])), meta=dict(json.loads(row[11])),
    )  # fmt: skip


class LocalIndex:
    """SQLite 한 파일 색인. `Retriever` 구현."""

    def __init__(self, path: str | Path, *, _force_like: bool = False) -> None:
        if str(path) != ":memory:" and not Path(path).parent.is_dir():
            raise FileNotFoundError(f"부모 디렉터리가 없다: {Path(path).parent}")
        self._conn = sqlite3.connect(str(path))
        self._conn.executescript(_SCHEMA)
        self._fts = False
        if not _force_like:
            try:
                self._conn.execute(_FTS)
                self._fts = True
            except sqlite3.OperationalError:
                self._fts = False
        self._conn.commit()

    @property
    def fts_enabled(self) -> bool:
        return self._fts

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._conn.close()

    def add(self, chunks: Iterable[Chunk]) -> int:
        """chunk_id 기준 upsert. 하나라도 검증에 실패하면 배치 전체를 거부한다."""
        valid = [_validate(c) for c in chunks]
        with self._conn:  # 트랜잭션
            for c in valid:
                self._conn.execute(
                    f"INSERT OR REPLACE INTO chunks({_COLS}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (c.chunk_id, c.source_id, c.tier, c.name, c.locator, c.url, c.published,
                     c.collected_at, c.text, c.quote,
                     json.dumps(list(c.regions), ensure_ascii=False),
                     json.dumps(dict(c.meta), ensure_ascii=False, sort_keys=True)),
                )  # fmt: skip
                self._conn.execute("DELETE FROM chunk_regions WHERE chunk_id=?", (c.chunk_id,))
                self._conn.executemany(
                    "INSERT INTO chunk_regions(chunk_id, region) VALUES (?,?)",
                    [(c.chunk_id, r) for r in set(c.regions)],
                )
                if self._fts:
                    self._conn.execute("DELETE FROM chunks_fts WHERE chunk_id=?", (c.chunk_id,))
                    self._conn.execute(
                        "INSERT INTO chunks_fts(chunk_id, text) VALUES (?,?)", (c.chunk_id, c.text)
                    )
        return len(valid)

    def get(self, chunk_id: str) -> Chunk:
        row = self._conn.execute(
            f"SELECT {_COLS} FROM chunks WHERE chunk_id=?", (chunk_id,)
        ).fetchone()
        if row is None:
            raise ChunkNotFound(chunk_id)
        return _row_to_chunk(row)

    def count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])

    def _filters(
        self, regions: Collection[str] | None, tiers: Collection[str] | None
    ) -> tuple[str, list[object]]:
        sql, params = "", []
        if regions is not None:
            ph = ",".join("?" * len(regions))
            sql += f" AND EXISTS (SELECT 1 FROM chunk_regions r WHERE r.chunk_id=c.chunk_id AND r.region IN ({ph}))"
            params += list(regions)
        if tiers is not None:
            ph = ",".join("?" * len(tiers))
            sql += f" AND c.tier IN ({ph})"
            params += list(tiers)
        return sql, params

    def search(
        self,
        query: str,
        *,
        regions: Collection[str] | None = None,
        tiers: Collection[str] | None = None,
        limit: int = 20,
    ) -> list[Hit]:
        if not 1 <= limit <= 200:
            raise ValueError("limit 은 1..200 이어야 한다")
        q = unicodedata.normalize("NFKC", query).strip()
        if not q or (regions is not None and not regions) or (tiers is not None and not tiers):
            return []
        where, params = self._filters(regions, tiers)
        cols = ", ".join(f"c.{n.strip()}" for n in _COLS.split(","))
        if self._fts and len(q) >= 3:
            phrase = '"' + q.replace('"', '""') + '"'
            rows = self._conn.execute(
                f"SELECT {cols}, -bm25(chunks_fts) FROM chunks_fts f "
                f"JOIN chunks c ON c.chunk_id=f.chunk_id "
                f"WHERE chunks_fts MATCH ?{where}",
                [phrase, *params],
            ).fetchall()
            hits = [Hit(_row_to_chunk(r[:12]), float(r[12])) for r in rows]
        else:
            rows = self._conn.execute(
                f"SELECT {cols} FROM chunks c WHERE c.text LIKE ? ESCAPE '\\'{where}",
                [f"%{_like_escape(q)}%", *params],
            ).fetchall()
            needle = q.lower()
            hits = [Hit(_row_to_chunk(r), float(r[8].lower().count(needle) or 1)) for r in rows]
        hits.sort(key=lambda h: (-h.score, _TIER_RANK[h.chunk.tier], h.chunk.chunk_id))
        return hits[:limit]
