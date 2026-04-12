# AGENTS.md

## Project mission

`book-research-agent` is a CLI-first external brain for a private book corpus.

The project is not a generic chatbot and not a UI app.
Its purpose is to ingest a private corpus, transform it into retrieval-ready layers, and later support source-grounded answering.

Core direction:
- source-first
- corpus-grounded
- layer-by-layer
- reusable scaffold first
- domain logic later
- private corpus stays outside git

---

## Architecture principles

1. Build layer by layer.
2. Keep scope narrow for each task.
3. Prefer working minimal slices over broad speculative design.
4. Keep `core`, `domain`, and `corpus` separated.
5. Retrieval quality comes before generation polish.
6. Keep the app CLI-first until a later phase.
7. Use file-based intermediate artifacts unless a stronger storage layer is clearly justified.
8. Do not put secrets in source code or git-tracked files.
9. Do not commit private raw, processed, or index artifacts.

---

## Current product shape

Current pipeline:

raw files
-> ingest
-> documents.jsonl
-> chunk
-> chunks.jsonl
-> embed
-> chunk_index.jsonl
-> search

Generation is not implemented yet.
Source retrieval quality and traceability come first.

---

## Scope constraints

Unless the active layer document explicitly requires it, do NOT add:

- LangGraph
- UI / web app
- Telegram integration
- OCR
- PDF parsing
- DOCX parsing
- vector database
- reranking model
- multi-agent orchestration
- MCP
- function calling
- generation / synthesis
- domain-specific reasoning
- broad speculative frameworks

Also avoid:
- unrelated refactors
- rewriting stable working layers without strong reason
- changing file layout more than necessary
- adding dependencies unless clearly justified

---

## Coding style

1. Keep code small and explicit.
2. Prefer stdlib unless an external dependency is clearly necessary.
3. Prefer dataclasses, plain functions, and readable control flow.
4. Avoid premature abstraction.
5. Keep models narrow and purpose-specific.
6. Keep serialization explicit.
7. Keep CLI thin; business logic should live in core modules.
8. Keep tests narrow and deterministic.
9. Never print or persist secrets.
10. Preserve traceability from retrieval outputs back to source documents.

---

## Data and security rules

Never commit:
- `data/raw/*`
- `data/processed/*`
- `data/index/*`
- `.env`
- API keys
- private corpus text outside safe test fixtures

Allowed tracked placeholders:
- `data/raw/.gitkeep`
- `data/processed/.gitkeep`
- `data/index/.gitkeep`

Secrets policy:
- Secrets live only in `.env` or environment variables.
- Secrets must never be hardcoded.
- Secrets must never be written to logs or tracked files.
- Secret presence may be reported as yes/no, but values must not be shown.

---

## Workflow rules

For every new layer:

1. Read `AGENTS.md`.
2. Read `CURRENT_STATE.md`.
3. Read the active layer document in `docs/layers/`.
4. Implement only the current layer.
5. Keep changes narrow and directly relevant.
6. Run the verification commands from the active layer document.
7. Update:
   - `docs/project-map.md`
   - `CURRENT_STATE.md`
8. Keep `CURRENT_STATE.md` concise and structured.
   Do not turn it into a running diary or verbose changelog.
   Update only the relevant fixed sections.
9. Return:
   - changed files
   - short architecture summary
   - verification commands
   - verification results
   - remaining notes or risks
   - suggested commit message

Do not claim a layer is complete unless its Definition of Done is satisfied.

---

## Testing rules

- Add or update tests only for the current layer.
- Prefer simple deterministic tests.
- Avoid real network calls in unit tests.
- Mock or stub external providers where needed.
- Manual smoke tests are acceptable for live provider integration, but must be clearly labeled.

---

## Git discipline

- Work in small accepted layers.
- Commit only after a layer passes review.
- Keep commit messages narrow and meaningful.
- Do not commit noisy temporary files.
- Do not commit private corpus artifacts.

---

## Good layer outcome

A good layer:
- is narrow
- is understandable
- preserves architecture clarity
- preserves traceability
- avoids smuggling in future complexity
- moves the project one real step forward