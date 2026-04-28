from __future__ import annotations

import json
import re
from dataclasses import dataclass

from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.providers.base import EmbeddingProvider, GenerationProvider

from .search import SearchResult, search_index
from .source import filter_neighboring_results, format_excerpt


DEFAULT_RERANK_EXCERPT_LENGTH = 280
DEFAULT_RERANK_CANDIDATE_MULTIPLIER = 3
_CANDIDATE_ID_PATTERN = re.compile(r"R\d+")


@dataclass(frozen=True)
class RerankedRetrievalBundle:
    retrieval_candidates: list[SearchResult]
    final_evidence: list[SearchResult]


def retrieve_reranked_results(
    *,
    query: str,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int,
) -> list[SearchResult]:
    return retrieve_reranked_bundle(
        query=query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=top_k,
    ).final_evidence


def retrieve_reranked_bundle(
    *,
    query: str,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int,
) -> RerankedRetrievalBundle:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    candidate_results = search_index(
        query=query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        top_k=max(top_k * DEFAULT_RERANK_CANDIDATE_MULTIPLIER, top_k),
    )
    filtered_results = filter_neighboring_results(candidate_results)
    return RerankedRetrievalBundle(
        retrieval_candidates=filtered_results,
        final_evidence=rerank_search_results(
            query=query,
            candidates=filtered_results,
            generation_provider=generation_provider,
            top_k=top_k,
        ),
    )


def rerank_search_results(
    *,
    query: str,
    candidates: list[SearchResult],
    generation_provider: GenerationProvider,
    top_k: int,
) -> list[SearchResult]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")
    if not candidates:
        return []

    try:
        raw_response = generation_provider.generate_text(
            build_reranking_prompt(query=query, candidates=candidates),
        )
    except Exception:
        return candidates[:top_k]

    ordered_ids = parse_candidate_id_order(raw_response)
    if not ordered_ids:
        return candidates[:top_k]

    candidates_by_id = {
        _candidate_id(index): candidate
        for index, candidate in enumerate(candidates, start=1)
    }
    selected_ids: set[str] = set()
    selected_results: list[SearchResult] = []

    for candidate_id in ordered_ids:
        if candidate_id in selected_ids:
            continue
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            continue
        selected_ids.add(candidate_id)
        selected_results.append(candidate)
        if len(selected_results) >= top_k:
            return selected_results

    for candidate_id, candidate in candidates_by_id.items():
        if candidate_id in selected_ids:
            continue
        selected_results.append(candidate)
        if len(selected_results) >= top_k:
            break

    return selected_results


def build_reranking_prompt(
    *,
    query: str,
    candidates: list[SearchResult],
    excerpt_length: int = DEFAULT_RERANK_EXCERPT_LENGTH,
) -> str:
    if excerpt_length <= 0:
        raise ValueError("excerpt_length must be greater than zero")

    candidate_blocks = [
        _format_candidate_block(
            candidate_id=_candidate_id(index),
            result=result,
            excerpt_length=excerpt_length,
        )
        for index, result in enumerate(candidates, start=1)
    ]
    return "\n".join(
        [
            "You select existing evidence chunks for a private corpus query.",
            "Return only a JSON array of candidate ids in best evidence order.",
            'Example: ["R2", "R1", "R3"]',
            "Do not explain. Do not quote, rewrite, summarize, or create evidence.",
            "Use only the candidate ids listed below.",
            "",
            f"Query: {query}",
            "",
            "Candidates:",
            *candidate_blocks,
        ]
    )


def parse_candidate_id_order(raw_response: str) -> list[str]:
    response = raw_response.strip()
    if not response:
        return []

    try:
        payload = json.loads(response)
    except json.JSONDecodeError:
        return _parse_plain_candidate_ids(response)

    if not isinstance(payload, list):
        return []

    candidate_ids: list[str] = []
    for item in payload:
        if not isinstance(item, str):
            return []
        item = item.strip()
        if not _CANDIDATE_ID_PATTERN.fullmatch(item):
            return []
        candidate_ids.append(item)
    return candidate_ids


def _parse_plain_candidate_ids(response: str) -> list[str]:
    normalized = response.replace(",", "\n")
    candidate_ids: list[str] = []
    for line in normalized.splitlines():
        item = line.strip()
        if not item:
            continue
        if item.startswith("- "):
            item = item[2:].strip()
        if not _CANDIDATE_ID_PATTERN.fullmatch(item):
            return []
        candidate_ids.append(item)
    return candidate_ids


def _candidate_id(index: int) -> str:
    return f"R{index}"


def _format_candidate_block(
    *,
    candidate_id: str,
    result: SearchResult,
    excerpt_length: int,
) -> str:
    chunk = result.indexed_chunk
    return "\n".join(
        [
            "---",
            f"id: {candidate_id}",
            f"chunk_id: {chunk.chunk_id}",
            f"score: {result.score:.4f}",
            f"title: {chunk.metadata.source_title}",
            f"path: {chunk.metadata.document_relative_path}",
            "excerpt:",
            format_excerpt(chunk.text, max_length=excerpt_length),
        ]
    )
