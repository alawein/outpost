---
name: refactor-safely
description: Use when restructuring code for clarity without changing behavior. Names the before and after and proves the same tests pass before and after the change.
---

# refactor-safely

A refactor changes structure, not behavior. The proof is simple: the same tests pass before and after. If the touched code has no tests, add them first or stop.

## When to use it

- A function doing three things, a duplicated branch, a leaky abstraction, or a file that grew too large.
- Not when behavior should change; split that out first.
- For folding duplication or waste in code you just changed, `simplify` is the lighter tool; refactor-safely is for reshaping existing code under its tests.

## Required inputs

- The code to restructure and a clear reason it is hard to read or change now.
- The tests that cover the touched behavior, or the plan to add them first.

## Steps

1. Name the smell and the target shape. Say what is hard now and what will be clearer after.
2. Confirm coverage first. Run the tests for the touched code. If they do not cover the behavior, write characterization tests first.
3. Make the smallest change that reaches the target shape. Prefer a series of small behavior-preserving steps.
4. Verify that the same tests pass unchanged. If a test must change, stop and reconsider.
5. Keep it separate. One refactor per commit, never mixed with a behavior change.

## Output format

- Before and after: one or two sentences.
- Diff: the diff.
- Verification: confirmation that the same tests pass unchanged.

## Stop conditions

- Stop when the target shape is reached and the tests pass without edits.
- Stop if a test needs changing; that means behavior moved, which is out of scope here.
- Do not bundle an opportunistic rename three files away. It belongs in its own change.
