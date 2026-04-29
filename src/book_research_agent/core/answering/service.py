from __future__ import annotations

from book_research_agent.core.answering.defaults import DEFAULT_ANSWER_TOP_K
from book_research_agent.core.generation.budgets import get_generation_output_budget
from book_research_agent.core.answering.models import AnswerResult, SourceReference
from book_research_agent.core.answering.prompting import build_grounded_answer_prompt
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.providers.base import EmbeddingProvider, GenerationProvider
from book_research_agent.core.retrieval import retrieve_reranked_results
from book_research_agent.domain import DEFAULT_DOMAIN_PACK


def answer_query(
    *,
    query: str,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int = DEFAULT_ANSWER_TOP_K,
) -> AnswerResult:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    search_results = retrieve_reranked_results(
        query=query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=top_k,
    )

    if not search_results:
        return AnswerResult(
            query=query,
            answer="No relevant sources were found in the local index.",
            sources_used=[],
        )

    prompt = build_grounded_answer_prompt(
        query=query,
        search_results=search_results,
        domain_pack=DEFAULT_DOMAIN_PACK,
    )
    answer = generation_provider.generate_text(
        prompt,
        output_budget=get_generation_output_budget("answer"),
    ).strip()
    if not answer:
        raise ValueError("generation provider returned an empty answer")

    return AnswerResult(
        query=query,
        answer=answer,
        sources_used=[
            SourceReference(
                title=result.indexed_chunk.metadata.source_title,
                relative_path=result.indexed_chunk.metadata.document_relative_path,
                chunk_index=result.indexed_chunk.metadata.chunk_index,
            )
            for result in search_results
        ],
    )
