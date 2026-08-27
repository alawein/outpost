---
name: grill
description: Use when a design, plan, or diff needs hostile scrutiny before it is trusted or shipped. It tries to break the design, plan, diff, or claim rather than confirm it, then gives one verdict. Distinct from code-review, which checks correctness.
---

# grill

`code-review` checks whether a change looks correct. `grill` tries to break a design, plan, diff,
or claim before you trust it. Use `self-refute` on your own fresh output. Use `grill` on something
you are being asked to trust.

## When to use it

- A design, plan, or diff that is about to be trusted, merged, or shipped.
- A claim that needs to hold under pressure, not only sound right.
- For a claim that must be recomputed from a source of truth, use `prove`, the heavier sibling; grill argues, prove recomputes.
- Skip it for a small, reversible change already covered by code-review.

## Required inputs

- The thing to test: the design, plan, diff, or claim.
- Any spec or docs it rests on, so claims can be checked against what was promised.

## Steps

1. List the key claims. Name the three to seven things the design, plan, diff, or claim depends on.
2. Attack each claim. Write the strongest concrete counter-case: an input, sequence, race, missing precondition, or assumption that breaks it.
3. Cross-check against the spec or docs when they exist. Flag disagreements and claims with no enforcement.
4. Rank the results. Mark each claim `SURVIVED` with the reason, or `BROKEN` with the counter-case and a severity of blocker, major, or minor.

## Output format

- Claims: the key claim list, one line each.
- Findings: per claim, `SURVIVED` or `BROKEN`, with the counter-case and severity for broken ones.
- Verdict: one line. Trustworthy as-is, trustworthy with the listed fixes, or not yet trustworthy.

## Stop conditions

- Do not soften a finding to be agreeable. If nothing breaks, say why the design, plan, diff, or claim held.
- This is read-only. Do not modify the design, plan, diff, or claim; hand fixes to refactor-safely or the build.
- Stop at the verdict. One honest line, no hedging.
