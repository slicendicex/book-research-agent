# Layer 09 — Contradiction / Tension Foundation

## Purpose

Add the first contradiction-aware mode on top of the current retrieval, answer, and compare foundations.

## Goal

Implement a narrow contradiction / tension mode that:
- takes two queries
- retrieves sources for both sides separately
- builds a compact contradiction-focused prompt
- returns a short judgment plus explanation
- shows source references for both sides

## In scope

1. Add a `contradict` CLI command.
2. Reuse existing retrieval, compare, and generation foundations.
3. Add a small contradiction/tension prompt assembly layer.
4. Keep the implementation additive.
5. Update `docs/project-map.md`.
6. Update `CURRENT_STATE.md` concisely.
7. Add narrow tests.

## Suggested behavior

Example:

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli contradict "auditor as protector" "auditor as destroyer"
```

A useful result should include:
- verdict: aligned / in tension / contradictory / unclear
- short explanation
- sources used for both sides

## Definition of Done

This layer is complete when:
1. A new contradiction-facing CLI mode exists.
2. It reuses the current retrieval and generation foundations.
3. It produces a short grounded contradiction/tension judgment.
4. Source references are visible.
5. Tests pass.
6. `docs/project-map.md` is updated.
7. `CURRENT_STATE.md` is updated concisely.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli contradict "auditor as protector" "auditor as destroyer"
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```
