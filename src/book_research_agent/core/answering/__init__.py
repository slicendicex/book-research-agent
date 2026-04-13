from .compare import compare_queries
from .contradiction import contradict_queries
from .canon import canon_query
from .defaults import (
    DEFAULT_ANSWER_TOP_K,
    DEFAULT_CANON_TOP_K,
    DEFAULT_COMPARE_TOP_K,
    DEFAULT_CONTRADICT_TOP_K,
)
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
    "DEFAULT_ANSWER_TOP_K",
    "DEFAULT_CANON_TOP_K",
    "DEFAULT_COMPARE_TOP_K",
    "DEFAULT_CONTRADICT_TOP_K",
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
