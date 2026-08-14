# 0027: Admit risk-review

Status: Accepted
Date: 2026-08-14

## Context

`code-review` reviews a diff in one fast pass, explicitly leaving the cheap checks to the linter
and CI, and nothing requires a heavier pass for the one class of change where a subtle bug is
genuinely costly: install.py and kit/installers/'s file-ownership and path logic. This repo's own
history already has two real bugs there that passed a normal read: the manifest path-traversal
issue (CHANGELOG.md v0.2.0, Security section) and the prune/remove data-loss bug (PR #25). grill
attacks a handed-off artifact's claims but produces no review verdict, so nothing currently
composes a mandatory attack step into a review gate.

Reading ack's actual review-deep.md after the draft and its dogfood run already existed shows
divergence beyond the shared, unavoidable idea that some changes deserve a heavier review:
review-deep triggers on an abstract risk taxonomy (trust boundaries, migrations, public
contracts, concurrency, and hard-to-unwind rollback) with no named file or path anywhere, while
risk-review's primary trigger is Outpost's own three named write paths, with "hard to reverse"
only as a secondary catch-all. The mechanisms diverge further: review-deep is an eight-step,
four-prompt composition (grill, prove, panel, and simplify) with a five-value uncertainty-tagging
scheme for claims, an explicit change-model step, and an alternative-design comparison, none of
which risk-review has; risk-review is a narrow, four-step composition of exactly two siblings
(code-review and grill) with a binary survived-or-broken mark, and it explicitly refuses to widen
beyond the named risk, the opposite of review-deep's broader ambition. The one real point of
contact, gating an approve verdict on the claims table being complete, is the obvious way to make
a mandatory-attack-then-verdict composition binding at all, the same category of unavoidable
convergence ADR-0023 already named for check-intent's shared mismatch taxonomy. Verdict:
CLEAN-ROOM.

## Decision

Admit `risk-review` to the Review and ship stage, positioned immediately after `code-review`.

- Distinct job: gates a diff touching install/adapter write paths, or anything named hard to
  reverse, behind a mandatory claim-attack step neither `code-review` nor `grill` requires alone.
- Nearest sibling: `code-review` (same scope, no mandatory attack) and `grill` (attacks claims,
  produces no review verdict).
- Unsafe default: a risky installer change passes `code-review` on a normal read, as it already
  has twice in this repo's own history.
- Binding mechanism: the stop condition itself, an unattacked claim tied to the named risk makes
  the verdict incomplete, not just weaker.
- Dogfood case: the 2026-08-14 run recorded in `docs/dogfooding.md`, applying the prompt's own
  steps to `install.py` and `kit/installers/*` as they stand today. It found a real, live-verified
  finding, not a placeholder: a crafted manifest `files` record naming a path through a
  project-local directory symlink clears the existing string-only path validation and lets
  `install.py --remove` delete a file outside the project root, confirmed by an actual
  reproduction, not just a read. A second, already-known gap (`unmerge_kit_settings` and a
  never-installed tool) was independently reconfirmed still open. Three other claims survived a
  real attack. Neither finding required a change to `risk-review.md` itself: its own instruction
  to attack the strongest concrete counter-case is what surfaced both.
- Deletion condition: retire this prompt if `code-review` alone proves just as thorough on
  installer changes over several real runs without the mandatory attack step.

## Alternatives

- Fold a mandatory attack step into `code-review` itself for every diff. Rejected: `code-review`
  already covers six dimensions in one fast pass by design; making every diff pay the cost of a
  claim-by-claim attack changes its job for the 95% of changes that do not need it.
- Copy ack's review-deep prompt directly. Rejected: ack is private, proprietary software; its
  LICENSE forbids copying, modification, or distribution without written permission. Only the
  abstract idea (some changes deserve a heavier review) was reused; the contract here was drafted
  independently and checked against the real file only after the draft and its dogfood run
  already existed.
- Do nothing; treat the two historical bugs as one-off mistakes already fixed. Rejected: both
  passed review once already; the unsafe default is real on its own terms, not hypothetical, and
  the 2026-08-14 dogfood run found a live third instance of the same general class in the same
  file, still open today.

## Consequences

Changes to the installer's write paths get a stricter gate than an ordinary diff, at the cost of
one more prompt to maintain. The deletion condition ties that cost to evidence from later runs,
not a one-time argument. The dogfood run's two findings (the symlink-mediated escape and the
`unmerge_kit_settings` gap) are recorded in `docs/dogfooding.md` as open installer findings, not
fixed by this admission; they need their own follow-up, scoped separately from admitting the
prompt that found them.
