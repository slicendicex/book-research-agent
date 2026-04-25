# Layer 20 — Prompt-Based Reranking Foundation

## Purpose

Improve evidence selection after semantic retrieval.

Semantic search finds related chunks, but the highest semantic hit is not always
the most useful, complete, canonical, or answer-supporting evidence for a query.
Layer 18 already improved chunking, diversity filtering, and duplicate
suppression. This layer adds a narrow prompt-based reranking step instead of
duplicating deterministic retrieval filtering.

## Goal

Introduce OpenAI prompt-based candidate selection on top of the existing
retrieval stack:

semantic search -> larger candidate set -> prompt-based candidate ordering -> final evidence `top_k`

The reranker must select and reorder existing candidate ids only. It must not
rewrite, summarize, or generate evidence.

## In scope

1. Add a small core reranking path that uses the existing generation provider.
2. Retrieve a larger semantic candidate set before final evidence selection.
3. Build a compact reranking prompt containing:
   - query
   - stable candidate ids
   - short excerpts
   - source paths
   - source titles
4. Parse an ordered list of candidate ids from the model response.
5. Reorder existing `SearchResult` objects by returned candidate ids.
6. Ignore duplicate or unknown ids.
7. Fill missing final slots from the original semantic order.
8. Fall back to original semantic order if reranking fails or output cannot be parsed.
9. Apply reranking to user-facing evidence consumers:
   - `source`
   - `answer`
   - `canon`
   - `compare`
   - `contradict`
10. Keep `search` as raw semantic retrieval for baseline inspection.
11. Preserve existing chunk schema, index format, source metadata, scores, and traceability.
12. Keep eval observability useful for before/after retrieval comparison.
13. Add narrow deterministic tests for prompt construction, parsing, ordering, and fallback behavior.

Do not add a new rerank provider abstraction, Cohere rerank, vector database,
LangChain, LangGraph, source rewriting, generation of evidence, or a reranking
CLI flag in this layer unless implementation requires the smallest possible
internal switch.

## Suggested behavior

For each reranked evidence request:

1. Run existing semantic search with a candidate count larger than final `top_k`.
2. Convert candidates into stable ids local to the reranking request.
3. Build a compact prompt asking the model to return only ordered candidate ids.
4. Parse the response strictly.
5. Keep only ids that map to known candidates.
6. Preserve each selected candidate as the original `SearchResult`.
7. Fill any remaining result slots from semantic order.
8. Return the final `top_k` evidence results to the existing consumer.

If the model response is empty, malformed, verbose, duplicated, or unusable,
the caller should receive the original semantic candidate order trimmed to
`top_k`.

For compare and contradiction flows, rerank each side independently using that
side's query and candidate set.

## Definition of Done

- Prompt-based reranking exists as a narrow core retrieval helper.
- The reranker uses the existing generation provider path.
- The reranker returns existing candidates only.
- Source paths, titles, chunk ids, scores, and metadata remain traceable.
- Invalid reranker output falls back to semantic order.
- `search` remains raw semantic retrieval.
- `source`, `answer`, `canon`, `compare`, and `contradict` use reranked evidence.
- Eval still runs and keeps retrieval snapshot fields useful for comparison.
- No chunk schema or index format changes are introduced.
- No new provider, vector database, LangChain, LangGraph, or Cohere rerank dependency is added.
- Tests cover parsing, duplicate ids, unknown ids, partial ids, malformed output, and fallback.
- `docs/project-map.md` and `CURRENT_STATE.md` are updated concisely when the layer is implemented.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli source "auditor"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli answer "What does the auditor represent?"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli canon "auditor language"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli compare "auditor" "old man"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli contradict "auditor as protector" "auditor as destroyer"
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval
PYTHONPATH=src .venv/bin/python -m book_research_agent.cli eval --json-out data/eval/runs/dev.json
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git diff --check
```
