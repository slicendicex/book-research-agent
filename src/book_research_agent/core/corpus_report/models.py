from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MotifCandidate:
    text: str
    occurrences: int
    document_count: int


@dataclass(frozen=True)
class OrphanNote:
    title: str
    relative_path: str
    best_overlap: float


@dataclass(frozen=True)
class CorpusReport:
    top_motifs: list[MotifCandidate]
    emerging_motifs: list[MotifCandidate]
    orphan_notes: list[OrphanNote]
