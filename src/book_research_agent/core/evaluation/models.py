from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalCase:
    id: str
    mode: str
    query: str


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    mode: str
    status: str
    retrieval_count: int
    answer_present: bool
    message: str = ""


@dataclass(frozen=True)
class EvalSummary:
    pass_count: int
    warn_count: int
    fail_count: int
