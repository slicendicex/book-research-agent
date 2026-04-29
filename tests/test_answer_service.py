from __future__ import annotations

import unittest

from book_research_agent.core.answering import AnswerResult, SourceReference, answer_query
from book_research_agent.core.chunks.models import ChunkMetadata
from book_research_agent.core.indexing.models import IndexedChunk


class StubEmbeddingProvider:
    provider_name = "stub"
    model_name = "stub-model"

    def embed_text(self, text: str, *, input_type: str) -> list[float]:
        mapping = {
            "auditor question": [1.0, 0.0],
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
        return "The auditor represents oversight and accountability."


def make_indexed_chunk(
    *,
    chunk_id: str,
    document_id: str,
    title: str,
    relative_path: str,
    text: str,
    chunk_index: int,
    embedding: list[float],
) -> IndexedChunk:
    return IndexedChunk(
        chunk_id=chunk_id,
        document_id=document_id,
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


class AnswerServiceTests(unittest.TestCase):
    def test_answer_query_returns_grounded_answer_and_visible_sources(self) -> None:
        generation_provider = StubGenerationProvider()
        result = answer_query(
            query="auditor question",
            indexed_chunks=[
                make_indexed_chunk(
                    chunk_id="doc-1:0",
                    document_id="doc-1",
                    title="Auditor Notes",
                    relative_path="notes/auditor.md",
                    text="The auditor represents oversight and accountability.",
                    chunk_index=0,
                    embedding=[1.0, 0.0],
                ),
                make_indexed_chunk(
                    chunk_id="doc-2:0",
                    document_id="doc-2",
                    title="Appendix",
                    relative_path="notes/appendix.md",
                    text="Appendix details appear here.",
                    chunk_index=0,
                    embedding=[0.2, 0.8],
                ),
            ],
            embedding_provider=StubEmbeddingProvider(),
            generation_provider=generation_provider,
            top_k=1,
        )

        self.assertEqual(
            result,
            AnswerResult(
                query="auditor question",
                answer="The auditor represents oversight and accountability.",
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
        self.assertIn("Return only a JSON array of candidate ids", generation_provider.prompts[0])
        answer_prompt = generation_provider.prompts[-1]
        self.assertIn("Question: auditor question", answer_prompt)
        self.assertIn("title: Auditor Notes", answer_prompt)
        self.assertIn("Prefer specific source-backed details", answer_prompt)
        self.assertIn("limits: <uncertainty or missing evidence, or none>", answer_prompt)
        self.assertIn("Domain guidance:", answer_prompt)
        self.assertIn("Auditor", answer_prompt)
        self.assertIn("Do not invent facts, citations, or canon.", answer_prompt)


if __name__ == "__main__":
    unittest.main()
