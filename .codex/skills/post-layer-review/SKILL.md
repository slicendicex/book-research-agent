---
name: post-layer-review
description: Review a completed `book-research-agent` project layer before commit or push. Use after layer implementation to check scope discipline, git hygiene, diffs, verification, docs/state hygiene, unsafe files, and whether the layer is safe to commit.
---

# Post Layer Review

Use this skill after a layer has been implemented and before final commit or push.

The goal is to confirm that the layer stayed narrow, the repo is clean enough, and no unrelated or unsafe files are being included.

## Review Checklist

### 1. Scope Check

Confirm that:

- the implementation matches the active layer doc
- no obvious out-of-scope features were added
- stable existing layers were not changed unnecessarily

### 2. Git Hygiene

Check:

- `git status`
- staged vs unstaged changes
- whether unrelated files are present

Flag especially:

- logs
- `.env`
- private corpus files
- processed artifacts
- index artifacts
- tmux / OMX runtime files
- `Zone.Identifier` files

### 3. Diff Review

Inspect the changes and summarize:

- which files changed
- whether the changes are coherent
- whether any file looks unexpectedly large or unrelated

### 4. Verification Review

Confirm:

- tests passed
- smoke checks passed
- known failures are explained clearly

### 5. Docs / State Hygiene

Check:

- `docs/project-map.md` was updated if needed
- `CURRENT_STATE.md` was updated concisely
- `CURRENT_STATE.md` did not become a verbose changelog

## Commit Gate

Do not recommend commit or push if:

- unrelated files are included
- verification is missing without explanation
- private or unsafe files are staged
- the layer clearly drifted beyond scope

## Required Output

Return a compact review with:

1. scope held / scope drift
2. repo clean / repo not clean
3. unrelated files found / not found
4. verification status
5. notes before commit
6. final commit recommendation
