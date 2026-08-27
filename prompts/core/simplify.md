---
name: simplify
description: Use when changed code works but carries duplication, needless indirection, or waste. Finds and applies reuse, simplification, and efficiency cleanups that preserve behavior. It does not hunt bugs (code-review does) and it is not a planned reshape (refactor-safely is).
---

# simplify

Working code is not finished code. `simplify` reviews the change you just made for the
cleanups a good reviewer would ask for: duplication to fold, indirection nobody needs,
work done twice, a stdlib call that replaces a hand-rolled block. It applies the small ones
and hands the large ones to `refactor-safely`.

## When to use it

- Right after a change works and its tests pass, before `code-review`.
- When review feedback says the change is correct but heavier than it needs to be.
- Skip it when the change is one line, or when no tests cover the code (write them first;
  cleanup without a net is how behavior changes by accident).

## Required inputs

- The diff or file list to clean. Default scope: the current change, not the whole repo.
- The test command that proves behavior is preserved.

## Steps

1. Run the tests first. Red means stop; simplification starts from green.
2. Hunt in this order: duplication (the same logic twice), reuse (an existing helper or
   stdlib call that replaces new code), indirection (a layer with one caller and no second
   use in sight), waste (recomputed values, needless copies, work inside a loop that can
   move out).
3. Judge each candidate: does the cleanup make the code easier to read for the next person,
   and is behavior provably unchanged? Reject cleanups that only relocate complexity.
4. Apply the accepted small cleanups one at a time, tests green after each.
5. Route the large ones. A cleanup is too large for this pass when its reshape would change
   a test, alter a public contract (a name, signature, output, or error), or grow past the
   diff under review. Each of those goes to `refactor-safely` as a named follow-up, not into
   this diff. The threshold matches refactor-safely's own stop rule (a test that must change
   means behavior moved), so the handoff is testable, not a judgment call.

## Output format

- What changed: each cleanup in one line, with the reason it reads better.
- What was rejected: each candidate kept as-is, with the reason (kept, so no one re-proposes
  it).
- What was deferred: the reshapes handed to `refactor-safely`.
- The test evidence: the command run and its result after the last cleanup.

## Stop conditions

- Tests green on the final tree, same suite as the start.
- No behavior change: no public name, signature, output, or error contract moved.
- Every rejected and deferred candidate is recorded with its reason.
