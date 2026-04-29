# Layer 23 — Mode-Aware Generation Output Budgets

## Purpose

Fix answer-facing output truncation without changing retrieval behavior, trace
artifacts, or prompt structure.

Layer 22 traces exposed that one shared generation output budget is too coarse:
- `answer`, `canon`, and `contradict` may fit within a moderate limit
- `compare` can still truncate
- reranking does not need the same budget as answer-facing generation

This layer separates output budgets by mode so the project can preserve short
reranking responses while giving answer-facing modes enough space to finish.

## Reason
Layer 22 trace artifacts exposed answer-facing output truncation caused by a shared low generation budget.
## Goal

Introduce narrow mode-aware generation output budgets for the existing OpenAI
generation path.

The new behavior should:
- keep reranking on a small output ceiling
- keep answer/canon/contradict on a moderate output ceiling
- give compare a larger output ceiling
- avoid prompt changes
- avoid retrieval changes
- avoid trace format changes

## In scope

1. Add small configurable output budgets for:
   - reranking
   - answer
   - canon
   - contradict
   - compare
   Keep this mapping centralized in one explicit runtime policy structure, for
   example:

   ```python
   GENERATION_OUTPUT_BUDGETS = {
       "reranking": 256,
       "answer": 900,
       "canon": 900,
       "contradict": 900,
       "compare": 1400,
   }
   ```
2. Keep the implementation narrow and explicit.
3. Reuse the existing generation provider path.
4. Preserve current provider boundaries unless a minimal extension is required.
5. If needed, add a tiny mode-aware generation helper or provider method that
   accepts an output-budget parameter.
6. Update answer-facing and reranking call sites to use the correct budget for
   their mode.
7. Keep current prompt wording unchanged in this layer.
8. Keep trace artifact behavior unchanged except that generated outputs should
   no longer end mid-sentence due to low token ceilings.
9. Add deterministic tests with stub providers only.
10. Unit tests should verify budget routing, not live output length.

Do not:
- change compare prompt wording
- change retrieval ranking
- change reranking selection logic
- add new providers
- add truncation scoring or evaluation logic
- redesign the trace layer

## Suggested behavior

The project should stop using one shared generation output ceiling for all uses.

Instead, mode-aware budgets should be applied approximately like this:

- reranking:
  - small ceiling
  - enough for ordered candidate ids only

- answer:
  - moderate ceiling
  - enough for grounded answer + support + limits

- canon:
  - moderate ceiling
  - enough for structured canon judgment

- contradict:
  - moderate ceiling
  - enough for short verdict + explanation

- compare:
  - larger ceiling
  - enough for the structured compare response without mid-sentence truncation

The exact numbers should live in one centralized mapping rather than being
hardcoded separately across call sites.

The main rule is:
- reranking stays tight
- compare gets more headroom than the other answer-facing modes

Normal CLI behavior should remain the same except for reduced output truncation.

Trace artifacts should naturally reflect the improved outputs without any trace
schema change.

Unit tests should verify that:
- `answer` uses the answer budget
- `canon` uses the canon budget
- `contradict` uses the contradict budget
- `compare` uses the larger compare budget
- reranking uses the small reranking budget

Live smoke checks should then confirm, at a human level, that the previous
truncation is no longer showing up in the standard cases.

## Definition of Done

- The project no longer relies on one shared generation output ceiling.
- Reranking uses a smaller budget than answer-facing generation.
- Compare uses a larger budget than answer/canon/contradict.
- Prompt wording is unchanged in this layer.
- Retrieval and reranking behavior remain functionally the same.
- Trace artifact schema is unchanged.
- Unit tests deterministically verify correct budget routing per mode and make
  no real network calls.
- The previous low-ceiling truncation is no longer observed in the standard
  smoke cases.
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
