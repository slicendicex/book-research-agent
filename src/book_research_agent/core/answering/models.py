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


@dataclass(frozen=True)
class CompareResult:
    left_query: str
    right_query: str
    comparison: str
    left_sources_used: list[SourceReference]
    right_sources_used: list[SourceReference]


@dataclass(frozen=True)
class ContradictionResult:
    left_query: str
    right_query: str
    judgment: str
    left_sources_used: list[SourceReference]
    right_sources_used: list[SourceReference]
