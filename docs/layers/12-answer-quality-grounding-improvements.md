# Layer 12 — Answer Quality / Grounding Improvements

## Purpose

Improve the quality and grounding of the existing answer-facing modes without changing the core retrieval/indexing architecture.

## Goal

Implement a narrow quality layer that:
- improves grounding reliability
- improves source selection for answer generation
- reduces vague or weakly supported answers
- keeps the implementation additive

## In scope

1. Improve prompt assembly for `answer`, and reuse improvements where clearly appropriate for `canon`, `compare`, and `contradict`.
2. Make retrieval depth defaults mode-aware instead of relying on one overly small default.
3. Keep grounding primary: retrieved sources remain the main evidence.
4. Improve answer structure so unsupported claims are less likely.
5. Keep source references visible.
6. Update `docs/project-map.md`.
7. Update `CURRENT_STATE.md` concisely.
8. Add narrow tests.

## Suggested behavior

### Prompt quality
Prompts should:
- prefer concise grounded judgments
- explicitly admit uncertainty when support is weak
- avoid overclaiming
- avoid inventing unsupported canon or facts

### Retrieval depth by mode
Allow better defaults per mode, for example:
- `answer`
- `canon`
- `compare`
- `contradict`

The goal is not more complexity for its own sake, but better evidence selection.

### Output quality
A good result should:
- be more specific when sources support specificity
- be more cautious when support is weak
- feel less vague
- still remain short and readable

## Definition of Done

This layer is complete when:
1. Answer-facing modes produce more precise grounded output.
2. Retrieval depth defaults are better aligned to each mode.
3. Grounding remains primary.
4. Tests pass.
5. `docs/project-map.md` is updated.
6. `CURRENT_STATE.md` is updated concisely.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli answer "What does the auditor represent?"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli canon "auditor language"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli compare "auditor" "old man"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli contradict "auditor as protector" "auditor as destroyer"
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```
