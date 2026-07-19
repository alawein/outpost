---
name: prepare-pr
description: Use when a branch is ready for review. Drafts the commit, the PR title and body, the testing notes, and the risks from the diff, and runs the pre-merge checks.
---

# prepare-pr

Use this when a branch is ready for review. It drafts the commit and PR text from the diff and runs the pre-merge checks. A human still opens and merges the PR.

## When to use it

- A branch that is ready for review, with the work complete and the tests passing.
- Reaching for a staged-commit step: this drafts the explicit staged paths and commit message (absorbs the `commit` use case).
- Reaching for a PR-draft step: this drafts the PR title, changed-work bullets, testing notes, and risks (absorbs the earlier PR-draft step).
- Not mid-change; finish the work first.

## Required inputs

- The branch and its diff against the base.
- The change's intent and the repo's commit and PR conventions.

## Steps

1. Confirm the basics: the right branch, not the base, the right commit identity, explicit staged paths only, and no stray files.
2. Draft the commit. Use one imperative subject under about 70 characters, specific, with no emoji and no trailer. Add a body only when the why is not obvious.
3. Draft the PR body to match the change: Summary, What changed, Why or context, Testing, and Risks and limitations.
4. If the repo keeps a changelog, add an entry for anything user-visible; if it does not, skip this and note the skip.
5. Run the required check: lint, tests, and the repo's validate command. Record each result in the checklist.

## Output format

- Commit draft: the proposed subject and body.
- PR draft: the title and the filled body template.
- Pre-merge checklist: each item checked or flagged.

## Stop conditions

- Stop when the drafts are complete and the checks have run. Present the drafts and the results.
- Draft only. Do not commit, push, open the PR, mark it ready, or request reviewers. Those are the human's actions, taken on an explicit instruction, not this prompt's.
- If a required check fails, report the failure in the checklist rather than hiding it; still open nothing.
