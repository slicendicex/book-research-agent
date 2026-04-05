from __future__ import annotations

import json
from pathlib import Path

from book_research_agent.core.chunks.models import Chunk


def write_chunks_jsonl(chunks: list[Chunk], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.to_dict(), ensure_ascii=False))
            handle.write("\n")

    return output_path
