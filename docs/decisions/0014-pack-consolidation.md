# 0014: Pack consolidation after the Phase 1 audit

Status: Accepted (owner ruling 2026-07-11)
Date: 2026-07-11

## Context

The Phase 1 audit (`docs/audit-2026-07-10.md`) scored every prompt for a distinct job, sibling
overlap, routing clarity, and binding, and proposed consolidation rulings. The owner accepted
seven. This record carries each ruling, the rejected merges, and the falsifier that would reopen
each call.

## The rulings

1. Keep `simplify` and `refactor-safely`; sharpen the handoff. The proposed merge is rejected:
   they have different callers (fresh diff vs planned reshape) and different artifacts (applied
   cleanups vs a proven-equal restructure). The handoff threshold is now testable: a cleanup
   whose reshape would change a test, alter a public contract, or grow past the diff under
   review routes to `refactor-safely`. Falsifier: two recorded sessions where the prompts share
   callers, inputs, safety boundaries, and outputs; that evidence reopens the merge.

2. Keep `self-refute` and `grill` as shipped, no prompt edit. The proposed merge is rejected:
   the boundary is the mutate vs read-only split, `self-refute` is the author attacking fresh
   output before presenting it, `grill` is a hostile pass over an artifact it does not own.
   Falsifier: a recorded owner-plus-mode trial where ownership changes nothing about behavior;
   that evidence reopens the merge.

3. Fold `deassume` into `repo-review` and retire it. The lens carries deassume's unique parts
   (the personal-trace grep, the allowed-homes input, the generated-surface pass) as an opt-in
   ownership lens with its own trigger. The dogfooding ledger stays append-only; no row was
   edited. Falsifier: a recurring caller who needs the ownership audit without the health audit;
   that demand justifies a standalone prompt again.

4. Rewrite `prove` (audit F16). An unsure refutation attempt routes to UNKNOWN and names the
   deciding measurement; REFUTED requires a concrete break (a recomputation that disagrees, a
   contradicting source, a failing check). Parallel agents drop from precondition to optional
   strengthener; the sequential default keeps the two-independent-refutation bar, and sequential
   attempts count when their methods differ. Falsifier: a run where the sequential path passes a
   claim that a parallel run refutes.

5. Keep `panel`'s contract (conflicts are the finding; one recommendation naming the accepted
   trade-off and the overridden view); demote parallelism to a Claude-hosted strengthener. The
   sequential fallback writes each view before reading the others back and names its mode,
   because sequential independence is an intent, not a proof. Falsifier: a recorded trial where
   sequential views anchor enough to flip the recommendation.

6. Fix `converge`'s definition and make it Claude-only (audit F15). Clean is zero blockers and
   zero majors; confirmed minors are reported, not required. The mechanism is a per-prompt
   `hosts` field in the catalog, honored by the shared prompt loader and the install manifest,
   so the manual hosts install 23 of 24 prompts and every parity check stays green. Falsifier:
   a manual host running the loop end to end; that reopens cross-tool shipping.

7. Narrow `write-doc`. The template becomes a required input (its check step can then always
   execute), scope narrows to the body's own examples (README, findings note, report), the
   "or other" catch-all goes, and boundary lines route decisions to `record-decision`,
   shortcuts to `debt-log`, PR text to `prepare-pr`, and session state to `handoff-session`.
   Falsifier: a recurring deliverable outside those three types with a tested template; that
   widens the list by a new record.

## Consequences

The pack is 24 prompts, one of them host-limited. The two rejected merges stay in this record so
no one re-proposes them without the named evidence. Reversal of any ruling is a new record, not
an edit to this one.
