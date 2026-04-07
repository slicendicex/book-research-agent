# CURRENT_STATE.md

## Project identity

Project: `book-research-agent`  
Version line: `v0.1 foundation`  
Direction: CLI-first external brain for a private book corpus

The project is being built as a layered retrieval-first system with minimal grounded generation now in place.

---

## Current pipeline

raw files
-> ingest
-> documents.jsonl
-> chunk
-> chunks.jsonl
-> embed
-> chunk_index.jsonl
-> search / source / answer

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
- Layer 05 — Generation / Answer Assembly Foundation

---

## Working commands

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli doctor
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli ingest
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli chunk
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli index
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli search "auditor"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli source "auditor"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli answer "What does the auditor represent?"
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
- provider: `cohere`
- answer mode: retrieval-grounded single-shot generation

---

## Known limitations

- chunking is character-based
- no domain-specific reasoning layer yet
- no MCP / function-calling layer yet

---

## Next target layer

Layer 06 — Later expansion

Goal:
keep later work beyond the new minimal answer layer narrow and traceable.

Focus:
- future provider expansion
- deeper reasoning layers
- still no domain-specific reasoning yet

---

## Update rule

When updating this file:
- keep the section structure stable
- update only the relevant sections
- keep wording concise
- do not turn this file into a diary or verbose changelog
