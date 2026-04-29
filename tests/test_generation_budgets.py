from __future__ import annotations

import unittest

from book_research_agent.core.answering import (
    answer_query,
    canon_query,
    compare_queries,
    contradict_queries,
)
from book_research_agent.core.chunks.models import ChunkMetadata
from book_research_agent.core.generation.budgets import GENERATION_OUTPUT_BUDGETS
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.retrieval import rerank_search_results
from book_research_agent.core.retrieval.search import SearchResult


class StubEmbeddingProvider:
    provider_name = "stub"
    model_name = "stub-model"

    def embed_text(self, text: str, *, input_type: str) -> list[float]:
        mapping = {
            "auditor": [1.0, 0.0],
            "auditor language": [1.0, 0.0],
            "old man": [0.0, 1.0],
            "auditor as protector": [1.0, 0.0],
            "auditor as destroyer": [0.0, 1.0],
        }
        return mapping[text]

    def embed_texts(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        return [self.embed_text(text, input_type=input_type) for text in texts]


class RecordingGenerationProvider:
    provider_name = "recording-generation"
    model_name = "recording-model"

    def __init__(self) -> None:
        self.calls: list[tuple[str, int | None]] = []

    def generate_text(self, prompt: str, *, output_budget: int | None = None) -> str:
        self.calls.append((prompt, output_budget))
        if prompt.startswith("You select existing evidence chunks"):
            return '["R1"]'
        if prompt.startswith("You answer questions"):
            return "answer: grounded\nsupport: source-backed\nlimits: none"
        if prompt.startswith("You produce a short canon-oriented judgment"):
            return (
                "current_canonical_reading: grounded\n"
                "competing_variants: unclear\n"
                "confidence: medium because sources are partial"
            )
        if prompt.startswith("You compare two topics"):
            return (
                "shared_ground: grounded\n"
                "key_differences: grounded\n"
                "tension: grounded\n"
                "limits: none"
            )
        if prompt.startswith("You judge whether two source-grounded claims"):
            return "verdict: in tension\nexplanation: grounded"
        raise AssertionError(f"Unexpected prompt prefix: {prompt[:60]}")


def make_indexed_chunk(
    *,
    chunk_id: str,
    title: str,
    relative_path: str,
    text: str,
    chunk_index: int,
    embedding: list[float],
) -> IndexedChunk:
    return IndexedChunk(
        chunk_id=chunk_id,
        document_id=chunk_id.split(":", maxsplit=1)[0],
        text=text,
        metadata=ChunkMetadata(
            document_relative_path=relative_path,
            source_title=title,
            chunk_index=chunk_index,
            char_start=0,
            char_end=len(text),
        ),
        embedding=embedding,
        embedding_model="stub-model",
    )


def make_indexed_chunks() -> list[IndexedChunk]:
    return [
        make_indexed_chunk(
            chunk_id="doc-a:0",
            title="Auditor Notes",
            relative_path="notes/auditor.md",
            text="The auditor represents order.",
            chunk_index=0,
            embedding=[1.0, 0.0],
        ),
        make_indexed_chunk(
            chunk_id="doc-b:0",
            title="Old Man Notes",
            relative_path="notes/old-man.md",
            text="The old man preserves life.",
            chunk_index=0,
            embedding=[0.0, 1.0],
        ),
    ]


class GenerationBudgetRoutingTests(unittest.TestCase):
    def test_answer_uses_answer_budget(self) -> None:
        provider = RecordingGenerationProvider()

        answer_query(
            query="auditor",
            indexed_chunks=make_indexed_chunks(),
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=provider,
            top_k=1,
        )

        self.assertEqual(provider.calls[-1][1], GENERATION_OUTPUT_BUDGETS["answer"])

    def test_canon_uses_canon_budget(self) -> None:
        provider = RecordingGenerationProvider()

        canon_query(
            query="auditor language",
            indexed_chunks=make_indexed_chunks()[:1],
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=provider,
            top_k=1,
        )

        self.assertEqual(provider.calls[-1][1], GENERATION_OUTPUT_BUDGETS["canon"])

    def test_compare_uses_larger_compare_budget(self) -> None:
        provider = RecordingGenerationProvider()

        compare_queries(
            left_query="auditor",
            right_query="old man",
            indexed_chunks=make_indexed_chunks(),
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=provider,
            top_k=1,
        )

        self.assertEqual(provider.calls[-1][1], GENERATION_OUTPUT_BUDGETS["compare"])

    def test_contradict_uses_contradict_budget(self) -> None:
        provider = RecordingGenerationProvider()

        contradict_queries(
            left_query="auditor as protector",
            right_query="auditor as destroyer",
            indexed_chunks=make_indexed_chunks(),
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=provider,
            top_k=1,
        )

        self.assertEqual(provider.calls[-1][1], GENERATION_OUTPUT_BUDGETS["contradict"])

    def test_reranking_uses_small_reranking_budget(self) -> None:
        provider = RecordingGenerationProvider()
        candidates = [
            SearchResult(indexed_chunk=make_indexed_chunks()[0], score=0.95),
            SearchResult(indexed_chunk=make_indexed_chunks()[1], score=0.90),
        ]

        rerank_search_results(
            query="auditor",
            candidates=candidates,
            generation_provider=provider,
            top_k=1,
        )

        self.assertEqual(provider.calls[-1][1], GENERATION_OUTPUT_BUDGETS["reranking"])


if __name__ == "__main__":
    unittest.main()
