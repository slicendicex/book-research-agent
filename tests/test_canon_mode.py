from __future__ import annotations

import unittest

from book_research_agent.core.answering import (
    CanonResult,
    SourceReference,
    build_grounded_canon_prompt,
    canon_query,
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
            "auditor language": [1.0, 0.0],
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
        return (
            "current_canonical_reading: The auditor language is tied to order.\n"
            "competing_variants: unclear from the provided sources.\n"
            "confidence: medium because one source supports the reading."
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


class CanonModeTests(unittest.TestCase):
    def test_canon_prompt_is_grounded_cautious_and_structured(self) -> None:
        prompt = build_grounded_canon_prompt(
            query="auditor language",
            search_results=[
                make_search_result(
                    chunk_id="doc-a:0",
                    title="Auditor Notes",
                    relative_path="notes/auditor.md",
                    text="The auditor speaks in the language of order.",
                    chunk_index=0,
                )
            ],
            domain_pack=DEFAULT_DOMAIN_PACK,
        )

        self.assertIn("using only the provided sources", prompt)
        self.assertIn("Treat retrieved sources as the primary evidence.", prompt)
        self.assertIn("Prefer 'unclear' over overclaiming canon", prompt)
        self.assertIn("Do not convert interpretation into canon", prompt)
        self.assertIn("current_canonical_reading:", prompt)
        self.assertIn("competing_variants:", prompt)
        self.assertIn("confidence:", prompt)
        self.assertIn("Do not invent facts, citations, or unsupported canon.", prompt)
        self.assertIn("Canon query: auditor language", prompt)
        self.assertIn("title: Auditor Notes", prompt)
        self.assertIn("Domain guidance:", prompt)
        self.assertIn("Auditor", prompt)
        self.assertIn("canon", prompt)

    def test_canon_query_returns_judgment_and_sources(self) -> None:
        generation_provider = StubGenerationProvider()

        result = canon_query(
            query="auditor language",
            indexed_chunks=[
                make_indexed_chunk(
                    chunk_id="doc-a:0",
                    title="Auditor Notes",
                    relative_path="notes/auditor.md",
                    text="The auditor speaks in the language of order.",
                    chunk_index=0,
                    embedding=[1.0, 0.0],
                )
            ],
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=generation_provider,
            top_k=1,
        )

        self.assertEqual(
            result,
            CanonResult(
                query="auditor language",
                judgment=(
                    "current_canonical_reading: The auditor language is tied to order.\n"
                    "competing_variants: unclear from the provided sources.\n"
                    "confidence: medium because one source supports the reading."
                ),
                sources_used=[
                    SourceReference(
                        title="Auditor Notes",
                        relative_path="notes/auditor.md",
                        chunk_index=0,
                    )
                ],
            ),
        )
        self.assertEqual(len(generation_provider.prompts), 2)
        canon_prompt = generation_provider.prompts[-1]
        self.assertIn("Canon query: auditor language", canon_prompt)
        self.assertIn("Prefer 'unclear' over overclaiming canon", canon_prompt)
        self.assertIn("Domain guidance:", canon_prompt)

    def test_canon_query_returns_unclear_when_no_sources_are_found(self) -> None:
        result = canon_query(
            query="auditor language",
            indexed_chunks=[],
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=StubGenerationProvider(),
            top_k=1,
        )

        self.assertEqual(result.query, "auditor language")
        self.assertIn("current_canonical_reading: unclear", result.judgment)
        self.assertEqual(result.sources_used, [])


if __name__ == "__main__":
    unittest.main()
