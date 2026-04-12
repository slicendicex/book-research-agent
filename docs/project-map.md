# Project Map

## Title

book-research-agent

## Current status

Initial repository scaffold created, with local Python environment, runnable CLI scaffold, automatic local `.env` loading, AI boundary/config foundation, document ingestion, chunking, embedding/index foundation, source-facing retrieval, retrieval-grounded answer assembly, read-only corpus diagnostics, compact canon-aware answer guidance, and grounded compare mode.

## Current structure

- `data/raw/`
- `data/processed/`
- `data/index/`
- `docs/layers/`
- `docs/layers/00-ai-boundary-config.md`
- `docs/layers/01-document-ingestion.md`
- `docs/layers/02-chunking-layer.md`
- `docs/layers/03-embedding-index-foundation.md`
- `docs/layers/04-source-retrieval-mode.md`
- `docs/layers/05-generation-answer-assembly.md`
- `docs/layers/06-corpus-diagnostics.md`
- `docs/layers/07-domain-pack-canon-foundation.md`
- `docs/layers/08-compare-mode-foundation.md`
- `requirements.txt`
- `src/book_research_agent/core/`
- `src/book_research_agent/core/chunks/`
- `src/book_research_agent/core/chunking/`
- `src/book_research_agent/core/config/`
- `src/book_research_agent/core/config/env.py`
- `src/book_research_agent/core/diagnostics/`
- `src/book_research_agent/core/documents/`
- `src/book_research_agent/core/ingestion/`
- `src/book_research_agent/core/indexing/`
- `src/book_research_agent/core/generation/`
- `src/book_research_agent/core/answering/`
- `src/book_research_agent/core/answering/compare.py`
- `src/book_research_agent/core/providers/`
- `src/book_research_agent/core/retrieval/`
- `src/book_research_agent/core/retrieval/source.py`
- `src/book_research_agent/domain/`
- `src/book_research_agent/domain/canon.py`
- `src/book_research_agent/corpus/`
- `src/book_research_agent/config.py`
- `src/book_research_agent/cli.py`
- `tests/`

## What exists now

- Base repository metadata and setup files
- Initial scaffold directories
- Empty package markers for scaffold layers
- Local `.venv/` Python environment
- Minimal runnable CLI scaffold and basic path configuration
- Runtime settings loaded from environment variables
- CLI startup automatically loads project-root `.env` without overriding shell variables
- Reusable provider interfaces with dummy implementations and a local factory
- `doctor` CLI command for safe configuration inspection
- Document models for normalized local source files
- Ingestion pipeline for `.txt` and `.md` files from `data/raw/`
- JSONL export to `data/processed/documents.jsonl`
- Character-based chunking from `documents.jsonl` to `chunks.jsonl`
- Chunk metadata that preserves document traceability
- Minimal ingestion tests
- Minimal chunking tests
- Cohere as the first real embedding provider
- Local file-based chunk index in `data/index/chunk_index.jsonl`
- Plain cosine-similarity semantic search over indexed chunks
- Source-facing retrieval formatting with readable excerpts
- Light same-document neighbor suppression for source-mode output
- Dedicated `source` CLI command for source-first retrieval display
- Cohere as the first real generation provider
- Retrieval-grounded answer assembly with visible source references
- Dedicated `answer` CLI command for short grounded answers
- Read-only corpus diagnostics commands: `stats`, `inspect-doc`, `inspect-chunk`, `inspect-index`
- Compact domain pack for canon-aware answer wording without overriding retrieved sources
- Dedicated `compare` CLI command for short grounded comparisons with visible sources for both sides

## What is still missing

- Additional provider choices beyond the current Cohere-first path
- Deeper domain-specific reasoning beyond the compact prompt lens

## Next logical layer

Broader reasoning and provider expansion built on top of the canon-aware answer, compare, and diagnostics foundation.
