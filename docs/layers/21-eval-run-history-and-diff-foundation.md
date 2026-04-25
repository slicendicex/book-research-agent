# Layer 21 — Eval Run History and Diff Foundation

## Purpose

Make eval runs easier to use after prompt-based reranking by reducing manual
steps around saving, comparing, and cleaning up eval outputs.

Layer 19 made eval observable, but everyday usage is still awkward:
- `eval` must be called with `--json-out` to preserve a run
- before/after reranking comparison requires manual inspection
- saved run files accumulate without lifecycle management

This layer keeps eval file-based and CLI-first, but makes it practical as a
repeatable retrieval inspection tool.

## Goal

Add a narrow eval run lifecycle layer that:
- auto-saves eval runs by default into `data/eval/runs/`
- adds a CLI compare mode for two saved eval run files
- supports concise compare input without repeating full paths
- supports comparing the two latest saved run files
- adds simple retention cleanup for old run files
- keeps saved eval runs outside normal git tracking
- keeps existing eval semantics and JSON structure intact

## In scope

1. Auto-save `eval` runs by default without requiring `--json-out`.
2. Use deterministic human-readable run filenames with timestamps.
3. Keep `--json-out` as an explicit override path.
4. Add a new CLI command for file-vs-file comparison, for example:
   - `eval-compare <run_a> <run_b>`
   - `eval-compare --latest`
5. Print a concise human-readable diff in the CLI.
6. Optionally support diff export through `--json-out`.
7. Compare only existing eval run data:
   - summary counts
   - per-case status changes
   - changed `top_paths`
   - changed `top_scores`
   - changed `unique_document_count`
   - changed `duplicate_like_count`
8. Add simple retention cleanup using a keep-last-N policy.
9. Use a conservative default retention value such as the newest `20` run files.
10. Ignore eval run artifacts in git with:
   - `data/eval/runs/*`
   - `!data/eval/runs/.gitkeep`
11. Keep the implementation stdlib-only, file-based, and additive.
12. Add narrow deterministic tests.

Do not change eval case meaning, reranking logic, provider behavior, retrieval
behavior, or answer-generation behavior in this layer.

## Suggested behavior

### Auto-save

Running:

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval
```

should automatically write a run file into `data/eval/runs/` using a stable
timestamped name, for example:

```text
data/eval/runs/2026-04-25T13-20-10_eval.json
```

The command should print the saved path explicitly, for example:

```text
saved_run: data/eval/runs/2026-04-25T13-20-10_eval.json
```

If `--json-out` is provided, the explicit path should be used instead of the
default auto-save location.

### Compare mode

Running:

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval-compare \
  before.json \
  after.json
```

should print a concise diff showing:
- summary deltas
- cases with changed status
- cases with changed retrieval snapshots or observability metrics

The compare command should resolve short filenames inside `data/eval/runs/` by
default, so users do not need to repeat the full directory path each time.

If a passed argument already exists as an explicit relative or absolute path,
that path should be used as-is.

Running:

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval-compare --latest
```

should compare the two newest saved run files in `data/eval/runs/`.

If `--json-out` is provided, the diff should also be written as a structured
JSON file.

### Retention

After an auto-saved run is written, the system should prune older auto-saved
run files and keep only the newest configured count.

Retention should stay simple:
- keep newest N files
- delete only auto-saved files matching the strict pattern `YYYY-MM-DDTHH-MM-SS_eval.json`
- do not delete manual baseline files such as `manual.json`, `before-rerank.json`, or `after-rerank.json`
- do not delete files outside the run directory
- do not require a database or background cleanup process

## Definition of Done

- `eval` auto-saves a run file by default.
- `--json-out` still works as an explicit override.
- auto-saved run filenames are deterministic and human-readable.
- `eval` prints `saved_run: ...` after writing an auto-saved or explicit run file.
- `eval-compare` exists and compares two saved run files.
- short filenames are resolved inside `data/eval/runs/` by default.
- `eval-compare --latest` compares the two newest saved run files.
- compare output is concise and useful in the CLI.
- optional diff JSON output works.
- retention cleanup keeps only the newest configured auto-saved run files.
- manual baseline files are not deleted by retention.
- eval run artifacts are ignored in git except for `.gitkeep`.
- existing eval JSON structure remains usable.
- no reranking, retrieval, provider, or answer logic changes are introduced.
- tests cover auto-save, compare behavior, diff export, and retention cleanup.
- `docs/project-map.md` and `CURRENT_STATE.md` are updated concisely when the layer is implemented.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval-compare --latest
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval --json-out data/eval/runs/manual.json
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval-compare --latest --json-out data/eval/runs/latest-diff.json
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git diff --check
```
