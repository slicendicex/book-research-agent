---
name: layer-execution
description: Execute one narrow `book-research-agent` project layer using `AGENTS.md`, `CURRENT_STATE.md`, and the latest active layer doc in `docs/layers/`. Use when implementing a single additive layer, updating project state docs, and running that layer's verification without broad refactors or speculative redesign.
---

# Layer Execution

Use this skill when implementing one project layer in `book-research-agent`.

This skill is for narrow additive layer work, not broad refactors or speculative redesign.

## Required Inputs

Before acting, read:

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. the active layer doc in `docs/layers/`

If multiple layer docs look active, choose the highest-numbered normal layer doc and ignore `:Zone.Identifier` files.

## Operating Rules

1. Implement only the active layer.
2. Keep scope narrow and additive.
3. Do not rewrite stable working layers without strong reason.
4. Keep retrieval grounding and traceability intact.
5. Keep CLI thin.
6. Avoid unrelated refactors.
7. Do not add features that are out of scope for the active layer.
8. Do not turn `CURRENT_STATE.md` into a diary.
9. Preserve user worktree changes that are unrelated to the layer.

## Required Updates

Update only what is necessary:

- `docs/project-map.md`
- `CURRENT_STATE.md`

When updating `CURRENT_STATE.md`:

- keep the section structure stable
- keep wording concise
- update only the relevant sections

## Verification Rule

Run the verification commands defined by the active layer doc.

Prefer:

- narrow tests for the layer
- minimal relevant smoke checks

Do not expand verification unnecessarily unless the layer is risky.

## Refusal Conditions

Stop and ask for clarification only if:

- the active layer doc is missing
- the required scope is internally contradictory
- implementation would require breaking an existing stable layer

## Final Response

At the end, return:

1. changed files
2. short architecture summary
3. verification commands
4. verification results
5. remaining notes or risks
6. suggested commit message
