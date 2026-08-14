---
description: "Start a change: plan it, implement it, and cover it with tests."
---

# /drive

Start a change with these prompts:

1. `plan-change`: scope the change against the real repo and name how each step is verified.
2. `implement-change`: make the smallest correct edits, with the tree runnable at each step.
3. `write-tests`: cover the happy path, the edges, and the failure modes against the contract.

If a test breaks, use `debug-failure`. If the code needs a structural cleanup, use
`refactor-safely`. Stop at a green test run, then hand off to `/ship`.
