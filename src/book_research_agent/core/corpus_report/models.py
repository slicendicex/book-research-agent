from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConceptCandidate:
    text: str
    occurrences: int
    document_count: int


@dataclass(frozen=True)
class ConceptCoOccurrence:
    left: str
    right: str
    document_count: int


@dataclass(frozen=True)
class OrphanNote:
    title: str
    relative_path: str
    best_overlap: float


@dataclass(frozen=True)
class CorpusReport:
    core_concepts: list[ConceptCandidate]
    secondary_concepts: list[ConceptCandidate]
    co_occurrences: list[ConceptCoOccurrence]
    orphan_notes: list[OrphanNote]
