---
name: code-review
description: Use on a diff or a branch before a PR. A structured correctness-and-standards review that catches the expensive-to-fix issues and gives one honest verdict.
---

# code-review

Use this on a diff or branch before a PR. Focus on the issues that are expensive to fix later:
design, contracts, data model, and intent. Let the linter and CI cover the cheap checks.

## When to use it

- On a diff or a branch before opening a PR, yours or a teammate's.
- Not for a whole repo with no change, and not to attack one file.

## Required inputs

- The diff or the branch, and the change's stated intent (the description, the plan, the linked decision).
- Read access to the surrounding code the diff touches.

## Steps

1. Read the intent first. Know what the change is for before reading the diff. If no intent is stated, infer it from the diff and say so at the top of the review, or ask; never review against an unstated intent silently.
2. Separate what tools cover. Note what the linter and CI already check and do not repeat it.
3. Review what tools cannot: whether the change matches its intent and the contract it touches. Watch data boundaries, public interfaces, migrations, and error paths.
4. Check portability and self-consistency: output deterministic across operating systems and within the repo's version floors, and not in conflict with the repo's own checks, CI, or stated rules. A change that fights the project's own checks is a finding, not a detail.
5. Check the tests. A behavior change should ship with coverage, and a bugfix should ship with a regression test that would fail before it.
6. Read any new prose, such as docs, comments, or the PR body. Flag wordiness and restatement.

## Output format

- Verdict: `approve`, `comment`, or `request changes`, with one line of why.
- Findings: ordered, the blocking ones first, each tied to a file and line.
- Notes: non-blocking nits, marked as such.
- Read-only: it produces the review, it does not apply fixes.

## Stop conditions

- Request changes only for a must-fix. Approve only when you would stand behind the merge.
- One concern per PR. If the diff does three separable things, say so.
- Stop when the verdict is stated and supported. Do not pad the review to look thorough.
