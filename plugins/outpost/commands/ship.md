---
description: "Review the work, run the pre-merge checks, and prepare the PR."
---

# /ship

Review the work and prepare the PR.

Run these steps in order. Stop if a step finds a blocker:

1. `self-refute`: attack your own diff for the gaps you would miss.
2. `code-review`: one structured review against intent and the contract, one honest verdict.
3. `prepare-pr`: draft the commit and PR body from the diff, run the pre-merge checks, and confirm they pass.

Report each step's result. These steps draft the PR; a human opens it. If any step finds a blocker, stop and report it instead of proceeding.
