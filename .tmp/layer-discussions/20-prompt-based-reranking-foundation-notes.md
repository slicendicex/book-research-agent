# Layer 20 — Prompt-Based Reranking Foundation Notes

## Proposed layer name

Layer 20 — Prompt-Based Reranking Foundation

## User intent

Add the first OpenAI prompt-based reranking layer after Layer 19 made eval snapshots useful for before/after retrieval comparison.

The goal is to improve evidence selection when raw semantic similarity finds related chunks but not necessarily the most useful, complete, canonical, or answer-supporting chunks.

## Problem statement

The current retrieval stack can find semantically similar chunks, but the top semantic hit is not always the best evidence for answering the query.

Layer 18 already added paragraph-aware chunking, diversity filtering, and near-duplicate suppression. A purely deterministic local reranker would likely duplicate that work under a different name.

Layer 20 should therefore introduce a narrow prompt-based candidate selection step:

semantic search -> larger candidate set -> OpenAI prompt-based candidate selection/reranking -> final evidence top_k

## In-scope ideas

- Use the existing OpenAI generation provider / generation path if possible.
- Retrieve a larger candidate set with the existing semantic search.
- Build a compact reranking prompt with:
  - query
  - candidate ids
  - short excerpts
  - source paths
  - source titles
- Ask the model to return only an ordered list of candidate ids.
- Select final `top_k` from the reordered candidates.
- Preserve original chunks, scores, source paths, titles, chunk ids, and metadata.
- Keep `search` as raw semantic retrieval for baseline use.
- Apply reranking first to user-facing evidence consumers:
  - `source`
  - `answer`
  - `canon`
  - `compare`
  - `contradict`
- Keep eval observability useful for before/after comparison.
- Add deterministic parsing and fallback tests around reranker output.

## Out-of-scope boundaries

- Do not add a new rerank provider abstraction yet.
- Do not add Cohere rerank.
- Do not add a vector database.
- Do not add LangChain or LangGraph.
- Do not change chunk schema.
- Do not change index format.
- Do not change source metadata.
- Do not rewrite or generate evidence.
- Do not allow the model to return free-form explanations as reranking output.
- Do not make `search` reranked by default.
- Do not add a reranking CLI flag in this first layer unless implementation requires it.
- Do not introduce broad domain-specific reasoning.

## Open questions resolved

- Reranking path: OpenAI prompt-based reranking, not deterministic local reranking.
- Main quality problem: semantic top hit is not always the best evidence.
- Baseline behavior: keep `search` raw semantic retrieval.
- Initial consumers: apply to `source`, `answer`, `canon`, `compare`, and `contradict`.
- Failure behavior: if reranking fails or output cannot be parsed, fall back to original semantic order.

## Implementation direction

Add a small core reranking module that can:

1. Accept a query, candidate `SearchResult` list, generation provider, and final `top_k`.
2. Build a compact prompt containing stable candidate ids and short excerpts.
3. Request an ordered id list from the existing generation provider.
4. Parse the response strictly.
5. Reorder known candidates by returned ids.
6. Ignore unknown ids and duplicate ids.
7. Fill missing slots from the original candidate order.
8. Fall back fully to original semantic order when parsing fails or no usable ids are returned.

Integrate the reranking step after larger candidate retrieval and before final evidence selection in evidence-consuming modes. Preserve existing `SearchResult` objects rather than constructing rewritten evidence.

## Suggested verification ideas

- Unit tests for prompt construction shape without private corpus text.
- Unit tests for parsing valid ordered id output.
- Unit tests for ignoring unknown and duplicate ids.
- Unit tests for filling missing candidates from original semantic order.
- Unit tests for fallback when output is malformed or empty.
- Existing mode tests updated only where reranking changes evidence selection path.
- Smoke checks:
  - `PYTHONPATH=src .venv/bin/python -m book_research_agent.cli source "auditor"`
  - `PYTHONPATH=src .venv/bin/python -m book_research_agent.cli answer "What does the auditor represent?"`
  - `PYTHONPATH=src .venv/bin/python -m book_research_agent.cli canon "auditor language"`
  - `PYTHONPATH=src .venv/bin/python -m book_research_agent.cli compare "auditor" "old man"`
  - `PYTHONPATH=src .venv/bin/python -m book_research_agent.cli contradict "auditor as protector" "auditor as destroyer"`
  - `PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval --json-out data/eval/runs/dev.json`
  - `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v`
  - `git diff --check`

## Risks to control

- Model output may be malformed, verbose, duplicated, or include unknown ids.
- Prompt excerpts may leak too much context or become too large.
- Reranking may accidentally reduce traceability if candidate ids are not mapped back to original `SearchResult` objects.
- Applying reranking to compare/contradict may need care because each side has its own query and candidate set.
- Eval should remain observability-oriented, not become gold-label judging.
