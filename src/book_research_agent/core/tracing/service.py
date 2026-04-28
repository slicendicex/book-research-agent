from __future__ import annotations

from book_research_agent.core.answering import (
    AnswerResult,
    CanonResult,
    CompareResult,
    ContradictionResult,
    SourceReference,
)
from book_research_agent.core.answering.defaults import (
    DEFAULT_ANSWER_TOP_K,
    DEFAULT_CANON_TOP_K,
    DEFAULT_COMPARE_TOP_K,
    DEFAULT_CONTRADICT_TOP_K,
)
from book_research_agent.core.answering.prompting import (
    build_grounded_answer_prompt,
    build_grounded_canon_prompt,
    build_grounded_compare_prompt,
    build_grounded_contradiction_prompt,
)
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.providers.base import EmbeddingProvider, GenerationProvider
from book_research_agent.core.retrieval import (
    SearchResult,
    format_excerpt,
    retrieve_reranked_bundle,
)
from book_research_agent.domain import DEFAULT_DOMAIN_PACK

from .models import RagTraceArtifact, TraceEvidenceBlock, TraceSide


DEFAULT_TRACE_EXCERPT_LENGTH = 280


def run_answer_with_trace(
    *,
    query: str,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int = DEFAULT_ANSWER_TOP_K,
) -> tuple[AnswerResult, RagTraceArtifact]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    bundle = retrieve_reranked_bundle(
        query=query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=top_k,
    )
    search_results = bundle.final_evidence
    if not search_results:
        result = AnswerResult(
            query=query,
            answer="No relevant sources were found in the local index.",
            sources_used=[],
        )
    else:
        prompt = build_grounded_answer_prompt(
            query=query,
            search_results=search_results,
            domain_pack=DEFAULT_DOMAIN_PACK,
        )
        answer = generation_provider.generate_text(prompt).strip()
        if not answer:
            raise ValueError("generation provider returned an empty answer")
        result = AnswerResult(
            query=query,
            answer=answer,
            sources_used=_source_references(search_results),
        )

    return (
        result,
        build_single_mode_trace(
            mode="answer",
            query=query,
            retrieval_candidates=bundle.retrieval_candidates,
            final_evidence=bundle.final_evidence,
            generated_output=result.answer,
        ),
    )


def run_canon_with_trace(
    *,
    query: str,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int = DEFAULT_CANON_TOP_K,
) -> tuple[CanonResult, RagTraceArtifact]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    bundle = retrieve_reranked_bundle(
        query=query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=top_k,
    )
    search_results = bundle.final_evidence
    if not search_results:
        result = CanonResult(
            query=query,
            judgment=(
                "current_canonical_reading: unclear\n"
                "competing_variants: unclear\n"
                "confidence: unclear because no relevant sources were found."
            ),
            sources_used=[],
        )
    else:
        prompt = build_grounded_canon_prompt(
            query=query,
            search_results=search_results,
            domain_pack=DEFAULT_DOMAIN_PACK,
        )
        judgment = generation_provider.generate_text(prompt).strip()
        if not judgment:
            raise ValueError("generation provider returned an empty canon judgment")
        result = CanonResult(
            query=query,
            judgment=judgment,
            sources_used=_source_references(search_results),
        )

    return (
        result,
        build_single_mode_trace(
            mode="canon",
            query=query,
            retrieval_candidates=bundle.retrieval_candidates,
            final_evidence=bundle.final_evidence,
            generated_output=result.judgment,
        ),
    )


def run_compare_with_trace(
    *,
    left_query: str,
    right_query: str,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int = DEFAULT_COMPARE_TOP_K,
) -> tuple[CompareResult, RagTraceArtifact]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    left_bundle = retrieve_reranked_bundle(
        query=left_query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=top_k,
    )
    right_bundle = retrieve_reranked_bundle(
        query=right_query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=top_k,
    )

    left_results = left_bundle.final_evidence
    right_results = right_bundle.final_evidence
    if not left_results or not right_results:
        result = CompareResult(
            left_query=left_query,
            right_query=right_query,
            comparison="No relevant sources were found for one or both compare queries.",
            left_sources_used=_source_references(left_results),
            right_sources_used=_source_references(right_results),
        )
    else:
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
        result = CompareResult(
            left_query=left_query,
            right_query=right_query,
            comparison=comparison,
            left_sources_used=_source_references(left_results),
            right_sources_used=_source_references(right_results),
        )

    return (
        result,
        build_pair_mode_trace(
            mode="compare",
            left_query=left_query,
            right_query=right_query,
            left_candidates=left_bundle.retrieval_candidates,
            left_final_evidence=left_bundle.final_evidence,
            right_candidates=right_bundle.retrieval_candidates,
            right_final_evidence=right_bundle.final_evidence,
            generated_output=result.comparison,
        ),
    )


def run_contradict_with_trace(
    *,
    left_query: str,
    right_query: str,
    indexed_chunks: list[IndexedChunk],
    embedding_provider: EmbeddingProvider,
    generation_provider: GenerationProvider,
    top_k: int = DEFAULT_CONTRADICT_TOP_K,
) -> tuple[ContradictionResult, RagTraceArtifact]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    left_bundle = retrieve_reranked_bundle(
        query=left_query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=top_k,
    )
    right_bundle = retrieve_reranked_bundle(
        query=right_query,
        indexed_chunks=indexed_chunks,
        embedding_provider=embedding_provider,
        generation_provider=generation_provider,
        top_k=top_k,
    )

    left_results = left_bundle.final_evidence
    right_results = right_bundle.final_evidence
    if not left_results or not right_results:
        result = ContradictionResult(
            left_query=left_query,
            right_query=right_query,
            judgment="verdict: unclear\nexplanation: Missing sources for one or both sides.",
            left_sources_used=_source_references(left_results),
            right_sources_used=_source_references(right_results),
        )
    else:
        prompt = build_grounded_contradiction_prompt(
            left_query=left_query,
            right_query=right_query,
            left_results=left_results,
            right_results=right_results,
            domain_pack=DEFAULT_DOMAIN_PACK,
        )
        judgment = generation_provider.generate_text(prompt).strip()
        if not judgment:
            raise ValueError("generation provider returned an empty contradiction judgment")
        result = ContradictionResult(
            left_query=left_query,
            right_query=right_query,
            judgment=judgment,
            left_sources_used=_source_references(left_results),
            right_sources_used=_source_references(right_results),
        )

    return (
        result,
        build_pair_mode_trace(
            mode="contradict",
            left_query=left_query,
            right_query=right_query,
            left_candidates=left_bundle.retrieval_candidates,
            left_final_evidence=left_bundle.final_evidence,
            right_candidates=right_bundle.retrieval_candidates,
            right_final_evidence=right_bundle.final_evidence,
            generated_output=result.judgment,
        ),
    )


def build_single_mode_trace(
    *,
    mode: str,
    query: str,
    retrieval_candidates: list[SearchResult],
    final_evidence: list[SearchResult],
    generated_output: str,
) -> RagTraceArtifact:
    return RagTraceArtifact(
        mode=mode,
        query=query,
        retrieval_candidates=_build_evidence_blocks(retrieval_candidates),
        final_evidence=_build_evidence_blocks(final_evidence),
        generated_output=generated_output,
    )


def build_pair_mode_trace(
    *,
    mode: str,
    left_query: str,
    right_query: str,
    left_candidates: list[SearchResult],
    left_final_evidence: list[SearchResult],
    right_candidates: list[SearchResult],
    right_final_evidence: list[SearchResult],
    generated_output: str,
) -> RagTraceArtifact:
    return RagTraceArtifact(
        mode=mode,
        generated_output=generated_output,
        left=TraceSide(
            query=left_query,
            retrieval_candidates=_build_evidence_blocks(left_candidates),
            final_evidence=_build_evidence_blocks(left_final_evidence),
        ),
        right=TraceSide(
            query=right_query,
            retrieval_candidates=_build_evidence_blocks(right_candidates),
            final_evidence=_build_evidence_blocks(right_final_evidence),
        ),
    )


def _build_evidence_blocks(results: list[SearchResult]) -> list[TraceEvidenceBlock]:
    return [
        TraceEvidenceBlock(
            chunk_id=result.indexed_chunk.chunk_id,
            title=result.indexed_chunk.metadata.source_title,
            relative_path=result.indexed_chunk.metadata.document_relative_path,
            chunk_index=result.indexed_chunk.metadata.chunk_index,
            score=round(result.score, 4),
            evidence_block="\n".join(
                [
                    f"title: {result.indexed_chunk.metadata.source_title}",
                    f"path: {result.indexed_chunk.metadata.document_relative_path}",
                    f"chunk_index: {result.indexed_chunk.metadata.chunk_index}",
                    f"excerpt: {format_excerpt(result.indexed_chunk.text, max_length=DEFAULT_TRACE_EXCERPT_LENGTH)}",
                ]
            ),
        )
        for result in results
    ]


def _source_references(results: list[SearchResult]) -> list[SourceReference]:
    return [
        SourceReference(
            title=result.indexed_chunk.metadata.source_title,
            relative_path=result.indexed_chunk.metadata.document_relative_path,
            chunk_index=result.indexed_chunk.metadata.chunk_index,
        )
        for result in results
    ]
