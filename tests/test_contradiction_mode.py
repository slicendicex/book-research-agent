from __future__ import annotations

import unittest

from book_research_agent.core.answering import (
    ContradictionResult,
    SourceReference,
    build_grounded_contradiction_prompt,
    contradict_queries,
)
from book_research_agent.core.chunks.models import ChunkMetadata
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.retrieval import SearchResult
from book_research_agent.domain import DEFAULT_DOMAIN_PACK


class StubEmbeddingProvider:
    provider_name = "stub"
    model_name = "stub-model"

    def embed_text(self, text: str, *, input_type: str) -> list[float]:
        mapping = {
            "auditor as protector": [1.0, 0.0],
            "auditor as destroyer": [0.0, 1.0],
        }
        return mapping[text]

    def embed_texts(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        return [self.embed_text(text, input_type=input_type) for text in texts]


class StubGenerationProvider:
    provider_name = "stub-generation"
    model_name = "stub-generation-model"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate_text(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return (
            "verdict: in tension\n"
            "explanation: The sources support both protective intent and destructive effects."
        )


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
        embedding_model="embed-v4.0",
    )


def make_search_result(
    *,
    chunk_id: str,
    title: str,
    relative_path: str,
    text: str,
    chunk_index: int,
) -> SearchResult:
    return SearchResult(
        indexed_chunk=make_indexed_chunk(
            chunk_id=chunk_id,
            title=title,
            relative_path=relative_path,
            text=text,
            chunk_index=chunk_index,
            embedding=[1.0, 0.0],
        ),
        score=0.95,
    )


class ContradictionModeTests(unittest.TestCase):
    def test_contradiction_prompt_is_cautious_grounded_and_structured(self) -> None:
        prompt = build_grounded_contradiction_prompt(
            left_query="auditor as protector",
            right_query="auditor as destroyer",
            left_results=[
                make_search_result(
                    chunk_id="doc-a:0",
                    title="Protector Notes",
                    relative_path="notes/protector.md",
                    text="The auditor preserves order.",
                    chunk_index=0,
                )
            ],
            right_results=[
                make_search_result(
                    chunk_id="doc-b:0",
                    title="Destroyer Notes",
                    relative_path="notes/destroyer.md",
                    text="The auditor removes what moves.",
                    chunk_index=0,
                )
            ],
            domain_pack=DEFAULT_DOMAIN_PACK,
        )

        self.assertIn("Use only the provided sources.", prompt)
        self.assertIn("aligned, in tension, contradictory, or unclear", prompt)
        self.assertIn("prefer 'in tension' or 'unclear'", prompt)
        self.assertIn("weak evidence as unclear rather than contradiction", prompt)
        self.assertIn("verdict: <aligned|in tension|contradictory|unclear>", prompt)
        self.assertIn("Left claim/query: auditor as protector", prompt)
        self.assertIn("Right claim/query: auditor as destroyer", prompt)
        self.assertIn("title: Protector Notes", prompt)
        self.assertIn("title: Destroyer Notes", prompt)
        self.assertIn("Domain guidance:", prompt)

    def test_contradict_queries_returns_judgment_and_sources_for_both_sides(self) -> None:
        generation_provider = StubGenerationProvider()

        result = contradict_queries(
            left_query="auditor as protector",
            right_query="auditor as destroyer",
            indexed_chunks=[
                make_indexed_chunk(
                    chunk_id="doc-a:0",
                    title="Protector Notes",
                    relative_path="notes/protector.md",
                    text="The auditor preserves order.",
                    chunk_index=0,
                    embedding=[1.0, 0.0],
                ),
                make_indexed_chunk(
                    chunk_id="doc-b:0",
                    title="Destroyer Notes",
                    relative_path="notes/destroyer.md",
                    text="The auditor removes what moves.",
                    chunk_index=0,
                    embedding=[0.0, 1.0],
                ),
            ],
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=generation_provider,
            top_k=1,
        )

        self.assertEqual(
            result,
            ContradictionResult(
                left_query="auditor as protector",
                right_query="auditor as destroyer",
                judgment=(
                    "verdict: in tension\n"
                    "explanation: The sources support both protective intent and destructive effects."
                ),
                left_sources_used=[
                    SourceReference(
                        title="Protector Notes",
                        relative_path="notes/protector.md",
                        chunk_index=0,
                    )
                ],
                right_sources_used=[
                    SourceReference(
                        title="Destroyer Notes",
                        relative_path="notes/destroyer.md",
                        chunk_index=0,
                    )
                ],
            ),
        )
        self.assertEqual(len(generation_provider.prompts), 1)
        self.assertIn("Left claim/query: auditor as protector", generation_provider.prompts[0])
        self.assertIn("Right claim/query: auditor as destroyer", generation_provider.prompts[0])
        self.assertIn("prefer 'in tension' or 'unclear'", generation_provider.prompts[0])


if __name__ == "__main__":
    unittest.main()
