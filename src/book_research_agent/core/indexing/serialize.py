from __future__ import annotations

import json
from pathlib import Path

from book_research_agent.core.indexing.models import IndexedChunk


def read_indexed_chunks_jsonl(input_path: Path) -> list[IndexedChunk]:
    if not input_path.exists():
        return []

    indexed_chunks: list[IndexedChunk] = []

    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            indexed_chunks.append(IndexedChunk.from_dict(json.loads(line)))

    return indexed_chunks


def write_indexed_chunks_jsonl(
    indexed_chunks: list[IndexedChunk],
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for indexed_chunk in indexed_chunks:
            handle.write(json.dumps(indexed_chunk.to_dict(), ensure_ascii=False))
            handle.write("\n")

    return output_path
