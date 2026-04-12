from .compare import compare_queries
from .contradiction import contradict_queries
from .canon import canon_query
from .models import (
    AnswerResult,
    CanonResult,
    CompareResult,
    ContradictionResult,
    SourceReference,
)
from .prompting import (
    build_grounded_answer_prompt,
    build_grounded_canon_prompt,
    build_grounded_compare_prompt,
    build_grounded_contradiction_prompt,
)
from .service import answer_query

__all__ = [
    "AnswerResult",
    "CanonResult",
    "CompareResult",
    "ContradictionResult",
    "SourceReference",
    "answer_query",
    "build_grounded_canon_prompt",
    "build_grounded_compare_prompt",
    "build_grounded_contradiction_prompt",
    "build_grounded_answer_prompt",
    "canon_query",
    "compare_queries",
    "contradict_queries",
]
