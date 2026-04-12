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
-> search / source / answer / compare / contradict

Current retrieval stack is functional:
- local private corpus
- normalized documents
- character-based chunks
- Cohere embeddings
- file-based local semantic index
- top-k semantic search
- source-facing retrieval display mode
- canon-aware answer prompt lens
- grounded compare mode
- grounded contradiction/tension mode
- CLI autoloads project-root `.env`
- read-only corpus diagnostics commands

---

## Completed layers

- Layer 00 — AI Boundary & Runtime Config Foundation
- Layer 01 — Document Ingestion Layer
- Layer 02 — Chunking Layer
- Layer 03 — Embedding Integration + Local Index Foundation
- Layer 04 — Source Retrieval Mode
- Layer 05 — Generation / Answer Assembly Foundation
- Layer 06 — Corpus Diagnostics
- Layer 07 — Domain Pack / Canon Foundation
- Layer 08 — Compare Mode Foundation
- Layer 09 — Contradiction / Tension Foundation

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
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli compare "auditor" "old man"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli contradict "auditor as protector" "auditor as destroyer"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli stats
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli inspect-doc --path "notes/example.md"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli inspect-chunk --chunk-id "doc-1:0"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli inspect-index --chunk-id "doc-1:0"
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

CLI commands load project-root `.env` automatically; manual `source .env` is not required for normal use.

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
- domain awareness is currently a compact prompt lens, not a reasoning layer
- no MCP / function-calling layer yet

---

## Next target layer

Layer 10 — Later expansion

Goal:
keep later work beyond canon-aware retrieval-grounded answering, compare/contradiction modes, and diagnostics narrow and traceable.

Focus:
- future provider expansion
- deeper reasoning layers
- no broad domain-specific reasoning engine yet

---

## Update rule

When updating this file:
- keep the section structure stable
- update only the relevant sections
- keep wording concise
- do not turn this file into a diary or verbose changelog
