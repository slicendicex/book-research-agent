# Chunking Layer

## Goal

Create a minimal reusable chunking pipeline that reads normalized documents from JSONL, splits them into retrieval-ready character chunks, and writes chunks to JSONL.

## Definition of done

- Read `data/processed/documents.jsonl`
- Produce character-based chunks with configurable size and overlap
- Preserve chunk-to-document traceability
- Write `data/processed/chunks.jsonl`
- Expose the pipeline through `book-research-agent chunk`

## Files changed

- `docs/project-map.md`
- `src/book_research_agent/cli.py`
- `src/book_research_agent/core/documents/models.py`
- `src/book_research_agent/core/ingestion/serialize.py`
- `src/book_research_agent/core/chunks/__init__.py`
- `src/book_research_agent/core/chunks/models.py`
- `src/book_research_agent/core/chunking/__init__.py`
- `src/book_research_agent/core/chunking/service.py`
- `src/book_research_agent/core/chunking/serialize.py`
- `tests/test_chunking.py`

## What this layer does

- Loads normalized documents from processed JSONL
- Splits text by character count
- Preserves source title, source relative path, and character offsets
- Writes chunk rows to JSONL

## Intentionally not included yet

- Semantic chunking
- Embeddings
- Vector index
- Retrieval
- Generation

## Next major layer

Embedding and index integration on top of `chunks.jsonl`.
