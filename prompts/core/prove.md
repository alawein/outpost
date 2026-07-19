---
name: prove
description: Use when numbers go to stakeholders, a finding is contested, or a claim must survive scrutiny. Proves or refutes many claims by recomputing each from the source of truth and attacking the survivors, then tags every claim with a confidence verdict. The heavier sibling of grill.
---

# prove

`grill` stress-tests one item. `prove` checks many claims by recomputing each from the
source of truth and running adversarial refutation against the survivors, then tags every
claim with a confidence verdict. Use it when being wrong in public is expensive.

## When to use it

- Numbers are going to stakeholders.
- A finding is contested or a strategy rests on a few key measurements.
- A claim must survive independent scrutiny before you assert it flatly.
- Skip it for a small exploratory finding where the cost of being wrong is low.

## Required inputs

- The claims to check, one per line or bullet.
- The source of truth for each claim: the file, field, or dataset the number should come from.
- The cheapest falsifier for each claim: the test that would break it first.

## Steps

1. Frame falsifiable hypotheses. Rewrite each claim as something that could be shown false, and
   name the cheapest test that would break it.
2. Recompute each hypothesis from the source of truth itself, not from a prior summary or doc.
   Record the value, the method, the file and field, and whether the result matches the claim. A
   claim with no named source of truth cannot be recomputed: route it to UNKNOWN and name the
   source that would let it be checked, rather than confirming it.
3. Refute the survivors, cheapest falsifier first: cherry-picking, circular definition,
   selection bias, wrong baseline, arithmetic slip, hidden dependency. A refutation attempt
   ends one of three ways: it breaks the claim (a recomputation that disagrees, a contradicting
   source, or a failing check), the claim holds and the attempt says why, or it cannot decide,
   which routes the claim to UNKNOWN with the measurement that would decide it named. Unsure is
   never REFUTED.
4. Repeat the attack with a different method. CONFIRMED needs at least two independent
   refutation attempts; sequential attempts count as independent when they use different
   methods (a different lens, source, or computation, not the same check twice). Load-bearing
   claims get three attempts with distinct lenses.
5. Judge with the rubric. A claim is CONFIRMED only if it was recomputed and survived the
   refutation attempts. The most useful output is often the QUALIFIED set: true, but only under
   a condition an attempt surfaced. Ship the condition with the claim.
6. Synthesize one map: confirmed, qualified, refuted, unknown. Keep the refuted ones with their
   reasons so no one re-proposes them.

On a host that can run subagents, strengthen independence by fanning out: one agent per
hypothesis to recompute, one or more skeptics per surviving finding to refute. The fan-out is
optional; the sequential single-agent path above reaches every verdict on its own.

## Output format

- Claims: the falsifiable hypothesis for each input, one line each.
- Verdicts: per claim, CONFIRMED / QUALIFIED / REFUTED / UNKNOWN, with the condition or reason.
- Map: one section each for confirmed (assert flatly), qualified (assert with the condition),
  refuted (kept with the reason), unknown (the measurement that would decide it).

## Stop conditions

- CONFIRMED: recomputed from the source, cheapest falsifier failed, survived at least two
  independent refutation attempts (parallel or sequential with different methods). Assert it
  flatly.
- QUALIFIED: true only under a stated condition. Assert it with the condition, never without.
- REFUTED: broken by a concrete break only, a recomputation that disagrees, a contradicting
  source, or a failing check. Stays in the record with the reason so no one re-proposes it.
- UNKNOWN: the data cannot decide, or an attempt ended unsure. Name the one measurement that
  would decide it.
- Never upgrade a verdict to clear the room, and never downgrade unsure to REFUTED. If nothing
  refutes, say why the claim held.
