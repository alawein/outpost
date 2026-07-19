---
description: "Clean up the changed code: fold duplication, cut waste, behavior preserved."
---

# /simplify

Clean up the current change without changing what it does.

Run `simplify` over the working diff (or the named files). Tests green first, then hunt
duplication, missed reuse, needless indirection, and waste. Apply the small cleanups one at
a time with tests green after each; hand anything larger to `refactor-safely` as a named
follow-up. Report what changed, what was rejected and why, and what was deferred.
