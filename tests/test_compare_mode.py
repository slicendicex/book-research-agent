from __future__ import annotations

import unittest

from book_research_agent.core.answering import (
    CompareResult,
    SourceReference,
    build_grounded_compare_prompt,
    compare_queries,
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
            "auditor": [1.0, 0.0],
            "old man": [0.0, 1.0],
        }
        return mapping[text]

    def embed_texts(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        return [self.embed_text(text, input_type=input_type) for text in texts]


class StubGenerationProvider:
    provider_name = "stub-generation"
    model_name = "stub-generation-model"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate_text(self, prompt: str, *, output_budget: int | None = None) -> str:
        self.prompts.append(prompt)
        if prompt.startswith("You select existing evidence chunks"):
            return '["R1"]'
        return "Both relate to order, but the old man preserves while the auditor judges."


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


class CompareModeTests(unittest.TestCase):
    def test_compare_prompt_includes_queries_sources_and_domain_guidance(self) -> None:
        prompt = build_grounded_compare_prompt(
            left_query="auditor",
            right_query="old man",
            left_results=[
                make_search_result(
                    chunk_id="doc-a:0",
                    title="Auditor Notes",
                    relative_path="notes/auditor.md",
                    text="The auditor judges order.",
                    chunk_index=0,
                )
            ],
            right_results=[
                make_search_result(
                    chunk_id="doc-b:0",
                    title="Old Man Notes",
                    relative_path="notes/old-man.md",
                    text="The old man preserves life.",
                    chunk_index=0,
                )
            ],
            domain_pack=DEFAULT_DOMAIN_PACK,
        )

        self.assertIn("using only the provided sources", prompt)
        self.assertIn("shared themes, key differences, main tension", prompt)
        self.assertIn("concrete source-backed similarities and differences", prompt)
        self.assertIn(
            "Write the substantive content in the same language as the user's queries.",
            prompt,
        )
        self.assertIn(
            "Keep the section labels exactly as written in the response shape below.",
            prompt,
        )
        self.assertIn("shared_ground, key_differences, tension, limits", prompt)
        self.assertIn("Left query: auditor", prompt)
        self.assertIn("Right query: old man", prompt)
        self.assertIn("title: Auditor Notes", prompt)
        self.assertIn("title: Old Man Notes", prompt)
        self.assertIn("Domain guidance:", prompt)

    def test_compare_queries_returns_comparison_and_sources_for_both_sides(self) -> None:
        generation_provider = StubGenerationProvider()

        result = compare_queries(
            left_query="auditor",
            right_query="old man",
            indexed_chunks=[
                make_indexed_chunk(
                    chunk_id="doc-a:0",
                    title="Auditor Notes",
                    relative_path="notes/auditor.md",
                    text="The auditor judges order.",
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
            ],
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=generation_provider,
            top_k=1,
        )

        self.assertEqual(
            result,
            CompareResult(
                left_query="auditor",
                right_query="old man",
                comparison=(
                    "Both relate to order, but the old man preserves while the auditor judges."
                ),
                left_sources_used=[
                    SourceReference(
                        title="Auditor Notes",
                        relative_path="notes/auditor.md",
                        chunk_index=0,
                    )
                ],
                right_sources_used=[
                    SourceReference(
                        title="Old Man Notes",
                        relative_path="notes/old-man.md",
                        chunk_index=0,
                    )
                ],
            ),
        )
        self.assertEqual(len(generation_provider.prompts), 3)
        compare_prompt = generation_provider.prompts[-1]
        self.assertIn("Left query: auditor", compare_prompt)
        self.assertIn("Right query: old man", compare_prompt)
        self.assertIn("Domain guidance:", compare_prompt)


if __name__ == "__main__":
    unittest.main()
