# Layer 22 — RAG Trace Artifact Foundation

## Purpose

Improve end-to-end inspectability for answer-facing RAG flows after prompt-based
reranking and eval observability upgrades.

The project can already inspect:
- retrieval outputs
- source-facing evidence
- eval snapshots
- before/after eval diffs

But it still does not persist a compact local artifact showing what actually
happened between retrieval and final generated output for answer-facing modes.

This layer adds a narrow, optional trace artifact path for debugging grounded
answers without changing the current retrieval or eval architecture.

## Goal

Add a local, file-based trace artifact for answer-facing CLI flows that captures:
- the input query or query pair
- the larger retrieval candidate set before final selection
- the final evidence set after reranking
- the source metadata and compact evidence text used
- the generated output text

The trace must remain:
- optional
- local-only
- read-only
- CLI-first
- separate from eval semantics

## In scope

1. Add a small trace model and JSON serialization layer for answer-facing runs.
2. Add a local trace artifact directory, for example `data/traces/`.
3. Keep trace artifacts out of git with:
   - `data/traces/*`
   - `!data/traces/.gitkeep`
4. Support answer-facing modes only:
   - `answer`
   - `canon`
   - `compare`
   - `contradict`
   Do not add `search` tracing in this layer.
5. Add a narrow CLI path to save a trace only when explicitly requested.
6. Support either:
   - `--save-trace` for default auto-named local trace files
   - `--trace-out <path>` for an explicit output path
7. Capture compact trace fields such as:
   - mode
   - query or left/right queries
   - candidate chunk ids before final evidence selection
   - candidate source paths/titles
   - candidate scores
   - reranked intermediate order if it is easy to capture without reshaping the
     retrieval flow
   - final selected chunk ids
   - final selected source paths/titles
   - final selected scores
   - compact evidence blocks or prompt-ready source blocks
   - generated answer/judgment/comparison text
8. Print the saved trace path explicitly when a trace is written.
9. Add narrow deterministic tests using stub providers and no real OpenAI calls.
10. Do not apply retention cleanup to explicit `--trace-out` paths.

Do not:
- change retrieval ranking behavior
- change reranking logic
- change PASS/WARN/FAIL eval semantics
- add RAGAS
- add dashboards
- add UI
- add a database
- auto-save traces for every command by default

## Suggested behavior

When a normal answer-facing command runs without trace flags, behavior stays
unchanged.

When a user explicitly asks for tracing, for example:

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli answer \
  "What does the auditor represent?" \
  --save-trace
```

the command should:

1. run the existing retrieval and reranking path
2. preserve the larger candidate set before final evidence trimming
3. preserve the final selected evidence set
4. capture compact evidence blocks or prompt-ready source blocks for the final
   set rather than full raw document text
5. capture the final generated output text
6. write a local JSON trace artifact
7. print:

```text
saved_trace: data/traces/2026-04-28T18-20-10_answer_trace.json
```

If `--trace-out` is provided, that explicit path should be used instead of the
default trace location. Explicit trace paths must not be deleted or affected by
any retention logic in this layer.

For pair modes:
- `compare` traces should include separate `left` and `right` sections
- `contradict` traces should include separate `left` and `right` sections
- each side should preserve its own query, candidate evidence, and final
  evidence information

If reranked intermediate ordering is trivial to capture, it may be included.
If not, the minimum required trace shape is:
- `retrieval_candidates`
- `final_evidence`

The trace artifact should remain diagnostic, not normative. It exists to inspect
what the system did, not to change the result or grade it.

## Definition of Done

- A narrow trace artifact model exists for answer-facing runs.
- Trace artifacts can be written locally for `answer`, `canon`, `compare`, and
  `contradict`.
- Normal command behavior is unchanged when tracing is not requested.
- Trace artifacts contain:
  - mode
  - query data
  - candidate retrieval ids/metadata before final selection
  - reranked intermediate order only if easy to capture
  - final selected evidence ids/metadata
  - compact evidence blocks or prompt-ready excerpts used
  - final generated output text
- Pair mode traces use separate `left` and `right` sections.
- Trace artifacts stay outside git except for a `.gitkeep` placeholder and
  explicit ignore rules for `data/traces/*`.
- Trace path output is printed clearly when a trace is saved.
- Explicit `--trace-out` paths are never affected by retention cleanup.
- Tests use stub providers, are deterministic, and do not make real network
  calls.
- `docs/project-map.md` and `CURRENT_STATE.md` are updated concisely when the
  layer is implemented.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli answer "What does the auditor represent?" --save-trace
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli canon "auditor language" --save-trace
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli compare "auditor" "old man" --save-trace
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli contradict "auditor as protector" "auditor as destroyer" --save-trace
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git diff --check
```
