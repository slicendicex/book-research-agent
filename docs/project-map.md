# Project Map

## Title

book-research-agent

## Current status

Initial repository scaffold created, with local Python environment, runnable CLI scaffold, automatic local `.env` loading, AI boundary/config foundation, document ingestion, paragraph-aware chunking, OpenAI embedding/index foundation, source-facing retrieval, retrieval-grounded answer assembly, read-only corpus diagnostics, compact canon-aware answer guidance, grounded compare mode, contradiction/tension mode, read-only duplicate detection, a narrow canon judgment mode, improved grounding prompts with mode-aware retrieval depth defaults, a retrieval-observability eval upgrade, and a read-only morphology-aware concept-level corpus coverage report with project concept curation.

## Current structure

- `data/raw/`
- `data/processed/`
- `data/index/`
- `data/config/concept_stoplist.txt`
- `data/eval/eval_cases.jsonl`
- `docs/layers/`
- `docs/layers/00-ai-boundary-config.md`
- `docs/layers/01-document-ingestion.md`
- `docs/layers/02-chunking-layer.md`
- `docs/layers/03-embedding-index-foundation.md`
- `docs/layers/04-source-retrieval-mode.md`
- `docs/layers/05-generation-answer-assembly.md`
- `docs/layers/06-corpus-diagnostics.md`
- `docs/layers/07-domain-pack-canon-foundation.md`
- `docs/layers/08-compare-mode-foundation.md`
- `docs/layers/09-contradiction-tension-foundation.md`
- `docs/layers/10-corpus-hygiene-duplicate-detection.md`
- `docs/layers/11-canon-mode-foundation.md`
- `docs/layers/12-answer-quality-grounding-improvements.md`
- `docs/layers/13-grounded-eval-foundation.md`
- `docs/layers/14-corpus-coverage-report-foundation.md`
- `docs/layers/15-concept-normalization-surface-report-foundation.md`
- `docs/layers/16-pymorphy-pos-filter-foundation.md`
- `docs/layers/17-concept-curation-domain-stoplist-foundation.md`
- `docs/layers/18_chunking_retrieval_upgrade_foundation.md`
- `docs/layers/19-eval-observability-upgrade-foundation.md`
- `requirements.txt`
- `src/book_research_agent/core/`
- `src/book_research_agent/core/chunks/`
- `src/book_research_agent/core/chunking/`
- `src/book_research_agent/core/config/`
- `src/book_research_agent/core/config/env.py`
- `src/book_research_agent/core/corpus_report/`
- `src/book_research_agent/core/diagnostics/`
- `src/book_research_agent/core/documents/`
- `src/book_research_agent/core/ingestion/`
- `src/book_research_agent/core/indexing/`
- `src/book_research_agent/core/evaluation/`
- `src/book_research_agent/core/generation/`
- `src/book_research_agent/core/generation/openai_generation.py`
- `src/book_research_agent/core/hygiene/`
- `src/book_research_agent/core/answering/`
- `src/book_research_agent/core/answering/defaults.py`
- `src/book_research_agent/core/answering/compare.py`
- `src/book_research_agent/core/answering/contradiction.py`
- `src/book_research_agent/core/answering/canon.py`
- `src/book_research_agent/core/providers/`
- `src/book_research_agent/core/providers/openai_embeddings.py`
- `src/book_research_agent/core/retrieval/`
- `src/book_research_agent/core/retrieval/source.py`
- `src/book_research_agent/domain/`
- `src/book_research_agent/domain/canon.py`
- `src/book_research_agent/corpus/`
- `src/book_research_agent/config.py`
- `src/book_research_agent/cli.py`
- `tests/`

## What exists now

- Base repository metadata and setup files
- Initial scaffold directories
- Empty package markers for scaffold layers
- Local `.venv/` Python environment
- Minimal runnable CLI scaffold and basic path configuration
- Runtime settings loaded from environment variables
- CLI startup automatically loads project-root `.env` without overriding shell variables
- Reusable provider interfaces with dummy implementations and a local factory
- `doctor` CLI command for safe configuration inspection
- Document models for normalized local source files
- Ingestion pipeline for `.txt` and `.md` files from `data/raw/`
- JSONL export to `data/processed/documents.jsonl`
- Paragraph-aware chunking from `documents.jsonl` to `chunks.jsonl` with character fallback for oversized paragraphs
- Chunk metadata that preserves document traceability
- Minimal ingestion tests
- Minimal chunking tests
- OpenAI as the active embedding provider
- Local file-based chunk index in `data/index/chunk_index.jsonl`
- Plain cosine-similarity semantic search over indexed chunks with lightweight diversity filtering
- Source-facing retrieval formatting with readable excerpts
- Light same-document neighbor suppression for source-mode output
- Dedicated `source` CLI command for source-first retrieval display
- OpenAI as the active generation provider
- Retrieval-grounded answer assembly with visible source references
- Dedicated `answer` CLI command for short grounded answers
- Read-only corpus diagnostics commands: `stats`, `inspect-doc`, `inspect-chunk`, `inspect-index`
- Compact domain pack for canon-aware answer wording without overriding retrieved sources
- Dedicated `compare` CLI command for short grounded comparisons with visible sources for both sides
- Dedicated `contradict` CLI command for cautious grounded contradiction/tension judgments
- Read-only duplicate detection commands: `dedup-stats`, `find-duplicates`, `find-duplicate-chunks`
- Dedicated `canon` CLI command for short cautious canon-oriented judgments with visible sources
- Mode-aware answer-facing source depth defaults and stricter grounding prompt structure
- Dedicated `eval` CLI command for retrieval snapshots, lightweight observability metrics, and optional JSON report output
- Dedicated `corpus-report` CLI command for pymorphy-backed normalized concepts, project-curated concept filtering, secondary concept lines, co-occurrences, and potential orphan notes

## What is still missing

- Additional provider hardening beyond the current OpenAI and Cohere paths
- Deeper domain-specific reasoning beyond the compact prompt lens

## Next logical layer

Broader reasoning and provider expansion built on top of the canon-aware answer, compare, contradiction, canon, diagnostics, corpus hygiene, retrieval-observability evals, curated morphology-aware concept-level corpus coverage, and upgraded chunking/retrieval foundation.
