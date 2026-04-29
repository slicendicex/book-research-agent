from __future__ import annotations

from book_research_agent.core.answering.compare import (
    _retrieve_compare_side,
    _source_references,
)
from book_research_agent.core.answering.defaults import DEFAULT_CONTRADICT_TOP_K
from book_research_agent.core.generation.budgets import get_generation_output_budget
from book_research_agent.core.answering.models import ContradictionResult
from book_research_agent.core.answering.prompting import (
    build_grounded_contradiction_prompt,
)
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.providers.base import EmbeddingProvider, GenerationProvider
from book_research_agent.domain import DEFAULT_DOMAIN_PACK


def contradict_queries(
    *,
    left_query: str,
    right_query: str,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int = DEFAULT_CONTRADICT_TOP_K,
) -> ContradictionResult:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    left_results = _retrieve_compare_side(
        query=left_query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=top_k,
    )
    right_results = _retrieve_compare_side(
        query=right_query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=top_k,
    )

    if not left_results or not right_results:
        return ContradictionResult(
            left_query=left_query,
            right_query=right_query,
            judgment="verdict: unclear\nexplanation: Missing sources for one or both sides.",
            left_sources_used=_source_references(left_results),
            right_sources_used=_source_references(right_results),
        )

    prompt = build_grounded_contradiction_prompt(
        left_query=left_query,
        right_query=right_query,
        left_results=left_results,
        right_results=right_results,
        domain_pack=DEFAULT_DOMAIN_PACK,
    )
    judgment = generation_provider.generate_text(
        prompt,
        output_budget=get_generation_output_budget("contradict"),
    ).strip()
    if not judgment:
        raise ValueError("generation provider returned an empty contradiction judgment")

    return ContradictionResult(
        left_query=left_query,
        right_query=right_query,
        judgment=judgment,
        left_sources_used=_source_references(left_results),
        right_sources_used=_source_references(right_results),
    )
