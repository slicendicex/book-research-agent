from __future__ import annotations

from book_research_agent.domain import DomainPack, format_domain_guidance
from book_research_agent.core.retrieval import SearchResult


def build_grounded_answer_prompt(
    *,
    query: str,
    search_results: list[SearchResult],
    domain_pack: DomainPack | None = None,
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
    prompt_parts = [
        "You answer questions using only the provided sources.",
        "Keep the answer short, direct, and grounded in the sources.",
        "If the sources do not contain the answer, say so plainly.",
        "Do not invent facts, citations, or canon.",
    ]

    if domain_pack is not None:
        prompt_parts.extend(
            [
                "",
                format_domain_guidance(domain_pack),
            ]
        )

    prompt_parts.extend(
        [
            "",
            f"Question: {normalized_query}",
            "",
            "Sources:",
            *source_blocks,
        ]
    )
    return "\n".join(prompt_parts)


def build_grounded_compare_prompt(
    *,
    left_query: str,
    right_query: str,
    left_results: list[SearchResult],
    right_results: list[SearchResult],
    domain_pack: DomainPack | None = None,
) -> str:
    normalized_left_query = left_query.strip()
    normalized_right_query = right_query.strip()
    if not normalized_left_query:
        raise ValueError("left_query must not be empty")
    if not normalized_right_query:
        raise ValueError("right_query must not be empty")
    if not left_results:
        raise ValueError("left_results must not be empty")
    if not right_results:
        raise ValueError("right_results must not be empty")

    left_source_blocks = [
        _format_source_block(result, index=index)
        for index, result in enumerate(left_results, start=1)
    ]
    right_source_blocks = [
        _format_source_block(result, index=index)
        for index, result in enumerate(right_results, start=1)
    ]
    prompt_parts = [
        "You compare two topics using only the provided sources.",
        "Keep the comparison short, direct, and grounded in the sources.",
        "Cover shared themes, key differences, main tension, and uncertainties if relevant.",
        "If the sources do not support a claim, say so plainly.",
        "Do not invent facts, citations, or canon.",
    ]

    if domain_pack is not None:
        prompt_parts.extend(
            [
                "",
                format_domain_guidance(domain_pack),
            ]
        )

    prompt_parts.extend(
        [
            "",
            f"Left query: {normalized_left_query}",
            f"Right query: {normalized_right_query}",
            "",
            "Left sources:",
            *left_source_blocks,
            "Right sources:",
            *right_source_blocks,
        ]
    )
    return "\n".join(prompt_parts)


def build_grounded_contradiction_prompt(
    *,
    left_query: str,
    right_query: str,
    left_results: list[SearchResult],
    right_results: list[SearchResult],
    domain_pack: DomainPack | None = None,
) -> str:
    normalized_left_query = left_query.strip()
    normalized_right_query = right_query.strip()
    if not normalized_left_query:
        raise ValueError("left_query must not be empty")
    if not normalized_right_query:
        raise ValueError("right_query must not be empty")
    if not left_results:
        raise ValueError("left_results must not be empty")
    if not right_results:
        raise ValueError("right_results must not be empty")

    left_source_blocks = [
        _format_source_block(result, index=index)
        for index, result in enumerate(left_results, start=1)
    ]
    right_source_blocks = [
        _format_source_block(result, index=index)
        for index, result in enumerate(right_results, start=1)
    ]
    prompt_parts = [
        "You judge whether two source-grounded claims are aligned, in tension, contradictory, or unclear.",
        "Use only the provided sources.",
        "Bias toward caution: prefer 'in tension' or 'unclear' over 'contradictory' unless the sources strongly support contradiction.",
        "Keep the response short and structured.",
        "Use this shape: verdict: <aligned|in tension|contradictory|unclear>",
        "Then add: explanation: <one or two concise sentences>",
        "Do not invent facts, citations, or canon.",
    ]

    if domain_pack is not None:
        prompt_parts.extend(
            [
                "",
                format_domain_guidance(domain_pack),
            ]
        )

    prompt_parts.extend(
        [
            "",
            f"Left claim/query: {normalized_left_query}",
            f"Right claim/query: {normalized_right_query}",
            "",
            "Left sources:",
            *left_source_blocks,
            "Right sources:",
            *right_source_blocks,
        ]
    )
    return "\n".join(prompt_parts)


def build_grounded_canon_prompt(
    *,
    query: str,
    search_results: list[SearchResult],
    domain_pack: DomainPack | None = None,
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
    prompt_parts = [
        "You produce a short canon-oriented judgment using only the provided sources.",
        "Treat retrieved sources as the primary evidence.",
        "Prefer 'unclear' over overclaiming canon when support is limited.",
        "Identify competing variants only if the sources support them.",
        "Keep the response short and structured.",
        "Use this shape: current_canonical_reading: <one concise sentence>",
        "Then add: competing_variants: <concise note or unclear>",
        "Then add: confidence: <high|medium|low|unclear> with a short reason",
        "Do not invent facts, citations, or unsupported canon.",
    ]

    if domain_pack is not None:
        prompt_parts.extend(
            [
                "",
                format_domain_guidance(domain_pack),
            ]
        )

    prompt_parts.extend(
        [
            "",
            f"Canon query: {normalized_query}",
            "",
            "Sources:",
            *source_blocks,
        ]
    )
    return "\n".join(prompt_parts)


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
