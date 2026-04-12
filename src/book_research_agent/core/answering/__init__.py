from .compare import compare_queries
from .contradiction import contradict_queries
from .models import AnswerResult, CompareResult, ContradictionResult, SourceReference
from .prompting import (
    build_grounded_answer_prompt,
    build_grounded_compare_prompt,
    build_grounded_contradiction_prompt,
)
from .service import answer_query

__all__ = [
    "AnswerResult",
    "CompareResult",
    "ContradictionResult",
    "SourceReference",
    "answer_query",
    "build_grounded_compare_prompt",
    "build_grounded_contradiction_prompt",
    "build_grounded_answer_prompt",
    "compare_queries",
    "contradict_queries",
]
