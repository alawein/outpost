# 0029: Admit cross-doc-check

Status: Accepted
Date: 2026-08-14

## Context

doc_truth checks that a named reference (a prompt or tool mentioned in prose) resolves to
something real. docs_sync checks that a generated span matches the catalog. Neither checks
whether two independently hand-written policy statements agree in substance. This repo has
already shipped that exact bug: docs/cadence.md's cited commit-subject length (50) contradicted
CLAUDE.md's and prepare-pr's shipped value (70), caught by luck during a repo-review self-review
pass (CHANGELOG.md, the Fixed entry for the doc-truth batch), not by anything built to find it.

A read-only comparison against ack's real align-instructions.md file (after this draft and its
dogfood run already existed) found real convergence and real divergence. Convergence: both
require the caller to pre-name the docs or files to compare rather than discovering pairs on
their own, both refuse to flag a same-substance wording difference, and both name their
strongest finding category the same way in substance, a same-case rule that requires a different
action, which is the obvious framing for this comparison and not a sign of copying on its own.
Divergence: ack's file explicitly excludes a rule that exists in only one file from any flag at
all, reserving its second category for two differing rules with no stated scope reason, while
this draft's second category is exactly the no-counterpart case ack's file excludes; the two
also diverge on output shape (a topic-by-topic table there, a flat findings list with a single
agree-or-disagree verdict and count here), and ack's file states explicitly that a human decides
what to do with a flagged contradiction, a framing this draft does not carry in those words.
Verdict: CLEAN-ROOM.

## Decision

Admit `cross-doc-check` to the Scrutiny stage, positioned immediately after `repo-review`.

- Distinct job: compares two named, hand-written docs for a real policy contradiction or an
  unexplained scope gap, never a wording difference; doc_truth and docs_sync both check a
  different kind of consistency (reference validity, generated-span accuracy).
- Nearest sibling: doc_truth. A considered alternative, folding this into repo-review's own
  docs-truth pass as a sixth pass, was set aside for this admission because repo-review's
  docs-truth pass compares docs against code, not docs against other docs, a different
  comparison target, and a standalone prompt can run on just two named docs without a full repo
  audit; worth revisiting if it is only ever invoked from inside repo-review in practice.
- Unsafe default: two docs stating the same numeric or policy rule silently disagree and nothing
  catches it except getting lucky during a broader audit, exactly what already happened once.
- Binding mechanism: the stop condition itself, every extracted rule from every named doc must be
  checked against every other named doc before the pass is done.
- Dogfood case: the 2026-08-14 run recorded in docs/dogfooding.md: both named pairs, CLAUDE.md
  vs docs/cadence.md and CLAUDE.md vs docs/contributing.md, returned agree with 0 findings,
  including a live re-check that the cadence.md commit-length contradiction named in Context
  stayed fixed.
- Deletion condition: retire this prompt if, over several real uses, it is only ever invoked from
  inside a repo-review run and never standalone, since that would mean the standalone case named
  above does not actually happen in practice.

## Alternatives

- Fold this into repo-review as a sixth pass instead of a standalone prompt. Considered seriously;
  set aside for now, see Nearest sibling above and the named deletion condition.
- Copy ack's align-instructions prompt directly. Rejected: ack is private, proprietary software;
  its LICENSE forbids copying, modification, or distribution without written permission. Only the
  abstract idea was reused; drafted independently, checked against the real file only after the
  draft and dogfood run already existed.

## Consequences

A pair of docs that are each supposed to state the same rule get a direct, on-demand check instead
of relying on a wider audit to catch drift by chance. One more prompt to maintain; the deletion
condition ties that cost to whether the standalone use case actually occurs.
