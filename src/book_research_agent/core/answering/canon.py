from __future__ import annotations

from book_research_agent.core.answering.compare import (
    _retrieve_compare_side,
    _source_references,
)
from book_research_agent.core.answering.models import CanonResult
from book_research_agent.core.answering.prompting import build_grounded_canon_prompt
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.providers.base import EmbeddingProvider, GenerationProvider
from book_research_agent.domain import DEFAULT_DOMAIN_PACK


def canon_query(
    *,
    query: str,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int = 3,
) -> CanonResult:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    search_results = _retrieve_compare_side(
        query=query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        top_k=top_k,
    )

    if not search_results:
        return CanonResult(
            query=query,
            judgment=(
                "current_canonical_reading: unclear\n"
                "competing_variants: unclear\n"
                "confidence: unclear because no relevant sources were found."
            ),
            sources_used=[],
        )

    prompt = build_grounded_canon_prompt(
        query=query,
        search_results=search_results,
        domain_pack=DEFAULT_DOMAIN_PACK,
    )
    judgment = generation_provider.generate_text(prompt).strip()
    if not judgment:
        raise ValueError("generation provider returned an empty canon judgment")

    return CanonResult(
        query=query,
        judgment=judgment,
        sources_used=_source_references(search_results),
    )
