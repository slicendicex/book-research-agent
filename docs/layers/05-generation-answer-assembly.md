# Layer 05 — Generation / Answer Assembly Foundation

## Purpose

Add the first source-grounded answer mode on top of the existing retrieval foundation.

The project already supports:
- ingestion
- chunking
- semantic indexing
- raw search
- source-facing retrieval output

This layer should add a minimal answer mode that uses retrieved sources to generate a short grounded response.

---

## Why this layer exists

The current system can already find and display relevant source fragments.

What is still missing:
- a direct answer mode
- retrieval-to-prompt assembly
- minimal grounded synthesis

This layer should create the first answer path without turning the project into a complex agent system.

---

## Goal

Implement a minimal answer mode that:

- takes a user question
- runs retrieval
- assembles a compact source-grounded context
- calls a generation provider
- returns a short answer
- shows which sources were used

---

## In scope

### 1. Real generation provider
Implement exactly one real generation provider.

Recommended provider for this layer:
- `openai`

The provider should:
- stay behind the existing `GenerationProvider` boundary
- read its API key from environment
- raise a clear error if the key is missing

### 2. Prompt assembly
Add a small answer-assembly layer that:
- takes the query
- takes the top retrieval hits
- builds a compact grounded prompt
- asks for a concise answer based only on the provided sources

Keep prompt assembly small and explicit.

### 3. Answer result model
Add a small result model for answer mode.

Suggested fields:
- query
- answer
- sources_used

Each source reference should include at least:
- title
- relative path
- chunk index

### 4. Answer CLI command
Add a dedicated CLI command, for example:
- `answer`

Suggested usage:
```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli answer "What does the auditor represent?"
```

Optional flags are acceptable:
- `--top-k`
- `--index-file`

### 5. Documentation updates
Update:
- `docs/project-map.md`
- `CURRENT_STATE.md`

Important:
when updating `CURRENT_STATE.md`, keep it concise and structured.
Do not turn it into a diary or verbose changelog.

### 6. Tests
Add narrow tests for:
- prompt assembly
- answer result shaping
- generation provider missing-key behavior
- answer mode orchestration with mocked generation provider


---

## Design constraints

1. Reuse the current retrieval and source layers.
2. Keep retrieval separate from generation.
3. Keep answer assembly small and explicit.
4. Do not hide sources.
5. Do not let generation bypass retrieval.
6. Avoid new complexity unless clearly necessary.

---

## Suggested architecture

Existing layers to reuse:
- `core/retrieval/search.py`
- `core/retrieval/source.py`

New generation-facing layer:
- `core/generation/openai_generation.py`
- `core/answering/models.py`
- `core/answering/prompting.py`
- `core/answering/service.py`

CLI:
- update `cli.py`
- keep CLI thin

---

## Definition of Done

This layer is complete when:

1. A new answer-facing CLI mode exists.
2. Answer mode reuses retrieval instead of bypassing it.
3. A real generation provider is integrated behind the provider boundary.
4. The system returns a short grounded answer.
5. The answer output includes source references.
6. Tests pass.
7. `docs/project-map.md` is updated.
8. `CURRENT_STATE.md` is updated concisely and without diary-like sprawl.

---

## Verification commands

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli answer "What does the auditor represent?"
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

Verification intent:
- confirm answer mode runs end-to-end
- confirm the answer is grounded in retrieved sources
- confirm tests pass
