from __future__ import annotations

import difflib
import math
from dataclasses import dataclass

from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.providers.base import EmbeddingProvider


@dataclass(frozen=True)
class SearchResult:
    indexed_chunk: IndexedChunk
    score: float


DEFAULT_TEXT_SIMILARITY_THRESHOLD = 0.96
DEFAULT_SAME_DOCUMENT_SIMILARITY_THRESHOLD = 0.9


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
    return filter_diverse_results(scored_results, max_results=top_k)


def filter_diverse_results(
    search_results: list[SearchResult],
    *,
    max_results: int,
    similarity_threshold: float = DEFAULT_TEXT_SIMILARITY_THRESHOLD,
    same_document_similarity_threshold: float = (
        DEFAULT_SAME_DOCUMENT_SIMILARITY_THRESHOLD
    ),
) -> list[SearchResult]:
    if max_results <= 0:
        raise ValueError("max_results must be greater than zero")

    kept_results: list[SearchResult] = []
    for result in search_results:
        if _is_near_duplicate(
            result,
            kept_results,
            similarity_threshold=similarity_threshold,
            same_document_similarity_threshold=same_document_similarity_threshold,
        ):
            continue

        kept_results.append(result)
        if len(kept_results) >= max_results:
            break

    return kept_results


def _is_near_duplicate(
    candidate: SearchResult,
    kept_results: list[SearchResult],
    *,
    similarity_threshold: float,
    same_document_similarity_threshold: float,
) -> bool:
    candidate_text = _normalize_text(candidate.indexed_chunk.text)

    for kept in kept_results:
        kept_text = _normalize_text(kept.indexed_chunk.text)
        if candidate_text == kept_text:
            return True

        similarity = _text_similarity(candidate_text, kept_text)
        same_document = (
            candidate.indexed_chunk.document_id == kept.indexed_chunk.document_id
        )
        threshold = (
            same_document_similarity_threshold
            if same_document
            else similarity_threshold
        )
        if similarity >= threshold:
            return True

    return False


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def _text_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return difflib.SequenceMatcher(a=left, b=right).ratio()
