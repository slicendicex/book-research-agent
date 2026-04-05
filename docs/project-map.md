# Project Map

## Title

book-research-agent

## Current status

Initial repository scaffold created, with local Python environment, runnable CLI scaffold, AI boundary/config foundation, document ingestion, and a first reusable chunking layer in place.

## Current structure

- `data/raw/`
- `data/processed/`
- `data/index/`
- `docs/layers/`
- `docs/layers/00-ai-boundary-config.md`
- `docs/layers/01-document-ingestion.md`
- `docs/layers/02-chunking-layer.md`
- `requirements.txt`
- `src/book_research_agent/core/`
- `src/book_research_agent/core/chunks/`
- `src/book_research_agent/core/chunking/`
- `src/book_research_agent/core/config/`
- `src/book_research_agent/core/documents/`
- `src/book_research_agent/core/ingestion/`
- `src/book_research_agent/core/providers/`
- `src/book_research_agent/domain/`
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
- Reusable provider interfaces with dummy implementations and a local factory
- `doctor` CLI command for safe configuration inspection
- Document models for normalized local source files
- Ingestion pipeline for `.txt` and `.md` files from `data/raw/`
- JSONL export to `data/processed/documents.jsonl`
- Character-based chunking from `documents.jsonl` to `chunks.jsonl`
- Chunk metadata that preserves document traceability
- Minimal ingestion tests
- Minimal chunking tests

## What is still missing

- Core implementation
- Domain-specific logic
- Embedding and index integration
- Real provider SDK integrations

## Next logical layer

Embedding and index integration built on top of chunks.
