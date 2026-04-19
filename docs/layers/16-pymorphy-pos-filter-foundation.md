## Purpose

Improve concept-level corpus observability by replacing heuristic Russian normalization with morphology-aware normalization and part-of-speech filtering.

## Goal

Implement a narrow refinement layer that:
- uses `pymorphy` for Russian lemmatization
- uses POS information to suppress noisy non-concept tokens
- improves concept bucket quality in `corpus-report`
- keeps the report deterministic, read-only, and CLI-first

## In scope

1. Add `pymorphy` as a project dependency for corpus-report analysis.
2. Replace heuristic Russian form grouping with morphology-aware lemmatization where appropriate.
3. Add POS-based filtering for concept candidates.
4. Prefer concept candidates that are nouns; allow limited adjective support only if clearly justified.
5. Reduce noisy verb/adverb/pronoun-like concept outputs such as `ВИДИТ`, `ПРАВ`, `ПЕРВ`.
6. Keep existing low-signal stoplist filtering.
7. Keep existing concept bucket and co-occurrence reporting structure.
8. Keep the system deterministic and LLM-free.
9. Keep everything read-only.
10. Update `docs/project-map.md`.
11. Update `CURRENT_STATE.md` concisely.
12. Add narrow tests for lemmatization and POS filtering.

## Suggested behavior

### Morphology-aware normalization

System should:
- parse Russian tokens through `pymorphy`
- convert token forms to a normalized lemma
- use the normalized lemma as the base for concept grouping

Examples:
- `аудитор`, `аудитора`, `аудитором` -> `АУДИТОР`
- `земли`, `земле`, `землёй` -> `ЗЕМЛЯ`

### POS filtering

System should:
- keep noun-like candidates as primary concept units
- drop obvious verb/adverb/pronoun/function-word candidates
- optionally allow adjective concepts only if they behave like stable domain concepts

Examples of noise to suppress:
- `ВИДИТ`
- `ПРАВ`
- `ПЕРВ`

### Output quality

`corpus-report` should:
- preserve core concepts
- produce cleaner secondary concept lines
- reduce abstract or malformed noise
- keep strong co-occurrences readable

## Definition of Done

This layer is complete when:
1. `pymorphy` is integrated into corpus-report concept normalization.
2. Russian forms are normalized through morphology instead of only heuristics.
3. POS filtering removes obvious non-concept outputs.
4. Secondary concept lines are visibly cleaner than in Layer 15.
5. Existing concept-level report sections still work.
6. No LLM usage is introduced.
7. No retrieval, indexing, generation, or provider behavior is changed.
8. Tests pass.
9. `docs/project-map.md` is updated.
10. `CURRENT_STATE.md` is updated concisely.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli corpus-report
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git diff --check
```
