from __future__ import annotations

from dataclasses import asdict, dataclass

from book_research_agent.core.chunks.models import ChunkMetadata


@dataclass(frozen=True)
class IndexedChunk:
    chunk_id: str
    document_id: str
    text: str
    metadata: ChunkMetadata
    embedding: list[float]
    embedding_model: str

    def to_dict(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "text": self.text,
            "metadata": asdict(self.metadata),
            "embedding": self.embedding,
            "embedding_model": self.embedding_model,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "IndexedChunk":
        metadata = ChunkMetadata(**payload["metadata"])
        embedding = [float(value) for value in payload["embedding"]]
        return cls(
            chunk_id=str(payload["chunk_id"]),
            document_id=str(payload["document_id"]),
            text=str(payload["text"]),
            metadata=metadata,
            embedding=embedding,
            embedding_model=str(payload["embedding_model"]),
        )
