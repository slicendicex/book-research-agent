from __future__ import annotations

from dataclasses import dataclass, field


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
