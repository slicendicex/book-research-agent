from __future__ import annotations

import hashlib
from pathlib import Path

from book_research_agent.core.documents.models import Document, DocumentMetadata
from book_research_agent.core.ingestion.normalize import normalize_text


SUPPORTED_EXTENSIONS = {".md", ".txt"}


def is_supported_document(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def iter_source_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []

    return sorted(path for path in input_dir.rglob("*") if path.is_file())


def load_document(path: Path, input_dir: Path) -> Document:
    raw_text = path.read_text(encoding="utf-8-sig")
    text = normalize_text(raw_text)
    relative_path = path.relative_to(input_dir).as_posix()
    document_id = hashlib.sha1(relative_path.encode("utf-8")).hexdigest()
    content_sha1 = hashlib.sha1(text.encode("utf-8")).hexdigest()

    return Document(
        id=document_id,
        title=extract_title(path, text),
        text=text,
        metadata=DocumentMetadata(
            source_kind="local_file",
            source_path=str(path.resolve()),
            relative_path=relative_path,
            file_extension=path.suffix.lower(),
            content_sha1=content_sha1,
        ),
    )


def extract_title(path: Path, text: str) -> str:
    if path.suffix.lower() == ".md":
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:].strip()
                if title:
                    return title

    return path.stem
