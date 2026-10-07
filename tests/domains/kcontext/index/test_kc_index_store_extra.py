"""place_alias(지명 사전)와 chunk_embeddings(벡터) — 합성 데이터만."""

import pytest

from domains.kcontext.index import (
    Chunk,
    ChunkNotFound,
    ChunkValidationError,
    LocalIndex,
    PlaceAlias,
    make_chunk_id,
)


def mk(text, *, tier="B", regions=("region_a",)):
    return Chunk(
        chunk_id=make_chunk_id("src_synth", "합성 §1", text), source_id="src_synth", tier=tier,
        name="합성 출처", locator="합성 §1", url="", published=None, collected_at="2026-10-07",
        text=text, quote="", regions=regions,
    )  # fmt: skip


@pytest.fixture
def idx():
    with LocalIndex(":memory:") as i:
        yield i


def test_place_alias_roundtrip_and_expand(idx):
    n = idx.add_place_aliases(
        [PlaceAlias("가나", "甲乙", "ko", source="manual"), PlaceAlias("Gana", "甲乙", "en")]
    )
    assert n == 2
    assert {a.alias for a in idx.aliases_for("甲乙")} == {"가나", "Gana"}
    assert idx.expand_place("가나") == ("가나", "Gana", "甲乙")  # 한글 → place → 다른 표기까지
    assert idx.expand_place("없는곳") == ("없는곳",)
    assert idx.expand_place("  ") == ()


def test_place_alias_nfkc_and_upsert(idx):
    idx.add_place_aliases([PlaceAlias("ＡＢＣ", "에이", "en")])  # 전각 → NFKC
    assert idx.aliases_for("ABC")[0].alias == "ABC"
    idx.add_place_aliases([PlaceAlias("ABC", "에이", "ko", region="r1")])  # 같은 (alias, place) → 갱신
    rows = idx.aliases_for("ABC")
    assert len(rows) == 1 and rows[0].region == "r1" and rows[0].lang == "ko"


def test_place_alias_validation_rejects_whole_batch(idx):
    with pytest.raises(ChunkValidationError):
        idx.add_place_aliases([PlaceAlias("ok", "ok", "ko"), PlaceAlias("", "x", "ko")])
    assert idx.aliases_for("ok") == []


def test_embeddings_put_get_missing(idx):
    a, b = mk("가 합성 본문"), mk("나 합성 본문")
    idx.add([a, b])
    assert idx.missing_embeddings("m1") == sorted([a.chunk_id, b.chunk_id])
    assert idx.put_embeddings("m1", {a.chunk_id: [1.0, 0.0, 0.5]}) == 1
    assert idx.get_embedding(a.chunk_id, "m1") == (1.0, 0.0, 0.5)
    assert idx.get_embedding(a.chunk_id, "other") is None
    assert idx.missing_embeddings("m1") == [b.chunk_id]
    assert idx.missing_embeddings("other") == sorted([a.chunk_id, b.chunk_id])


def test_embeddings_validation(idx):
    a = mk("가 합성 본문")
    idx.add([a])
    idx.put_embeddings("m1", {a.chunk_id: [1.0, 2.0]})
    with pytest.raises(ChunkNotFound):
        idx.put_embeddings("m1", {"없는id": [1.0, 2.0]})
    with pytest.raises(ChunkValidationError, match="차원"):
        idx.put_embeddings("m1", {a.chunk_id: [1.0, 2.0, 3.0]})
    with pytest.raises(ChunkValidationError):
        idx.put_embeddings("m1", {a.chunk_id: [1.0, float("nan")]})
    with pytest.raises(ChunkValidationError):
        idx.put_embeddings("m1", {a.chunk_id: []})
    idx.put_embeddings("m2", {a.chunk_id: [1.0, 2.0, 3.0]})  # 모델이 다르면 차원도 다를 수 있다


def test_search_vector_ranks_filters_and_models(idx):
    a, b, c = mk("가 합성", regions=("r1",)), mk("나 합성", regions=("r2",)), mk("다 합성", tier="S", regions=("r1",))
    idx.add([a, b, c])
    idx.put_embeddings("m", {a.chunk_id: [1, 0], b.chunk_id: [0.7, 0.7], c.chunk_id: [0, 1]})
    hits = idx.search_vector([1, 0.1], "m")
    assert [h.chunk.chunk_id for h in hits] == [a.chunk_id, b.chunk_id, c.chunk_id]
    assert hits[0].score > hits[1].score > hits[2].score
    assert [h.chunk.chunk_id for h in idx.search_vector([1, 0.1], "m", regions=["r2"])] == [b.chunk_id]
    assert [h.chunk.chunk_id for h in idx.search_vector([1, 0.1], "m", tiers=["S"])] == [c.chunk_id]
    assert idx.search_vector([1, 0.1], "m", limit=1)[0].chunk.chunk_id == a.chunk_id
    assert idx.search_vector([1, 0.1], "없는모델") == []
    assert idx.search_vector([1, 0.1], "m", regions=[]) == []
    with pytest.raises(ValueError):
        idx.search_vector([1, 0, 0], "m")  # 차원 불일치
    with pytest.raises(ValueError):
        idx.search_vector([0, 0], "m")


def test_embeddings_reject_bool_and_float32_overflow(idx):
    a = mk("가 합성 본문")
    idx.add([a])
    with pytest.raises(ChunkValidationError):
        idx.put_embeddings("m", {a.chunk_id: [True, 1.0]})
    with pytest.raises(ChunkValidationError):
        idx.put_embeddings("m", {a.chunk_id: [1e39, 1.0]})
