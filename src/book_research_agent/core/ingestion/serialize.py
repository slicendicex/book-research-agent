from __future__ import annotations

import json
from pathlib import Path

from book_research_agent.core.documents.models import Document


def read_documents_jsonl(input_path: Path) -> list[Document]:
    if not input_path.exists():
        return []

    documents: list[Document] = []

    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            documents.append(Document.from_dict(json.loads(line)))

    return documents


def write_documents_jsonl(documents: list[Document], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for document in documents:
            handle.write(json.dumps(document.to_dict(), ensure_ascii=False))
            handle.write("\n")

    return output_path
