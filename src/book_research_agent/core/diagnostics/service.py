from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from book_research_agent.core.chunking.serialize import read_chunks_jsonl
from book_research_agent.core.chunks.models import Chunk
from book_research_agent.core.documents.models import Document
from book_research_agent.core.indexing.models import IndexedChunk
from book_research_agent.core.indexing.serialize import read_indexed_chunks_jsonl
from book_research_agent.core.ingestion.serialize import read_documents_jsonl


class DiagnosticLookupError(LookupError):
    pass


@dataclass(frozen=True)
class CorpusStats:
    documents_path: Path
    chunks_path: Path
    index_path: Path
    document_count: int
    chunk_count: int
    indexed_chunk_count: int


def get_corpus_stats(
    documents_path: Path,
    chunks_path: Path,
    index_path: Path,
) -> CorpusStats:
    return CorpusStats(
        documents_path=documents_path,
        chunks_path=chunks_path,
        index_path=index_path,
        document_count=len(_read_documents(documents_path)),
        chunk_count=len(_read_chunks(chunks_path)),
        indexed_chunk_count=len(_read_indexed_chunks(index_path)),
    )


def get_document_by_path(documents_path: Path, relative_path: str) -> Document:
    for document in _read_documents(documents_path):
        if document.metadata.relative_path == relative_path:
            return document
    raise DiagnosticLookupError(f"document not found: {relative_path}")


def get_chunk_by_id(chunks_path: Path, chunk_id: str) -> Chunk:
    for chunk in _read_chunks(chunks_path):
        if chunk.id == chunk_id:
            return chunk
    raise DiagnosticLookupError(f"chunk not found: {chunk_id}")


def get_indexed_chunk_by_id(index_path: Path, chunk_id: str) -> IndexedChunk:
    for indexed_chunk in _read_indexed_chunks(index_path):
        if indexed_chunk.chunk_id == chunk_id:
            return indexed_chunk
    raise DiagnosticLookupError(f"indexed chunk not found: {chunk_id}")


def _read_documents(documents_path: Path) -> list[Document]:
    _require_file(documents_path)
    return read_documents_jsonl(documents_path)


def _read_chunks(chunks_path: Path) -> list[Chunk]:
    _require_file(chunks_path)
    return read_chunks_jsonl(chunks_path)


def _read_indexed_chunks(index_path: Path) -> list[IndexedChunk]:
    _require_file(index_path)
    return read_indexed_chunks_jsonl(index_path)


def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"file not found: {path}")
