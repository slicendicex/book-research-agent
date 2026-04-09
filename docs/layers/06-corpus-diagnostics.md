# Layer 06 — Corpus Diagnostics

## Purpose

Add a small diagnostics layer for inspecting the corpus pipeline state.

## Why this layer exists

The project now has a working pipeline:
- ingest
- chunk
- index
- search
- source
- answer

What is still weak is observability.
Before scaling the corpus, the system needs simple inspection tools.

## Goal

Add a narrow diagnostics mode that helps inspect:
- corpus size
- processed artifacts
- individual documents
- individual chunks
- indexed chunk metadata

## In scope

1. Add a `stats` command for basic corpus counts.
2. Add an `inspect-doc` command.
3. Add an `inspect-chunk` command.
4. Add an `inspect-index` command.
5. Keep all diagnostics read-only.
6. Update `docs/project-map.md`.
7. Update `CURRENT_STATE.md` concisely.
8. Add narrow tests.

## Suggested behavior

### `stats`
Show at least:
- document count
- chunk count
- indexed chunk count

### `inspect-doc`
Show a single processed document with basic metadata.

### `inspect-chunk`
Show a single chunk with:
- chunk id
- document id
- title
- path
- chunk index
- char offsets
- text

### `inspect-index`
Show a single indexed chunk with:
- chunk id
- embedding model
- embedding dimension
- metadata

Do not print the full embedding vector unless explicitly requested.


## Definition of Done

This layer is complete when:
1. Diagnostics commands exist.
2. They are read-only.
3. They help inspect pipeline state clearly.
4. Tests pass.
5. `docs/project-map.md` is updated.
6. `CURRENT_STATE.md` is updated concisely.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli stats
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli inspect-doc --path "oldman vs auditor.txt"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli inspect-chunk --chunk-id "SAMPLE:0"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli inspect-index --chunk-id "SAMPLE:0"
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```
