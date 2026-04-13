from __future__ import annotations

from book_research_agent.core.answering.defaults import DEFAULT_COMPARE_TOP_K
from book_research_agent.core.answering.models import CompareResult, SourceReference
from book_research_agent.core.answering.prompting import build_grounded_compare_prompt
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.providers.base import EmbeddingProvider, GenerationProvider
from book_research_agent.core.retrieval import SearchResult, filter_neighboring_results, search_index
from book_research_agent.domain import DEFAULT_DOMAIN_PACK


def compare_queries(
    *,
    left_query: str,
    right_query: str,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int = DEFAULT_COMPARE_TOP_K,
) -> CompareResult:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    left_results = _retrieve_compare_side(
        query=left_query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        top_k=top_k,
    )
    right_results = _retrieve_compare_side(
        query=right_query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        top_k=top_k,
    )

    if not left_results or not right_results:
        return CompareResult(
            left_query=left_query,
            right_query=right_query,
            comparison="No relevant sources were found for one or both compare queries.",
            left_sources_used=_source_references(left_results),
            right_sources_used=_source_references(right_results),
        )

    prompt = build_grounded_compare_prompt(
        left_query=left_query,
        right_query=right_query,
        left_results=left_results,
        right_results=right_results,
        domain_pack=DEFAULT_DOMAIN_PACK,
    )
    comparison = generation_provider.generate_text(prompt).strip()
    if not comparison:
        raise ValueError("generation provider returned an empty comparison")

    return CompareResult(
        left_query=left_query,
        right_query=right_query,
        comparison=comparison,
        left_sources_used=_source_references(left_results),
        right_sources_used=_source_references(right_results),
    )


def _retrieve_compare_side(
    *,
    query: str,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    top_k: int,
) -> list[SearchResult]:
    candidate_count = max(top_k * 3, top_k)
    candidate_results = search_index(
        query=query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        top_k=candidate_count,
    )
    return filter_neighboring_results(candidate_results)[:top_k]


def _source_references(results: list[SearchResult]) -> list[SourceReference]:
    return [
        SourceReference(
            title=result.indexed_chunk.metadata.source_title,
            relative_path=result.indexed_chunk.metadata.document_relative_path,
            chunk_index=result.indexed_chunk.metadata.chunk_index,
        )
        for result in results
    ]
