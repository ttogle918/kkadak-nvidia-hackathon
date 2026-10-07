"""앵커 이름으로 색인에서 후보 청크를 찾고(기사 단위로 묶어) 왕대가 몰리지 않게 고른다.

읽기 전용이다(색인에 쓰지 않는다). 지명은 코드에 두지 않는다 — 한자 표기는 색인의 place_alias 에서만 온다.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domains.kcontext.index import Chunk, LocalIndex

DEFAULT_LIMIT = 3
MAX_LIMIT = 10
MAX_NAME = 100
PER_TERM_HITS = 200  # LocalIndex.search 의 상한


@dataclass(frozen=True)
class Candidate:
    """한 기사의 대표 청크(그 기사에서 점수가 가장 높은 것)."""

    article_id: str
    chunk: Chunk
    score: float
    matched_term: str  # 이 청크를 찾아 낸 검색어(앵커 이름 또는 색인의 별칭)


@dataclass(frozen=True)
class AnchorResult:
    name: str
    terms: tuple[str, ...]  # 실제로 검색에 쓴 표기(이름 + place_alias 별칭)
    found_articles: int  # 선별 전 후보 기사 수
    truncated: bool = False  # 검색어 하나가 상한(PER_TERM_HITS 청크)까지 찼다 — 실제 후보는 더 많다
    selected: tuple[Candidate, ...] = field(default_factory=tuple)


def clean_name(name: object) -> str | None:
    if not isinstance(name, str):
        return None
    n = name.strip()
    return n if n and len(n) <= MAX_NAME else None


def check_limit(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"limit 은 1..{MAX_LIMIT} 정수여야 한다")
    return limit


def find_candidates(index: LocalIndex, name: str) -> tuple[tuple[str, ...], list[Candidate], bool]:
    """(검색어 목록, 후보, 잘림 여부). 후보는 기사당 1건, 점수 내림차순(동점은 article_id)."""
    terms = index.expand_place(name)  # 사전에 없으면 (name,) — 비어 있어도 동작한다
    best: dict[str, Candidate] = {}
    truncated = False
    for term in terms:
        hits = index.search(term, limit=PER_TERM_HITS)
        truncated = truncated or len(hits) >= PER_TERM_HITS
        for hit in hits:
            aid = hit.chunk.meta.get("article_id") or hit.chunk.source_id
            cur = best.get(aid)
            if cur is None or (hit.score, hit.chunk.chunk_id) > (cur.score, cur.chunk.chunk_id):
                best[aid] = Candidate(aid, hit.chunk, hit.score, term)
    ordered = sorted(best.values(), key=lambda c: (-c.score, c.article_id))
    return terms, ordered, truncated


def select(cands: list[Candidate], n: int = DEFAULT_LIMIT) -> list[Candidate]:
    """점수순이되 이미 뽑힌 수가 가장 적은 왕대의 후보를 먼저 뽑는다(왕이 없으면 하나의 '미상' 묶음)."""
    check_limit(n)
    pool = list(cands)
    picked: list[Candidate] = []
    count: dict[str, int] = {}
    while pool and len(picked) < n:
        nxt = min(
            pool,
            key=lambda c: (count.get(c.chunk.meta.get("king", ""), 0), -c.score, c.article_id),
        )
        pool.remove(nxt)
        picked.append(nxt)
        k = nxt.chunk.meta.get("king", "")
        count[k] = count.get(k, 0) + 1
    return picked
