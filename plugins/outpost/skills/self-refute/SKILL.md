---
name: self-refute
description: Use right after you produce an answer, plan, or design that matters, to attack your own output before presenting it. A reflexive red-team that hardens the result instead of defending it.
---

# self-refute

Use this right after you produce an answer, plan, or design that matters. Try to break your own
output before anyone else has to. `grill` attacks something handed to you. `self-refute` attacks
the thing you just made.

## When to use it

- Right after producing an answer, plan, or design that matters, before you present it.
- When a confident result has had no independent check.
- Skip it for a trivial or easily reversible answer.

## Required inputs

- Your own fresh draft: the answer, plan, or design you are about to present.
- The context it was made for, so an objection can be judged against the real goal.

## Steps

1. State your own key assumptions, the three to five claims the answer rests on. If you cannot name them, the answer is not ready.
2. Attack each one. Write the strongest concrete objection: a missed case, a broken constraint, a simpler answer, or a place it could be wrong.
3. Rate each objection `LANDS`, `GLANCES`, or `MISSES`, and say why.
4. Revise what `LANDS`. For anything you cannot fix, state the residual risk in one line.

## Output format

- Attacked: the assumptions you tested, one line each.
- Result: per assumption, `LANDS`, `GLANCES`, or `MISSES`, with the reason.
- Changes: what you revised, and any residual risk stated plainly.
- Revised answer: the final version.

## Stop conditions

- Do not defend the draft. The point is a hardened answer, not a won argument.
- A pass with no revisions must say why it held.
- Stop once every landed objection is fixed or flagged.
