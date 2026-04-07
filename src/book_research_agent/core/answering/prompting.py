from __future__ import annotations

from book_research_agent.core.retrieval import SearchResult


def build_grounded_answer_prompt(
    *,
    query: str,
    search_results: list[SearchResult],
) -> str:
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query must not be empty")
    if not search_results:
        raise ValueError("search_results must not be empty")

    source_blocks = [
        _format_source_block(result, index=index)
        for index, result in enumerate(search_results, start=1)
    ]
    return "\n".join(
        [
            "You answer questions using only the provided sources.",
            "Keep the answer short, direct, and grounded in the sources.",
            "If the sources do not contain the answer, say so plainly.",
            "Do not invent facts or citations.",
            "",
            f"Question: {normalized_query}",
            "",
            "Sources:",
            *source_blocks,
        ]
    )


def _format_source_block(result: SearchResult, *, index: int) -> str:
    metadata = result.indexed_chunk.metadata
    normalized_text = " ".join(result.indexed_chunk.text.split()).strip()
    return "\n".join(
        [
            f"[Source {index}]",
            f"title: {metadata.source_title}",
            f"path: {metadata.document_relative_path}",
            f"chunk_index: {metadata.chunk_index}",
            f"content: {normalized_text}",
            "",
        ]
    )
