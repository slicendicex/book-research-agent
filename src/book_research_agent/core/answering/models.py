from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceReference:
    title: str
    relative_path: str
    chunk_index: int


@dataclass(frozen=True)
class AnswerResult:
    query: str
    answer: str
    sources_used: list[SourceReference]
