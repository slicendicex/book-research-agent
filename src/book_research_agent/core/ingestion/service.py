from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from book_research_agent.core.documents.models import Document
from book_research_agent.core.ingestion.loaders import (
    is_supported_document,
    iter_source_files,
    load_document,
)


@dataclass(frozen=True)
class IngestionResult:
    documents: list[Document]
    scanned_files: int
    supported_files: int
    skipped_files: int
    produced_documents: int


def ingest_documents(input_dir: Path) -> IngestionResult:
    documents: list[Document] = []
    scanned_files = 0
    supported_files = 0
    skipped_files = 0

    for path in iter_source_files(input_dir):
        scanned_files += 1

        if not is_supported_document(path):
            skipped_files += 1
            continue

        supported_files += 1

        try:
            document = load_document(path, input_dir)
        except (OSError, UnicodeDecodeError, ValueError):
            skipped_files += 1
            continue

        documents.append(document)

    return IngestionResult(
        documents=documents,
        scanned_files=scanned_files,
        supported_files=supported_files,
        skipped_files=skipped_files,
        produced_documents=len(documents),
    )
