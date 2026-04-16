## Purpose

Provide a first visibility layer over the corpus that helps understand its structure as a system of themes, motifs, and connections rather than a collection of files.

## Goal

Implement a narrow corpus intelligence layer that:
- surfaces recurring themes, entities, or motifs
- highlights weakly represented or underdeveloped lines
- detects potentially isolated (orphan) notes
- avoids low-signal technical metrics (like chunk counts)
- keeps everything read-only, simple, and CLI-first

## In scope

1. Add a new CLI command `corpus-report`.
2. Analyze existing processed data (documents + chunks).
3. Extract simple recurring tokens / phrases as motif candidates.
4. Identify:
   - most frequent motifs/entities
   - low-frequency but repeated motifs (emerging lines)
5. Detect potential orphan notes:
   - documents with very low overlap with others
6. Print a compact human-readable report.
7. Keep logic deterministic and simple (no LLM required).
8. Update `docs/project-map.md`.
9. Update `CURRENT_STATE.md` concisely.
10. Add narrow tests if needed.

## Suggested behavior

### Motif surfacing

System should:
- scan chunks/documents
- extract candidate tokens (simple heuristics: words, n-grams)
- count frequency across corpus

Output:
- Top recurring motifs (high frequency)
- Emerging motifs (low frequency but >1 occurrence)

### Orphan detection

System should:
- compare documents via token overlap or simple similarity
- flag documents with very low overlap with others

Output:
- list of potential orphan notes

### Report structure

Example:

Corpus Report

Top motifs:
- auditor
- memory
- control

Emerging motifs:
- forest
- ritual

Potential orphan notes:
- note_x.md
- note_y.md

## Definition of Done

This layer is complete when:
1. CLI command `corpus-report` exists.
2. System analyzes corpus without using LLM.
3. Recurring motifs are surfaced.
4. Emerging motifs are surfaced.
5. Orphan notes are detected.
6. Output is readable and useful.
7. No chunk-count-based metrics are included.
8. Tests (if added) pass.
9. `docs/project-map.md` is updated.
10. `CURRENT_STATE.md` is updated concisely.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli corpus-report
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git diff --check
```
