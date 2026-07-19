---
name: debug-failure
description: Use when a test fails or an error is unclear. A hypothesis-first loop that reproduces the failure, finds the root cause, fixes it, and pins it with a regression test.
---

# debug-failure

Do not fix a bug by instinct. Reproduce it, narrow it, test the likely causes, fix the root cause, and lock it in with a regression test. The cause stays unknown until you can show where and why it fails.

## When to use it

- A failing test, a stack trace, or behavior that does not match expectation.
- Not for adding new coverage to working code; that is write-tests.

## Required inputs

- The failing command or the error, and the ability to run it.
- Read and write access to the code and its tests.

## Steps

1. Reproduce it every time. Find the exact failing command and the smallest input that still fails.
2. Read the real error. Use the full trace, the values, and the failing line. Run it and read the output.
3. Make testable guesses. Rank the likely causes and name the one observation that separates them.
4. Trace the failure. Narrow the area, add a temporary probe, or shrink the input until you isolate the failing line. Remove the probe after.
5. Fix the root cause. Do not hide the symptom and call it done.
6. Lock it in. Add a regression test that fails before the fix and passes after. Then run the required check and confirm it passes.

## Output format

- Root cause: one or two sentences.
- Fix: the diff.
- Regression test: the test, plus confirmation it fails before and passes after.

## Stop conditions

- Stop when the required check passes and the regression test holds.
- If the cause stays unknown after the loop, say so and name the next observation that would decide it.
- Do not claim a fix you did not verify by running it.
