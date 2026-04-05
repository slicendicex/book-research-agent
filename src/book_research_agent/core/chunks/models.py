from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ChunkMetadata:
    document_relative_path: str
    source_title: str
    chunk_index: int
    char_start: int
    char_end: int


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    text: str
    metadata: ChunkMetadata

    @property
    def char_count(self) -> int:
        return len(self.text)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "text": self.text,
            "char_count": self.char_count,
            "metadata": asdict(self.metadata),
        }
