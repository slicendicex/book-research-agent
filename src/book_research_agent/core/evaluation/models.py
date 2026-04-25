from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class EvalCase:
    id: str
    mode: str
    query: str
    notes: str = ""


@dataclass(frozen=True)
class EvalRetrievalSnapshot:
    query: str
    top_paths: list[str]
    top_titles: list[str]
    top_chunk_ids: list[str]
    top_scores: list[float]
    unique_document_count: int
    top_path_repeat_count: int
    duplicate_like_count: int
    score_spread: float


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    mode: str
    status: str
    retrieval_count: int
    answer_present: bool
    message: str = ""
    retrieval_snapshots: list[EvalRetrievalSnapshot] = field(default_factory=list)


@dataclass(frozen=True)
class EvalSummary:
    pass_count: int
    warn_count: int
    fail_count: int


@dataclass(frozen=True)
class EvalRunReport:
    summary: EvalSummary
    results: list[EvalResult]


@dataclass(frozen=True)
class EvalCaseDiff:
    case_id: str
    mode: str
    status_before: str | None
    status_after: str | None
    retrieval_count_before: int | None
    retrieval_count_after: int | None
    top_paths_before: list[list[str]]
    top_paths_after: list[list[str]]
    top_scores_before: list[list[float]]
    top_scores_after: list[list[float]]
    unique_document_count_before: list[int]
    unique_document_count_after: list[int]
    duplicate_like_count_before: list[int]
    duplicate_like_count_after: list[int]


@dataclass(frozen=True)
class EvalRunDiff:
    before_path: Path
    after_path: Path
    pass_delta: int
    warn_delta: int
    fail_delta: int
    changed_cases: list[EvalCaseDiff]
