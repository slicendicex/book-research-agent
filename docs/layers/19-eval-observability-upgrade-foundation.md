# Layer 19 — Eval Observability Upgrade Foundation

## Purpose

Improve the usefulness of `eval` before reranking by making retrieval behavior visible, comparable, and easy to inspect over time.

This layer is not a benchmark system.
It is a retrieval-observability upgrade for a living corpus.

## Goal

Implement a narrow evaluation upgrade that:
- keeps the existing health-check behavior
- records what retrieval actually returned
- makes before/after reranking comparisons practical
- works without requiring pre-labeled "correct" source documents
- stays deterministic, file-based, and CLI-first

## Why this layer exists

The current eval is useful as a smoke check, but too weak for retrieval quality work.

It currently tells us:
- whether retrieval exists
- whether answer output is non-empty

It does not tell us:
- which sources were retrieved
- how redundant the top results were
- whether top-k became more diverse
- how retrieval changed before and after reranking

For this project, that matters more than early gold-label scoring.

## Non-Goals

- no gold answer grading
- no LLM-as-judge
- no source correctness benchmark
- no reranking implementation yet
- no new provider logic
- no dashboard
- no database
- no complex experiment framework

## In scope

1. Extend eval results with retrieval snapshot fields.
2. Record the top retrieved source paths/chunk ids/scores per case.
3. Add small retrieval-quality observability metrics.
4. Add machine-readable eval output via JSON file.
5. Preserve existing PASS / WARN / FAIL health-check behavior.
6. Keep eval cases simple and file-based.
7. Update `docs/project-map.md`.
8. Update `CURRENT_STATE.md` concisely.
9. Add narrow deterministic tests.

## Retrieval snapshot fields

Each eval result should be able to include:
- `top_paths`
- `top_titles`
- `top_chunk_ids`
- `top_scores`

These fields are for inspection and before/after comparison.
They are not gold labels.

## Retrieval-quality observability metrics

Add a small set of metrics that do not require knowing the "correct" source:
- `unique_document_count`
- `top_path_repeat_count`
- `duplicate_like_count` or equivalent suppression count
- `score_spread`

These metrics should stay simple and deterministic.
They should help detect:
- overly repetitive top-k output
- weak diversity
- unstable or shallow retrieval

## Suggested behavior

### Existing health-check behavior stays

Keep current checks:
- no retrieval -> FAIL
- empty answer -> FAIL
- low retrieval -> WARN
- retrieval exists + answer exists -> PASS or WARN depending on retrieval depth

### New observability behavior

For each eval case:
- run retrieval
- keep the final top-k that the system would actually use
- store the top retrieval snapshot
- compute small retrieval-quality metrics
- print the usual status
- optionally write full structured results to JSON

## Eval cases format

Keep eval cases simple:

```json
{"id": "answer_1", "mode": "answer", "query": "What does the auditor represent?"}
{"id": "canon_1", "mode": "canon", "query": "auditor language"}
{"id": "compare_1", "mode": "compare", "query": "auditor || old man"}
{"id": "contradict_1", "mode": "contradict", "query": "auditor as protector || auditor as destroyer"}
```

Optional lightweight metadata is acceptable, for example:
- `notes`

Do not require:
- expected paths
- gold chunks
- gold answers

## CLI upgrade

Extend the existing `eval` command with an optional output flag:

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval \
  --json-out data/eval/runs/before-rerank.json
```

This should write a structured report containing:
- summary
- per-case results
- retrieval snapshot fields
- observability metrics

## Example JSON output shape

```json
{
  "summary": {
    "pass_count": 3,
    "warn_count": 1,
    "fail_count": 0
  },
  "results": [
    {
      "case_id": "answer_1",
      "mode": "answer",
      "status": "PASS",
      "retrieval_count": 3,
      "answer_present": true,
      "top_paths": ["auditor2.txt", "oldman vs auditor.txt"],
      "top_chunk_ids": ["doc-1:0", "doc-8:2"],
      "top_scores": [0.82, 0.77],
      "unique_document_count": 2,
      "top_path_repeat_count": 1,
      "score_spread": 0.05
    }
  ]
}
```

## Acceptance Criteria

- `eval` still works as a minimal health check
- per-case retrieval snapshot is available
- structured JSON output can be written
- retrieval observability metrics are visible
- implementation stays narrow and file-based
- no reranking logic is introduced in this layer
- tests pass
- docs are updated concisely

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval --json-out data/eval/runs/dev.json
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git diff --check
```

## Notes

- This layer is designed for a growing corpus.
- It should remain useful even when `data/raw` changes over time.
- For fair before/after reranking comparison, run eval on the same processed/index snapshot.
- This layer improves visibility, not truth judgment.
