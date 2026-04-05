from __future__ import annotations

import unittest

from book_research_agent.core.chunks.models import ChunkMetadata
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.retrieval.search import cosine_similarity, search_index


class StubEmbeddingProvider:
    provider_name = "stub"
    model_name = "stub-model"

    def embed_text(self, text: str, *, input_type: str) -> list[float]:
        mapping = {
            "alpha query": [1.0, 0.0],
            "beta query": [0.0, 1.0],
        }
        return mapping[text]

    def embed_texts(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        return [self.embed_text(text, input_type=input_type) for text in texts]


def make_indexed_chunk(
    chunk_id: str,
    title: str,
    relative_path: str,
    embedding: list[float],
) -> IndexedChunk:
    return IndexedChunk(
        chunk_id=chunk_id,
        document_id=chunk_id.split(":", maxsplit=1)[0],
        text=f"{title} body text",
        metadata=ChunkMetadata(
            document_relative_path=relative_path,
            source_title=title,
            chunk_index=int(chunk_id.rsplit(":", maxsplit=1)[1]),
            char_start=0,
            char_end=10,
        ),
        embedding=embedding,
        embedding_model="embed-v4.0",
    )


class RetrievalSearchTests(unittest.TestCase):
    def test_cosine_similarity(self) -> None:
        score = cosine_similarity([1.0, 0.0], [0.5, 0.5])
        self.assertAlmostEqual(score, 0.70710678, places=6)

    def test_top_k_search_returns_best_matches(self) -> None:
        indexed_chunks = [
            make_indexed_chunk("doc-a:0", "Alpha", "alpha.md", [1.0, 0.0]),
            make_indexed_chunk("doc-b:0", "Beta", "beta.md", [0.0, 1.0]),
            make_indexed_chunk("doc-c:0", "Mixed", "mixed.md", [0.8, 0.2]),
        ]

        results = search_index(
            query="alpha query",
            indexed_chunks=indexed_chunks,
            embedding_provider=StubEmbeddingProvider(),
            top_k=2,
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].indexed_chunk.chunk_id, "doc-a:0")
        self.assertEqual(results[1].indexed_chunk.chunk_id, "doc-c:0")
        self.assertGreater(results[0].score, results[1].score)


if __name__ == "__main__":
    unittest.main()
