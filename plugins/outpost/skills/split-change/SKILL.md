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
3. Separate the diff parts. For each concern, name the exact paths (or diff hunks) that belong to it, so each unit builds and tests on its own. Drafting only: staging and committing are the human's to run, not this prompt's.
4. When concerns should be separate PRs, say which land together and which move to their own branch off the first.
5. For each unit, give the check that confirms it stands alone: the test command to run once it is isolated, so the human can see it builds and passes without the others.

## Output format

- Concerns: the concerns found, one line each.
- Split plan: which commits or branches, in what order, and why.
- Verification: confirmation that each unit builds and its tests pass on its own.

## Stop conditions

- Stop when the plan names each unit's concern, its paths, the order, and how to verify it stands alone.
- Draft only. Do not stage or commit; separating the diff into commits is the human's action, taken on the plan this prompt hands over.
- If the concerns are genuinely entangled and cannot be split cleanly, say so and name what couples them, rather than forcing a split that breaks a build.
- Do not split for its own sake; one coherent concern stays one change.
