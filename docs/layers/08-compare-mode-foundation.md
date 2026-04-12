# Layer 08 — Compare Mode Foundation

## Purpose

Add the first compare mode on top of the current retrieval-first system.

## Goal

Implement a narrow compare mode that:
- takes two queries
- retrieves sources for both sides separately
- builds a compact compare prompt
- returns a short grounded comparison
- shows source references for both sides

## In scope

1. Add a `compare` CLI command.
2. Reuse existing retrieval and generation foundations.
3. Add a small compare prompt assembly layer.
4. Keep the implementation additive.
5. Update `docs/project-map.md`.
6. Update `CURRENT_STATE.md` concisely.
7. Add narrow tests.

## Suggested behavior

Example:

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli compare "auditor" "old man"
```

A useful result should include:
- shared themes
- key differences
- main tension
- uncertainties if relevant
- sources used for both sides

## Definition of Done

This layer is complete when:
1. A new compare CLI mode exists.
2. It reuses the current retrieval and generation foundations.
3. It produces a short grounded comparison.
4. Source references are visible.
5. Tests pass.
6. `docs/project-map.md` is updated.
7. `CURRENT_STATE.md` is updated concisely.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli compare "auditor" "old man"
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```
