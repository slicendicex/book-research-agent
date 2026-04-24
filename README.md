# book-research-agent

CLI-first local RAG pipeline for working with a private text corpus.

The project is built as a layered, retrieval-first system. It ingests local text
files, normalizes them into internal documents, splits them into chunks, builds a
local embedding index, and supports grounded query modes over the corpus.

## Current Capabilities

- local corpus ingestion from `data/raw`
- normalized document pipeline
- paragraph-aware chunking
- local embedding index
- semantic search
- source-oriented retrieval view
- grounded answer mode
- compare / contradict / canon modes
- corpus diagnostics and reporting
- eval runs with retrieval snapshots and JSON export

Retrieved sources remain the primary truth source. Domain guidance and generation
sit on top of retrieval, not instead of it.

## Pipeline

```text
data/raw
-> ingest
-> documents
-> chunk
-> chunks
-> index
-> search / source / answer / compare / contradict / canon / eval
```

## Project Structure

```text
data/
  raw/
  processed/
  index/
  eval/

docs/
  layers/
  project-map.md

src/
  book_research_agent/

tests/
```

## Example CLI Commands

```bash
doctor
ingest
chunk
index
search "auditor"
source "auditor"
answer "What does the auditor represent?"
compare "auditor" "old man"
contradict "auditor as protector" "auditor as destroyer"
canon "auditor language"
corpus-report
eval
eval --json-out data/eval/runs/baseline.json
```

## How It Works

1. Local `.txt` and `.md` files are read from `data/raw`.
2. They are normalized into internal document records.
3. Documents are split into retrieval-ready chunks.
4. Chunks are embedded into a local file-based index.
5. Query modes retrieve relevant chunks and use them as grounded context.

## Current Boundaries

- no OCR or PDF ingestion
- no web UI or Telegram interface
- no vector database
- no multi-agent orchestration
- no benchmark-grade answer scoring yet

## Local-Only Data

These should remain local and not be committed:

- `.env`
- `data/raw/*`
- `data/processed/*`
- `data/index/*`
- local eval run outputs

## More Context

- `docs/project-map.md`
- `docs/layers/`
- `CURRENT_STATE.md`
- `docs/architecture-decisions.md`