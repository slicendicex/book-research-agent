from __future__ import annotations

from book_research_agent.core.chunks.models import Chunk, ChunkMetadata
from book_research_agent.core.documents.models import Document


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be zero or greater")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[Chunk] = []
    step = chunk_size - chunk_overlap

    for document in documents:
        chunk_index = 0
        text = document.text

        for char_start in range(0, len(text), step):
            char_end = min(char_start + chunk_size, len(text))
            chunk_text = text[char_start:char_end]

            if not chunk_text.strip():
                continue

            chunks.append(
                Chunk(
                    id=f"{document.id}:{chunk_index}",
                    document_id=document.id,
                    text=chunk_text,
                    metadata=ChunkMetadata(
                        document_relative_path=document.metadata.relative_path,
                        source_title=document.title,
                        chunk_index=chunk_index,
                        char_start=char_start,
                        char_end=char_end,
                    ),
                )
            )
            chunk_index += 1

            if char_end >= len(text):
                break

    return chunks
