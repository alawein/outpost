---
description: "Rank a findings list: confirm, rate severity, route to fix, defer, or reject."
---

# /triage

Turn a findings list into a work list.

Run `triage` over the findings given (or the most recent review output in this session).
Verify each finding against the code before ranking it, then route every item: fix now,
defer to the debt log, or reject with a reason. Counts first, then the fix-now list in
severity order. Nothing dropped silently.
