# Embedding Integration + Local Index Foundation

## Goal

Create the first real semantic retrieval foundation by embedding chunk text with Cohere, writing a file-based local index, and exposing a simple search CLI.

## Definition of done

- Support `cohere` as the first real embedding provider
- Read chunks from `data/processed/chunks.jsonl`
- Write indexed chunks to `data/index/chunk_index.jsonl`
- Search the local index with cosine similarity
- Keep generation out of scope

## Files changed

- `.env.example`
- `requirements.txt`
- `docs/project-map.md`
- `src/book_research_agent/cli.py`
- `src/book_research_agent/core/chunking/__init__.py`
- `src/book_research_agent/core/chunking/serialize.py`
- `src/book_research_agent/core/chunks/models.py`
- `src/book_research_agent/core/config/settings.py`
- `src/book_research_agent/core/indexing/__init__.py`
- `src/book_research_agent/core/indexing/models.py`
- `src/book_research_agent/core/indexing/serialize.py`
- `src/book_research_agent/core/indexing/service.py`
- `src/book_research_agent/core/providers/base.py`
- `src/book_research_agent/core/providers/cohere_embeddings.py`
- `src/book_research_agent/core/providers/dummy.py`
- `src/book_research_agent/core/providers/factory.py`
- `src/book_research_agent/core/retrieval/__init__.py`
- `src/book_research_agent/core/retrieval/search.py`
- `tests/test_indexing.py`
- `tests/test_retrieval_search.py`

## What this layer does

- Uses Cohere as the first real embedding provider
- Builds a local file-based index from chunk JSONL
- Searches stored chunk embeddings with plain cosine similarity
- Keeps secrets only in `.env` or process environment variables

## Intentionally not included yet

- Generation
- Vector database
- Reranking
- Advanced retrieval policies
- Multi-provider embedding orchestration

## Next major layer

Better retrieval behavior or generation integration on top of the local semantic index.
