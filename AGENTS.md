# AGENTS.md — book-research-agent

## Purpose

This repository starts with a book-research use case, but it must be built as a reusable research-agent scaffold first.

Do not tightly fuse the architecture to one specific book from day one.

## Build order

Always build in this order:

1. Reusable scaffold
2. Domain-specific layer
3. Real corpus data

Do not merge these concerns into one step.

## v0.1 boundary

For the first version, keep the project:

- Python
- local `venv`
- one provider at a time
- local files as the main corpus
- retrieval-first
- CLI-first

Do not introduce unless explicitly requested:

- LangGraph
- multi-agent orchestration
- OCR
- Telegram bot
- web UI
- browser app
- background jobs
- heavy framework abstractions
- premature cloud infrastructure

## Architecture rule

Keep three layers conceptually separate:

- `core/` — reusable engine logic
- `domain/` — replaceable project/domain logic
- `corpus/` — concrete loaded materials

Main rule:
- Core should be reusable
- Domain should be replaceable
- Corpus should be attachable separately

## Layer rule

Work strictly one layer at a time.

For each layer:

1. Define the goal
2. Define a short definition of done
3. List the files that should change
4. Implement only that layer
5. Run a minimal verification
6. Explain what changed
7. Update `docs/project-map.md`

Do not silently expand scope.

## Change discipline

Prefer the smallest coherent change.

Do:
- keep code simple
- keep names explicit
- keep files focused
- preserve readability
- isolate responsibilities

Do not:
- rewrite unrelated files
- add abstractions for hypothetical future needs
- add dependencies without a clear reason
- mix scaffold design and real corpus ingestion in one step

## Verification and docs

After each completed layer:

- run the smallest relevant check
- note limitations honestly
- do a brief self-review for overengineering or scope drift
- update `docs/project-map.md`

If architecture-specific guidance grows, keep this file short and move details into project docs.