# Layer 07 — Domain Pack / Canon Foundation

## Purpose

Add the first domain-aware layer on top of the working retrieval-first core.

## Why this layer exists

The project now has a working generic pipeline:
- ingest
- chunk
- index
- search
- source
- answer
- diagnostics

What is still missing is domain awareness.
The system can answer from the corpus, but it does not yet reason with a book-specific lens.

## Goal

Add a narrow domain pack foundation that helps the agent answer in a more canon-aware and project-aware way.

## In scope

1. Add a small domain instruction layer for answer mode.
2. Add a project-specific terminology / concept pack.
3. Add a minimal canon-aware prompt contribution.
4. Keep the retrieval/indexing pipeline unchanged.
5. Keep the implementation additive.
6. Update `docs/project-map.md`.
7. Update `CURRENT_STATE.md` concisely.
8. Add narrow tests.

## Suggested behavior

### Domain instruction
Add a compact project-specific instruction that tells the answer mode to:
- stay grounded in sources
- reason within the book project context
- prefer canon-aware wording
- avoid inventing unsupported canon

### Terminology pack
Add a small domain file or structure for core project concepts, for example:
- Auditor
- Old Man
- Museum
- Forest
- preservation
- life
- order
- chaos
- canon

This is not a full ontology.
Keep it small and explicit.

### Prompt integration
Use the domain pack only as a thin augmentation to the existing answer prompt.
Do not replace retrieval-grounded prompting.

## Definition of Done

This layer is complete when:
1. Answer mode has a narrow domain-aware augmentation.
2. Retrieval grounding remains primary.
3. The system becomes more canon-aware without hallucinating unsupported canon.
4. Tests pass.
5. `docs/project-map.md` is updated.
6. `CURRENT_STATE.md` is updated concisely.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli answer "What does the auditor represent?"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli answer "What is the conflict between the old man and the auditor?"
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```
