## Purpose

Upgrade corpus observability from raw token frequency to concept-level understanding by introducing normalization and semantic grouping.

## Goal

Implement a corpus intelligence layer that:
- normalizes Russian word forms into unified concepts
- filters low-signal and overly generic terms
- groups tokens into concept buckets
- surfaces meaningful concept-level structures instead of raw tokens

## In scope

1. Add normalization for Russian word forms (basic lemmatization or heuristic normalization).
2. Introduce stoplist filtering (common + project-specific low-signal terms).
3. Group tokens into concept buckets (e.g., аудитор/аудитора → АУДИТОР).
4. Update corpus-report logic to operate on concepts instead of raw tokens.
5. Surface:
   - core concepts (high frequency, high document spread)
   - secondary concept lines (moderate frequency)
6. Introduce simple co-occurrence analysis between concepts.
7. Keep system deterministic and LLM-free.
8. Keep everything read-only.
9. Update project-map.md and CURRENT_STATE.md.
10. Add minimal tests if needed.

## Suggested behavior

### Normalization

System should:
- convert tokens to normalized form (lowercase + base form)
- merge morphological variants into single concept

### Stop filtering

System should:
- remove:
  - common stop words
  - overly generic domain words (e.g., "система")

### Concept grouping

System should:
- map normalized tokens → concept buckets
- track:
  - total occurrences
  - number of documents

### Concept surfacing

Output:

Core concepts:
- high frequency + high document spread

Secondary concepts:
- moderate frequency but meaningful repetition

### Co-occurrence

System should:
- detect concepts that frequently appear together
- output strongest pairs

Example:

Core concepts:
- АУДИТОР
- СТАРИК
- МУЗЕЙ

Strong co-occurrences:
- АУДИТОР <-> СИСТЕМА
- СТАРИК <-> ЧИТАТЕЛЬ

Secondary lines:
- РИТУАЛ
- ЛЕС

## Definition of Done

This layer is complete when:
1. Russian word forms are normalized.
2. Concept buckets replace raw tokens.
3. Low-signal terms are filtered.
4. Core and secondary concepts are surfaced.
5. Co-occurrence relationships are visible.
6. Output is significantly more meaningful than Layer 14.
7. No LLM usage is introduced.
8. Tests (if added) pass.
9. project-map.md is updated.
10. CURRENT_STATE.md is updated.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli corpus-report
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git diff --check
```
