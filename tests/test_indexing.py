from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from book_research_agent.core.chunks.models import Chunk, ChunkMetadata
from book_research_agent.core.config.settings import RuntimeSettings
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.indexing.serialize import (
    read_indexed_chunks_jsonl,
    write_indexed_chunks_jsonl,
)
from book_research_agent.core.indexing.service import build_chunk_index
from book_research_agent.core.providers.cohere_embeddings import CohereEmbeddingProvider
from book_research_agent.core.providers.factory import create_embedding_provider
from book_research_agent.core.providers.openai_embeddings import OpenAIEmbeddingProvider


class StubEmbeddingProvider:
    provider_name = "stub"
    model_name = "stub-model"

    def embed_text(self, text: str, *, input_type: str) -> list[float]:
        return self.embed_texts([text], input_type=input_type)[0]

    def embed_texts(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        return [[float(len(text)), 1.0 if input_type == "search_query" else 0.0] for text in texts]


def make_chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(
        id=chunk_id,
        document_id="doc-1",
        text=text,
        metadata=ChunkMetadata(
            document_relative_path="notes/example.md",
            source_title="Example",
            chunk_index=int(chunk_id.rsplit(":", maxsplit=1)[1]),
            char_start=0,
            char_end=len(text),
        ),
    )


class IndexingTests(unittest.TestCase):
    def test_indexed_chunk_roundtrip_jsonl(self) -> None:
        indexed_chunk = IndexedChunk(
            chunk_id="doc-1:0",
            document_id="doc-1",
            text="alpha",
            metadata=ChunkMetadata(
                document_relative_path="notes/example.md",
                source_title="Example",
                chunk_index=0,
                char_start=0,
                char_end=5,
            ),
            embedding=[0.1, 0.2],
            embedding_model="embed-v4.0",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "chunk_index.jsonl"
            write_indexed_chunks_jsonl([indexed_chunk], output_path)
            loaded = read_indexed_chunks_jsonl(output_path)

        self.assertEqual(loaded, [indexed_chunk])

    def test_build_chunk_index_batches_embeddings(self) -> None:
        chunks = [make_chunk("doc-1:0", "alpha"), make_chunk("doc-1:1", "beta")]

        indexed_chunks = build_chunk_index(
            chunks,
            embedding_provider=StubEmbeddingProvider(),
            embedding_model="stub-model",
            batch_size=1,
        )

        self.assertEqual(len(indexed_chunks), 2)
        self.assertEqual(indexed_chunks[0].chunk_id, "doc-1:0")
        self.assertEqual(indexed_chunks[0].embedding_model, "stub-model")

    def test_provider_factory_returns_cohere_embedding_provider(self) -> None:
        settings = RuntimeSettings(
            environment="test",
            embedding_provider="cohere",
            embedding_model="embed-v4.0",
            generation_provider="dummy",
            generation_model="dummy-generation-v1",
            has_cohere_api_key=True,
            has_openai_api_key=False,
            has_gemini_api_key=False,
            has_anthropic_api_key=False,
        )

        with patch.dict(os.environ, {"COHERE_API_KEY": "test-key"}, clear=False):
            provider = create_embedding_provider(settings)

        self.assertIsInstance(provider, CohereEmbeddingProvider)
        self.assertEqual(provider.model_name, "embed-v4.0")

    def test_provider_factory_returns_openai_embedding_provider(self) -> None:
        settings = RuntimeSettings(
            environment="test",
            embedding_provider="openai",
            embedding_model="text-embedding-3-small",
            generation_provider="dummy",
            generation_model="dummy-generation-v1",
            has_cohere_api_key=False,
            has_openai_api_key=True,
            has_gemini_api_key=False,
            has_anthropic_api_key=False,
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            provider = create_embedding_provider(settings)

        self.assertIsInstance(provider, OpenAIEmbeddingProvider)
        self.assertEqual(provider.model_name, "text-embedding-3-small")

    def test_cohere_provider_raises_when_api_key_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                ValueError,
                "COHERE_API_KEY is required",
            ):
                CohereEmbeddingProvider(
                    provider_name="cohere",
                    model_name="embed-v4.0",
                )

    def test_openai_provider_raises_when_api_key_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                ValueError,
                "OPENAI_API_KEY is required",
            ):
                OpenAIEmbeddingProvider(
                    provider_name="openai",
                    model_name="text-embedding-3-small",
                )

    def test_openai_embedding_provider_returns_embeddings(self) -> None:
        response = type(
            "EmbeddingResponse",
            (),
            {
                "data": [
                    type("EmbeddingItem", (), {"embedding": [0.1, 0.2]})(),
                    type("EmbeddingItem", (), {"embedding": [0.3, 0.4]})(),
                ]
            },
        )()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch(
                "book_research_agent.core.providers.openai_embeddings.OpenAI"
            ) as client_cls:
                client_cls.return_value.embeddings.create.return_value = response
                provider = OpenAIEmbeddingProvider(
                    provider_name="openai",
                    model_name="text-embedding-3-small",
                )

        embeddings = provider.embed_texts(["alpha", "beta"], input_type="search_document")
        self.assertEqual(embeddings, [[0.1, 0.2], [0.3, 0.4]])


if __name__ == "__main__":
    unittest.main()
