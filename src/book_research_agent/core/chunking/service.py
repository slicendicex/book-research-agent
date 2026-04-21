from __future__ import annotations

import re

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

    for document in documents:
        chunk_index = 0
        paragraph_spans = _split_paragraph_spans(document.text)
        pending_spans: list[tuple[int, int]] = []

        for paragraph_start, paragraph_end in paragraph_spans:
            paragraph_length = paragraph_end - paragraph_start

            if paragraph_length > chunk_size:
                if pending_spans:
                    chunks.append(_make_chunk(document, pending_spans, chunk_index))
                    chunk_index += 1
                    pending_spans = []

                oversized_chunks, chunk_index = _split_oversized_paragraph(
                    document,
                    paragraph_start=paragraph_start,
                    paragraph_end=paragraph_end,
                    chunk_index=chunk_index,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
                chunks.extend(oversized_chunks)
                continue

            candidate_spans = pending_spans + [(paragraph_start, paragraph_end)]
            if _spans_char_length(candidate_spans) <= chunk_size:
                pending_spans = candidate_spans
                continue

            if pending_spans:
                chunks.append(_make_chunk(document, pending_spans, chunk_index))
                chunk_index += 1

            overlap_spans = _build_overlap_spans(
                pending_spans,
                overlap_chars=chunk_overlap,
            )
            pending_spans = overlap_spans + [(paragraph_start, paragraph_end)]
            while _spans_char_length(pending_spans) > chunk_size:
                pending_spans = pending_spans[1:]

        if pending_spans:
            chunks.append(_make_chunk(document, pending_spans, chunk_index))
            chunk_index += 1

    return chunks


def _split_paragraph_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    cursor = 0

    for match in re.finditer(r"\n\s*\n+", text):
        paragraph = text[cursor:match.start()]
        if paragraph.strip():
            spans.append((cursor, match.start()))
        cursor = match.end()

    if text[cursor:].strip():
        spans.append((cursor, len(text)))

    return spans


def _build_overlap_spans(
    spans: list[tuple[int, int]],
    *,
    overlap_chars: int,
) -> list[tuple[int, int]]:
    if overlap_chars <= 0 or not spans:
        return []

    overlap_spans: list[tuple[int, int]] = []
    for start_index in range(len(spans) - 1, -1, -1):
        candidate = spans[start_index:]
        if _spans_char_length(candidate) > overlap_chars:
            break
        overlap_spans = candidate

    return overlap_spans


def _split_oversized_paragraph(
    document: Document,
    *,
    paragraph_start: int,
    paragraph_end: int,
    chunk_index: int,
    chunk_size: int,
    chunk_overlap: int,
) -> tuple[list[Chunk], int]:
    oversized_chunks: list[Chunk] = []
    step = chunk_size - chunk_overlap

    for char_start in range(paragraph_start, paragraph_end, step):
        char_end = min(char_start + chunk_size, paragraph_end)
        if not document.text[char_start:char_end].strip():
            continue

        oversized_chunks.append(
            Chunk(
                id=f"{document.id}:{chunk_index}",
                document_id=document.id,
                text=document.text[char_start:char_end],
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

        if char_end >= paragraph_end:
            break

    return oversized_chunks, chunk_index


def _make_chunk(
    document: Document,
    spans: list[tuple[int, int]],
    chunk_index: int,
) -> Chunk:
    char_start = spans[0][0]
    char_end = spans[-1][1]
    return Chunk(
        id=f"{document.id}:{chunk_index}",
        document_id=document.id,
        text=document.text[char_start:char_end],
        metadata=ChunkMetadata(
            document_relative_path=document.metadata.relative_path,
            source_title=document.title,
            chunk_index=chunk_index,
            char_start=char_start,
            char_end=char_end,
        ),
    )


def _spans_char_length(spans: list[tuple[int, int]]) -> int:
    if not spans:
        return 0
    return spans[-1][1] - spans[0][0]
