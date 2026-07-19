---
name: triage
description: Use when a findings list (from repo-review, code-review, or a teammate) needs ranking before action. Confirms or doubts each finding against the code, ranks severity, and routes each to fix now, defer, or reject, with a reason. The bridge between finding problems and acting on them.
---

# triage

A findings list is not a work list. `triage` turns one into the other: it re-checks each
finding against the source, ranks what survives, and routes every item to fix now, defer, or
reject. Nothing is dropped silently; a rejected finding stays in the record with its reason.

## When to use it

- After `repo-review` or `code-review` returns more findings than one sitting can fix.
- When findings arrive from a teammate or a tool and their confidence is unknown.
- Skip it for a list of one or two findings; just verify and fix them.

## Required inputs

- The findings, one per line, each with whatever evidence came with it.
- Access to the code the findings point at.
- The bar for fix now: what ships soon, what gate must stay green.

## Steps

1. Verify before ranking. For each finding, check the claim against the code it names. Tag
   it confirmed (reproduced or re-read and true), doubtful (could not confirm; say what
   would), or wrong (the code does not do what the finding says).
2. Rank the confirmed by severity: blocker (breaks the gate, corrupts data, misleads a
   user), major (wrong behavior with a workaround, a trap for the next editor), minor
   (cosmetic, style, a nice-to-have).
3. Route each confirmed finding against the caller's bar for fix now: the bar decides what
   is worth fixing now, severity decides the order. Blockers always meet the bar. Defer
   (majors and minors worth recording; mark each for the debt log with its reason and
   revisit trigger, to be recorded through `debt-log`), and reject only with a reason a
   reviewer would accept.
4. Wrong findings are answered, not deleted: one line each on why the code is right, so the
   finding does not come back.
5. End with the work list: fix-now items in order, each with its evidence.

## Output format

- Counts first: confirmed, doubtful, wrong, the severity breakdown of the confirmed, and of
  the confirmed: fix now, defer, reject.
- The work list: fix-now items in severity order, one line each with evidence.
- The record: deferred items (each marked for `debt-log` with its reason and trigger),
  rejected items (with reasons), wrong findings (with the one-line answer).

## Stop conditions

- Every input finding appears in exactly one bucket; none dropped silently.
- No finding is confirmed on assertion alone; each was re-checked against the source.
- Deferred items are marked for the debt log with their reason and trigger; recording them is `debt-log`'s job, not this prompt's.
