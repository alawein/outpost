# 0023: Admit check-intent

Status: Accepted
Date: 2026-08-07

## Context

`code-review` reviews correctness and standards, and its step 1 reads the stated intent so it
does not review against an unstated one silently. But intent is one check folded into a broader
pass covering design, contracts, portability, tests, and prose; nothing produces a structured,
item-by-item reconciliation of a plan against the diff that actually shipped. A long
implementation session drifts more often than it is deliberately redirected: a plan item gets
quietly dropped, an unrelated file gets touched along the way, or the approach silently changes
from what was decided. Nothing in the pack catches this before `code-review` or `prepare-pr` run,
both of which take the diff as a given rather than checking it against the plan that produced it.

The ACK capability comparison (`.superpowers/outpost-refinement/ack-capability-matrix.md`) named
this as ACK's `check-intent` prompt. That comparison used only an abstract one-line description,
never ACK's actual prompt text. The Outpost prompt below was drafted independently from that
abstract description and from Outpost's own contract style; a follow-up read-only comparison
against ACK's real file (after the draft existed) found the two diverge on philosophy (ACK is
explicitly non-blocking and defers to a documented deviation; the Outpost draft blocks on an
unexplained gap and now, after that comparison, also defers to an already-documented deviation,
adopted as a general practice, not copied wording) and output shape (a status table here, a
verdict-plus-findings there). Verdict: CLEAN-ROOM.

## Decision

Admit `check-intent` to the Review and ship stage, positioned right before `code-review`.

- Distinct job: reconcile a diff against the plan or ask that produced it, item by item, marking
  each Done, Missing, Changed-approach, or (for an untraceable file) Extra.
- Nearest sibling: `code-review`, whose step 1 checks intent as one of six dimensions in a
  broader correctness pass. `check-intent` does only the plan-to-diff reconciliation, as a
  structured table, not folded into a wider review.
- Unsafe default: an agent finishes implementing, the code looks right and tests pass, and it
  goes straight to `code-review` or `prepare-pr`. `code-review`'s intent check is soft ("infer it
  ... say so"), not a hard enumeration against the original plan, so a dropped plan item or a
  stray unrelated edit ships unnoticed.
- Binding mechanism: the stop conditions block continuing to `code-review` while a Missing item
  or an unexplained Extra file remains open; a Changed-approach that is still correct, or already
  explained in the diff or its commit messages, is not a blocker.
- Dogfood case: the 2026-08-07 run recorded in `docs/dogfooding.md`, applying the prompt's own
  steps to this admitting change's diff.
- Deletion condition: remove this prompt if two recorded sessions show `code-review`'s existing
  intent check alone catches every drift case `check-intent`'s structured table would have
  caught, so the dedicated pass adds no finding a folded-in check would have missed.

## Alternatives

- Fold a stricter intent check into `code-review` itself instead of a new prompt. Rejected:
  `code-review` already covers six dimensions in one pass; adding a seventh, structured one
  changes its job from "is this diff good" to "is this diff good and the one that was asked for,"
  which is the same overload ADR-0013 exists to prevent.
- Copy ACK's `check-intent` prompt directly. Rejected: ACK is a private, proprietary repository;
  its LICENSE forbids outside copying, modification, or distribution without written permission.
  Only the abstract capability (a pre-code-review intent reconciliation exists and is useful) was
  reused; the contract here was drafted independently and verified CLEAN-ROOM against the real
  file only after the draft existed.
- Do nothing; treat the gap as acceptable. Rejected: the unsafe default (a silently dropped plan
  item or an unrelated file shipping unnoticed) is real and the evidence a structured
  reconciliation catches it that a folded-in check does not, per the dogfood run.

## Consequences

A plan and its shipped diff get one honest reconciliation before review starts, catching drift
`code-review`'s folded-in intent check does not reliably surface. Admission adds one more prompt
and its generated plugin copy to maintain (26 prompts total). The deletion condition ties that
cost to evidence from later sessions, not a one-time argument.
