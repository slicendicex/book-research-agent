from __future__ import annotations


GENERATION_OUTPUT_BUDGETS = {
    "reranking": 256,
    "answer": 900,
    "canon": 900,
    "contradict": 900,
    "compare": 1400,
}


def get_generation_output_budget(mode: str) -> int:
    try:
        return GENERATION_OUTPUT_BUDGETS[mode]
    except KeyError as error:
        raise ValueError(f"Unknown generation output budget mode: {mode}") from error
