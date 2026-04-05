from __future__ import annotations

from book_research_agent.core.chunks.models import Chunk
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.providers.base import EmbeddingProvider


def build_chunk_index(
    chunks: list[Chunk],
    *,
    embedding_provider: EmbeddingProvider,
    embedding_model: str,
    batch_size: int = 32,
) -> list[IndexedChunk]:
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    indexed_chunks: list[IndexedChunk] = []

    for batch_start in range(0, len(chunks), batch_size):
        batch = chunks[batch_start : batch_start + batch_size]
        embeddings = embedding_provider.embed_texts(
            [chunk.text for chunk in batch],
            input_type="search_document",
        )

        for chunk, embedding in zip(batch, embeddings, strict=True):
            indexed_chunks.append(
                IndexedChunk(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    metadata=chunk.metadata,
                    embedding=embedding,
                    embedding_model=embedding_model,
                )
            )

    return indexed_chunks
