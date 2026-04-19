## Purpose

Refine corpus concept quality by introducing domain-aware concept curation using a project-specific stoplist and optional allowlist.

## Goal

Implement a narrow refinement layer that:
- removes overly abstract or low-signal concepts (e.g., "человек", "идея", "уровень")
- allows manual control over which concepts are considered meaningful
- improves the usefulness of `corpus-report` as a semantic map of the corpus
- keeps the system deterministic, simple, and read-only

## In scope

1. Introduce a project-level concept stoplist file:
   - `data/config/concept_stoplist.txt`
2. (Optional) Introduce concept allowlist:
   - `data/config/concept_allowlist.txt`
3. Load stoplist at runtime in corpus-report service.
4. Filter out concepts present in stoplist after normalization.
5. Ensure filtering applies to:
   - core concepts
   - secondary concept lines
   - co-occurrence computation (optional but recommended)
6. Keep pymorphy-based normalization and POS filtering.
7. Keep alias system intact.
8. Do not introduce LLM usage.
9. Do not modify retrieval, indexing, or generation.
10. Keep everything read-only.
11. Update `docs/project-map.md`.
12. Update `CURRENT_STATE.md`.
13. Add minimal tests for stoplist filtering behavior.

## Suggested behavior

### Stoplist filtering

System should:
- read `concept_stoplist.txt`
- normalize entries using same pipeline as tokens
- remove matching concepts from report

Example stoplist:
человек
идея
уровень
форма
смысл

### Allowlist (optional)

System may:
- preserve specific concepts even if they would otherwise be filtered
- override stoplist if needed

### Output improvement

After applying stoplist:
- core concepts should represent meaningful entities/themes
- secondary concepts should be more focused
- noise from abstract/general terms should be reduced

## Definition of Done

This layer is complete when:
1. Concept stoplist file is supported and loaded.
2. Stoplist concepts are excluded from corpus-report output.
3. Filtering works consistently across report sections.
4. Output quality improves (less abstract noise).
5. System remains deterministic and read-only.
6. No LLM usage is introduced.
7. Tests (if added) pass.
8. project-map.md is updated.
9. CURRENT_STATE.md is updated.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli corpus-report
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git diff --check
```
