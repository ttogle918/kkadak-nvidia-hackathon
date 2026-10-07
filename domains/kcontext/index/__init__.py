"""로컬 색인(청크 + 출처 메타 + FTS5 + 지명 사전 + 임베딩). D8."""

from domains.kcontext.index.chunk import chunk_text, make_chunk_id
from domains.kcontext.index.store import (
    TIERS,
    Chunk,
    ChunkNotFound,
    ChunkValidationError,
    Hit,
    IndexStoreError,
    LocalIndex,
    PlaceAlias,
    Retriever,
)

__all__ = [
    "TIERS",
    "Chunk",
    "ChunkNotFound",
    "ChunkValidationError",
    "Hit",
    "IndexStoreError",
    "LocalIndex",
    "PlaceAlias",
    "Retriever",
    "chunk_text",
    "make_chunk_id",
]
