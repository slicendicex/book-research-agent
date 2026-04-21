# Layer 18 — Chunking / Retrieval Upgrade Foundation

## Goal

Improve retrieval quality by making chunking more semantic and retrieval output less redundant.

---

## Non-Goals

- no change to embeddings
- no change to index format
- no new providers
- no reranking models
- no hybrid retrieval

---

## Changes

### Chunking

- switch from pure character-based splitting to paragraph-aware splitting
- use "\n\n" as primary boundary
- accumulate paragraphs into chunks within chunk_size
- fallback to character split for oversized paragraphs

### Overlap

- apply overlap at paragraph level
- include last paragraph from previous chunk when needed
- avoid excessive duplication

### Retrieval

- add diversity filtering on top_k results
- skip chunks that are too similar to already selected ones

### Duplicate suppression

- remove near-identical chunks from final retrieval output

---

## Files

- core/chunking/*
- core/retrieval/search.py
- tests/test_chunking.py
- tests/test_retrieval.py

---

## Acceptance Criteria

- chunks align with paragraph boundaries in most cases
- fallback works for long paragraphs
- retrieval output contains fewer near-duplicate chunks
- top_k results are more diverse
- no regression in existing commands

---

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli chunk
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli index
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli search "test query"
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

---

## Notes

- keep implementation deterministic
- avoid adding external dependencies
- keep changes minimal and localized

