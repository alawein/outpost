---
name: check-intent
description: Use right after implementation is done and before code-review, to reconcile the diff against the plan or the stated ask. Catches a dropped plan item, an unrelated file change, or a silent switch to a different approach before either ships unnoticed.
---

# check-intent

Use this right after implementation, before `code-review`. `code-review` judges whether the diff
is good; this checks whether the diff is the one that was actually asked for. A plan drifts
during a long implementation session more often than it is deliberately changed.

## When to use it

- Right after implementation is done, before `code-review` or `prepare-pr`.
- When a written plan, an issue, or an explicit ask exists to check the diff against.
- Skip it when there was no separate plan step: the ask and the diff are the same small fix.

## Required inputs

- The stated plan, issue, or ask: what was supposed to change, and why.
- The diff or the branch, in full: every file it touches.

## Steps

1. List every distinct item the plan or ask called for, one line each, at the grain the plan
   itself used: a step in a written plan, a bullet in an ask, or (with no separate plan) the
   change's own stated outcome. Do not fold "and tests for it" or a downstream fixup a change of
   this kind always needs into one line with the change itself; a grain too coarse to check
   against the diff reads as Done while the real work underneath it goes unverified.
2. Walk the diff file by file. For each plan item, mark it Done, Missing, or Changed-approach (the
   diff solves it a different way than the plan named). For each file the diff touches that traces
   to no plan item, mark it Extra. A file that implements a Changed-approach item is accounted for
   by that item; it is not Extra.
3. For a Changed-approach item, check first whether the diff, its commit messages, or the PR body
   already explains the switch; if so, record that it is accounted for rather than re-litigating
   it. Otherwise state whether the new approach is still correct and complete, not just different.
4. For an Extra file, decide whether it is a legitimate side effect (a generated span, a fixture
   the change requires) or scope creep that belongs in its own change.
5. Do not fix anything here. Report the reconciliation; the caller decides whether to close a gap,
   split an Extra into its own change, or update the plan to match a deliberate Changed-approach.

## Output format

- Reconciliation table: plan item, status (Done, Missing, or Changed-approach), one line of
  evidence.
- Extras: file, and legitimate side effect or scope creep.
- Verdict: clean (every item Done, no unexplained Extra) or not, with what remains open.

## Stop conditions

- Stop before `code-review` when a Missing item or an unexplained Extra remains open.
- A Changed-approach that is still correct and complete is not a blocker; note it, do not force a
  revert to the original plan.
- Stop once every plan item has a status and every diff file is accounted for. Do not re-review
  code quality; that is `code-review`'s job.
