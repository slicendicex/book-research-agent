# Architecture Decisions

This file records a small set of practical decisions that shape the project.

## 1. CLI-first before interface expansion

The project remains CLI-first.

Reason:
This keeps each layer easier to inspect, test, and evolve without adding UI
complexity too early.

Implication:
The system is optimized for clarity and controllability first, not for
interface polish.

## 2. Retrieval stays primary

The project is built retrieval-first, not generation-first.

Reason:
This is a private and evolving corpus. Source traceability matters more than
polished but weak answers.

Implication:
Answer, compare, contradict, and canon modes are built on top of retrieval
rather than replacing it.

## 3. Domain awareness stays thin

Domain awareness is implemented as a compact prompt lens, not as a full
reasoning engine.

Reason:
The system should use canon-aware wording and interpretation, but retrieved
sources must remain the primary truth source.

Implication:
Domain guidance shapes wording and framing, but does not override evidence.

## 4. Eval uses observability, not gold-source grading

At Layer 19, a stricter eval design based on `expected_path` per eval case was
considered and rejected.

Problem:
The corpus is live, keeps changing, and the notes are structurally uneven. In
many cases there is no stable gold source, including cases where I would not be
able to identify one honestly myself.

Decision:
Eval was upgraded toward observability rather than correctness scoring.

Chosen signals:
- `top_paths`
- `top_scores`
- `unique_document_count`
- `duplicate_like_count`

Reason:
For this project, retrieval state and retrieval behavior are more useful than
pretending there is a stable benchmark where there is not.

Implication:
Eval is used to inspect and compare retrieval before and after changes such as
reranking, not to claim benchmark-style correctness.

## 5. OpenAI is the active provider path

The project moved away from Cohere as the main embedding and reranking path.

Reason:
The main issue was practical provider use and payment constraints, not
theoretical capability.

Decision:
OpenAI is the active path for embeddings, retrieval support, and the current
reranking direction through prompt-based logic.

Implication:
The provider stack stays narrower, but more operationally reliable for the
current project.

## 6. No concept graph for this corpus

A concept graph / neighborhood map was considered and rejected.

Problem:
The notes are fragmented, uneven, and not structurally dense enough for
graph-style concept extraction to be trustworthy.

Reason:
Concept graphs work better on dense corpora with repeated stable concepts. On
broken notes, graph edges are likely to be noisy or accidental:
- small chunks may over-amplify the wrong entity
- large chunks may hide important structure in the middle

Decision:
The project keeps corpus analysis focused on retrieval, diagnostics, and
read-only reporting instead of graph-building.

Implication:
The system gives up a more ambitious exploratory view, but avoids adding a
layer that would look more meaningful than it really is.

## 7. Optional RAGAS layer postponed

RAGAS was considered as an optional faithfulness probe on top of saved eval runs.

Decision:
Do not add it yet.

Reason:
The current eval system is intentionally observability-oriented and already supports retrieval inspection. RAGAS would add an LLM-as-judge layer and extra dependencies before the project clearly needs them.

Implication:
RAGAS remains a later optional diagnostic layer, not a replacement for existing evals.