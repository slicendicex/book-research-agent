from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DocumentMetadata:
    source_kind: str
    source_path: str
    relative_path: str
    file_extension: str
    content_sha1: str


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    text: str
    metadata: DocumentMetadata

    @property
    def char_count(self) -> int:
        return len(self.text)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "char_count": self.char_count,
            "metadata": asdict(self.metadata),
        }
