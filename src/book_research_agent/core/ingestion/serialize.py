from __future__ import annotations

import json
from pathlib import Path

from book_research_agent.core.documents.models import Document


def write_documents_jsonl(documents: list[Document], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for document in documents:
            handle.write(json.dumps(document.to_dict(), ensure_ascii=False))
            handle.write("\n")

    return output_path
