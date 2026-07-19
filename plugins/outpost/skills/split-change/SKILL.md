---
name: split-change
description: Use when a change has grown to do more than one thing. Detects the separable concerns and splits them into focused commits or PRs, so each is small, reviewable, and revertible on its own.
---

# split-change

Use this when one diff has grown to do more than one thing. Split the concerns so each commit or PR
does one job, is easier to review, and is easier to revert. Run it before `prepare-pr` when the
change no longer fits in one sentence.

## When to use it

- A diff or branch that does more than one logical thing, or that you cannot summarize in one sentence.
- Not for a change that is already one concern; go straight to prepare-pr.

## Required inputs

- The working diff or branch.
- The intent of each part, so the split follows concerns, not just files.

## Steps

1. List the concerns in the diff. Name each in a few words. If there is only one, stop and continue to `prepare-pr`.
2. Decide the order. A behavior-preserving refactor or rename usually lands first, then the behavior change.
3. Separate the diff parts. Stage and commit one concern at a time by explicit path or selected diff part, so each commit builds and tests on its own.
4. When concerns should be separate PRs, move the later ones to their own branch off the first.
5. Verify each split unit. It should build, pass its tests, and be revertible without touching the others.

## Output format

- Concerns: the concerns found, one line each.
- Split plan: which commits or branches, in what order, and why.
- Verification: confirmation that each unit builds and its tests pass on its own.

## Stop conditions

- Stop when each unit is one concern, builds, and passes its tests on its own.
- If the concerns are genuinely entangled and cannot be split cleanly, say so and name what couples them, rather than forcing a split that breaks a build.
- Do not split for its own sake; one coherent concern stays one change.
