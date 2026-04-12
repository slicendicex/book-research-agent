# Layer 10 — Corpus Hygiene / Duplicate Detection

## Purpose

Add the first corpus hygiene layer for finding duplicate or near-duplicate material in the corpus.

## Goal

Implement a narrow duplicate-detection mode that:
- inspects processed documents and chunks
- identifies likely duplicate or near-duplicate material
- reports duplicate groups clearly
- keeps the implementation read-only

## In scope

1. Add a `dedup-stats` CLI command.
2. Add a `find-duplicates` CLI command for documents.
3. Add a `find-duplicate-chunks` CLI command.
4. Reuse existing processed artifacts instead of raw-file scanning logic.
5. Keep the implementation additive and read-only.
6. Update `docs/project-map.md`.
7. Update `CURRENT_STATE.md` concisely.
8. Add narrow tests.

## Suggested behavior

### `dedup-stats`
Show at least:
- processed document count
- processed chunk count
- likely duplicate document groups
- likely duplicate chunk groups

### `find-duplicates`
Show groups of duplicate or near-duplicate documents with:
- document id
- title
- relative path
- similarity indicator if available

### `find-duplicate-chunks`
Show groups of duplicate or near-duplicate chunks with:
- chunk id
- document id
- relative path
- chunk index
- similarity indicator if available

## Definition of Done

This layer is complete when:
1. Duplicate-detection commands exist.
2. They are read-only.
3. They help identify duplicate or near-duplicate material clearly.
4. Tests pass.
5. `docs/project-map.md` is updated.
6. `CURRENT_STATE.md` is updated concisely.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli dedup-stats
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli find-duplicates
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli find-duplicate-chunks
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```
