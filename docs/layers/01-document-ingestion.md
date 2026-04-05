# Document Ingestion Layer

## Goal

Create a minimal reusable ingestion pipeline that reads local text files, converts them into internal `Document` objects, and writes them to JSONL.

## Definition of done

- Recursively scan `data/raw/`
- Support only `.txt` and `.md`
- Normalize text lightly
- Extract a minimal title
- Write documents to `data/processed/documents.jsonl`
- Expose the pipeline through `book-research-agent ingest`

## Files changed

- `docs/project-map.md`
- `src/book_research_agent/cli.py`
- `src/book_research_agent/core/documents/__init__.py`
- `src/book_research_agent/core/documents/models.py`
- `src/book_research_agent/core/ingestion/__init__.py`
- `src/book_research_agent/core/ingestion/normalize.py`
- `src/book_research_agent/core/ingestion/loaders.py`
- `src/book_research_agent/core/ingestion/service.py`
- `src/book_research_agent/core/ingestion/serialize.py`
- `tests/test_document_ingestion.py`

## Supported now

- Local `.txt` files
- Local `.md` files
- UTF-8 and UTF-8-SIG text loading
- JSONL export of normalized documents

## Intentionally not included yet

- PDF or DOCX support
- OCR
- Chunking
- Embeddings
- Vector index
- Retrieval
- Any domain-specific book logic

## Next layer

Chunking built on top of `documents.jsonl`.
