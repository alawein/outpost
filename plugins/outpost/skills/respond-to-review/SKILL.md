---
name: respond-to-review
description: Use when acting on review feedback on your change. Triages each comment, fixes or pushes back with a reason, and replies so the loop closes before merge. Distinct from code-review, which gives the review.
---

# respond-to-review

Use this when review comments land on your change. Sort each comment, act on it, and reply so the
loop closes. Fix what is right, push back with a reason when needed, and ask when a comment is not
clear.

## When to use it

- A reviewer (human or bot) has left comments on your change.
- Not for reviewing someone else's change; that is code-review.
- Not for ranking a raw findings list with no review loop to close; that is `triage`.

## Required inputs

- The review comments and the diff they refer to.
- The change's intent, so you can judge a comment against the goal, not only comply.

## Steps

1. Read all comments first. Group them as a blocking correctness issue, a real improvement, a question, a nit, or a point you disagree with.
2. For each comment, decide and act: fix it, ask a clarifying question, or push back with a concrete reason.
3. When you fix something, make the smallest change that addresses the comment. Add or update a test if behavior changed.
4. Draft a reply to every comment with what you changed or why you did not change it. Do not post the replies; present them.
5. Re-run the required check after the fixes. Draft the re-request note too. Note that a push after approval usually dismisses that approval.

## Output format

- Comment log: one line per comment with its verdict (`fixed`, `pushed back`, `asked`), the reason, and the drafted reply.
- Diff: the fixes.
- Check result: the required check result after the changes.
- Re-request note: the drafted note for re-requesting review, for the human to post.

## Stop conditions

- Stop when every comment has a drafted reply and the required check passes. Present the fixes and the replies.
- Draft only. Posting the replies, re-requesting review, and resolving a comment are outbound actions the human takes, not this prompt.
- Push back honestly when the feedback is wrong. Do not comply against your judgment, and do not dismiss a real issue to save work.
