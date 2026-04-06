# CURRENT_STATE.md

## Project identity

Project: `book-research-agent`  
Version line: `v0.1 foundation`  
Direction: CLI-first external brain for a private book corpus

The project is being built as a layered semantic retrieval system before generation is added.

---

## Current pipeline

raw files
-> ingest
-> documents.jsonl
-> chunk
-> chunks.jsonl
-> embed
-> chunk_index.jsonl
-> search

Current retrieval stack is functional:
- local private corpus
- normalized documents
- character-based chunks
- Cohere embeddings
- file-based local semantic index
- top-k semantic search
- source-facing retrieval display mode

---

## Completed layers

- Layer 00 — AI Boundary & Runtime Config Foundation
- Layer 01 — Document Ingestion Layer
- Layer 02 — Chunking Layer
- Layer 03 — Embedding Integration + Local Index Foundation
- Layer 04 — Source Retrieval Mode

---

## Working commands

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli doctor
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli ingest
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli chunk
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli index
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli search "auditor"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli source "auditor"
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

---

## Data layout

Private local input:
- `data/raw/`

Processed local artifacts:
- `data/processed/documents.jsonl`
- `data/processed/chunks.jsonl`

Local index artifacts:
- `data/index/chunk_index.jsonl`

Important:
raw corpus, processed artifacts, and index artifacts must remain outside git except for `.gitkeep` placeholders.

---

## Providers

Embeddings:
- provider: `cohere`
- model: `embed-v4.0`

Generation:
- not implemented yet

---

## Known limitations

- chunking is character-based
- no generation / synthesis layer yet
- no domain-specific reasoning layer yet
- no MCP / function-calling layer yet

---

## Next target layer

Layer 05 — Generation Layer

Goal:
add a minimal source-grounded generation layer on top of retrieval without weakening traceability.

Focus:
- source-grounded answer scaffold
- retrieval-to-generation handoff
- explicit citation-first output shape
- no domain-specific reasoning yet

---

## Update rule

When updating this file:
- keep the section structure stable
- update only the relevant sections
- keep wording concise
- do not turn this file into a diary or verbose changelog
