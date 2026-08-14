---
name: risk-review
description: Use before merging a change to install.py, kit/installers/, or kit/adapters/ write paths, or anything the author names as hard to reverse. Gates the verdict on actually attacking the claims the risky part depends on, not just reading them. Distinct from code-review, which does not require that.
---

# risk-review

`code-review` is Outpost's fast pass: one read, one verdict, the cheap checks left to the linter
and CI. Some changes deserve more than a read. `risk-review` runs `code-review` first, then
requires the claims the risky part depends on to actually be attacked, the way `grill` attacks a
design, before it will approve.

## When to use it

- A change to `install.py`, `kit/installers/`, or a `kit/adapters/` write path: the code that
  decides what gets written, kept, or deleted on a user's project.
- Any other change the author names as hard to reverse.
- Skip it for an ordinary change; `code-review` alone is the right weight there.

## Required inputs

- The diff or branch, same as `code-review`.
- The specific risk: which files or behavior make this change worth the heavier pass, named
  explicitly, not inferred.

## Steps

1. Run `code-review`'s own pass first: intent, contracts, data boundaries, portability, tests,
   prose. Do not skip or shorten it.
2. From the risky part only, name the specific claims this change depends on: what has to be true
   for it not to delete, corrupt, or silently drop something it should not.
3. Attack each claim with `grill`'s method: the strongest concrete counter-case, an input,
   sequence, or missing precondition that breaks it. Mark each `SURVIVED` or `BROKEN`.
4. A `BROKEN` claim is a finding, not a note. Rank it with `code-review`'s own severity.

## Output format

- Verdict: `approve`, `comment`, or `request changes`, same shape as `code-review`.
- Claims: the risky part's claim list, each marked `SURVIVED` or `BROKEN` with its counter-case.
- Findings: `code-review`'s usual findings, plus any `BROKEN` claim, blocking ones first.

## Stop conditions

- Do not approve while a claim tied to the named risk has not been attacked. A claim left
  unattacked is an incomplete verdict, not a weaker one.
- Read-only, same as `code-review` and `grill`. It produces the review; it does not apply fixes.
- Stop once every named-risk claim has a mark and the verdict is stated. Do not widen the attack
  to parts of the diff outside the named risk; that is plain `code-review`'s job.
