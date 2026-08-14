---
name: cross-doc-check
description: Use when two docs are each supposed to state the same policy or rule, to check whether they actually agree. Flags a real contradiction or an unexplained scope gap, never a wording difference where the substance already agrees. Distinct from doc_truth, which checks that a named reference resolves, not whether two docs agree with each other.
---

# cross-doc-check

`doc_truth` checks that a prompt or tool named in prose still exists. Nothing checks whether two
docs that are each supposed to state the same rule actually agree. This repo has already shipped
that exact bug once: a cited number in one doc quietly disagreed with the same number stated
elsewhere, caught by luck during a wider review pass, not by anything built to find it.

## When to use it

- Given two or more docs that are each supposed to state the same or overlapping policy, before
  trusting they agree.
- Right after editing one of a pair of docs that share a rule, before the edit ships.
- Skip it when the docs cover different, non-overlapping topics; there is nothing to reconcile.

## Required inputs

- The specific docs to compare, named by the caller. This prompt does not guess which docs are
  supposed to agree.

## Steps

1. Read every named doc in full.
2. From each, extract the concrete, checkable rules it states: a number, a required or optional
   call, a threshold, a named exception. Set aside scene-setting prose that states no rule.
3. Compare the extracted rules across docs. Report only two kinds of finding: a
   direct contradiction, where both docs cover the same case and require a different
   action, or an unexplained scope gap, where one doc's rule has no counterpart in the
   other and neither doc says why. A rule stated in different words, with the same
   substance, is not a finding.
4. For each finding, name the exact location in each doc and the conflicting values or rules.

## Output format

- Findings: one line each, the two locations and what conflicts. Empty if none.
- Verdict: agree (no findings) or disagree, with the count.
- Read-only: it reports the mismatch; it does not edit either doc.

## Stop conditions

- Every rule extracted from every named doc has been checked against every other named doc.
- A wording difference alone, with the same substance, is never reported as a finding.
- Stop once every extracted rule is accounted for. Do not judge whether a rule is itself a good
  one; that is out of scope.
