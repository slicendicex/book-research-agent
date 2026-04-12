# Layer 11 — Canon Mode Foundation

## Purpose

Add the first canon mode on top of the current retrieval, answer, compare, and contradiction foundations.

## Goal

Implement a narrow canon mode that:
- takes one query
- retrieves relevant sources
- builds a compact canon-focused prompt
- returns a short canon-oriented judgment
- shows source references

## In scope

1. Add a `canon` CLI command.
2. Reuse existing retrieval and generation foundations.
3. Add a small canon-focused prompt assembly layer.
4. Keep the implementation additive.
5. Update `docs/project-map.md`.
6. Update `CURRENT_STATE.md` concisely.
7. Add narrow tests.

## Suggested behavior

Example:

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli canon "auditor language"
```

A useful result should include:
- current canonical reading
- competing variants if present
- confidence / uncertainty if relevant
- sources used

The mode should be cautious:
- prefer "unclear" over overclaiming canon
- do not invent unsupported canon
- treat retrieved sources as primary evidence

## Definition of Done

This layer is complete when:
1. A new canon-facing CLI mode exists.
2. It reuses the current retrieval and generation foundations.
3. It produces a short grounded canon-oriented judgment.
4. Source references are visible.
5. Tests pass.
6. `docs/project-map.md` is updated.
7. `CURRENT_STATE.md` is updated concisely.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli canon "auditor language"
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```
