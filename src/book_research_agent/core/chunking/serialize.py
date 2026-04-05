from __future__ import annotations

import json
from pathlib import Path

from book_research_agent.core.chunks.models import Chunk


def read_chunks_jsonl(input_path: Path) -> list[Chunk]:
    if not input_path.exists():
        return []

    chunks: list[Chunk] = []

    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            chunks.append(Chunk.from_dict(json.loads(line)))

    return chunks


def write_chunks_jsonl(chunks: list[Chunk], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.to_dict(), ensure_ascii=False))
            handle.write("\n")

    return output_path
