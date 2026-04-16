# Layer 13 — Grounded Eval Foundation

## Purpose

Introduce a minimal evaluation layer to verify that the agent remains retrieval-grounded and stable after changes.

This layer is not about scoring or benchmarking.
It is about detecting regressions and preserving grounded behavior.

## Goal

Implement a narrow evaluation layer that:
- validates retrieval presence
- validates basic answer output
- detects obvious breakages after changes
- keeps implementation simple and CLI-first

## In scope

1. Add a small set of eval cases (golden queries).
2. Implement a lightweight eval runner.
3. Add a CLI command `eval`.
4. Perform basic checks:
   - retrieval exists
   - answer is non-empty
5. Print per-case results and a summary.
6. Update `docs/project-map.md`.
7. Update `CURRENT_STATE.md` concisely.
8. Keep implementation minimal and readable.

## Suggested behavior

### Eval philosophy
- not a scoring system
- not a correctness judge
- a system health check

### What we check

For each case:

Retrieval:
- at least 1 chunk found → PASS
- no chunks → FAIL

Answer (for answer-facing modes):
- non-empty → PASS
- empty → FAIL

Soft signals:
- low retrieval → WARN

### Output format

Example:

[answer_1] PASS
[canon_1] PASS
[compare_1] WARN (low retrieval)
[contradict_1] PASS

Summary:
PASS: 3
WARN: 1
FAIL: 0

## Eval data format

File:
data/eval/eval_cases.jsonl

Example:

{"id": "answer_1", "mode": "answer", "query": "What does the auditor represent?"}
{"id": "canon_1", "mode": "canon", "query": "auditor language"}
{"id": "compare_1", "mode": "compare", "query": "auditor || old man"}
{"id": "contradict_1", "mode": "contradict", "query": "auditor as protector || auditor as destroyer"}

Notes:
- keep 5–10 cases
- no heavy schema
- keep simple

## Definition of Done

Layer is complete when:

1. Eval cases file exists.
2. CLI command `eval` runs.
3. Each case is executed.
4. Retrieval is checked.
5. Answer presence is checked.
6. Results are printed per case.
7. Summary is printed.
8. No unnecessary abstractions introduced.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval
```

## Architecture notes

- Lives in core layer
- Uses existing pipelines
- No new provider logic
- Stateless runner
- File-based eval cases


