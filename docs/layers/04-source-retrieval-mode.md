# Layer 04 — Source Retrieval Mode

## Goal

Turn the current low-level semantic search output into a more readable, source-first retrieval interface.

## Why now

Current search already works, but the output is still too raw:
- excerpts may start or end mid-word
- neighboring chunks from the same document may repeat noisily
- the result feels like debug output, not a source-facing mode

This layer should improve retrieval presentation without changing chunk storage or adding generation.

## In scope

Implement a source-facing layer on top of the existing search foundation:

1. Add a small source-facing result model.
2. Add excerpt formatting for display.
3. Add very light anti-noise logic.
4. Add a dedicated `source` CLI command.
5. Update `docs/project-map.md`.
6. Update `CURRENT_STATE.md` concisely.
7. Add narrow tests for this layer.

## Required behavior

### Source-facing result
Each result should include at least:
- score
- title
- relative path
- chunk index
- readable excerpt

### Excerpt formatting
The display excerpt should:
- normalize whitespace
- support a configurable display length
- avoid mid-word starts or ends when practical
- add `...` when truncated

Important:
this is a display layer only.
Do not mutate stored chunks.

### Light anti-noise logic
Use a simple deterministic rule, for example:
- per-document result limit
- and/or suppression of very close neighboring chunks from the same document

Keep this small and explicit.
Do not introduce reranking.

### CLI
Add a new command, for example:

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli source "auditor"