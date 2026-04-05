from __future__ import annotations

import math
from dataclasses import dataclass

from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.providers.base import EmbeddingProvider


@dataclass(frozen=True)
class SearchResult:
    indexed_chunk: IndexedChunk
    score: float


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding vectors must have the same length")

    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))

    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot_product / (left_norm * right_norm)


def search_index(
    *,
    query: str,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    top_k: int = 5,
) -> list[SearchResult]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")
    if not indexed_chunks:
        return []

    query_embedding = embedding_provider.embed_text(query, input_type="search_query")
    scored_results = [
        SearchResult(
            indexed_chunk=indexed_chunk,
            score=cosine_similarity(query_embedding, indexed_chunk.embedding),
        )
        for indexed_chunk in indexed_chunks
    ]
    scored_results.sort(key=lambda result: result.score, reverse=True)
    return scored_results[:top_k]
