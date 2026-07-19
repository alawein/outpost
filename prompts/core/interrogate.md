---
name: interrogate
description: Use when a request is vague and you are about to build. Show the hidden assumptions and the success test with sharp questions before any code, so the change is not scoped wrong from the start.
---

# interrogate

Use this before building when the request is still fuzzy. It finds the ambiguity that would show up
later and clears it early. It does not design the solution. It makes the requirement clear enough
for `plan-change`.

## When to use it

- A request that is underspecified, where two reasonable builders would do different things.
- Before plan-change, when the goal or the success test is unclear.
- Skip it when the requirement already fits in three sentences and the unknowns are reversible.

## Required inputs

- The request, in the user's words.
- Read access to the repo, so a question can be checked against the code before it is asked.

## Steps

1. Read the request for forks, the points where two builders would diverge. Each fork becomes a question.
2. Ask the most decisive question first, one at a time. Prefer multiple choice. Skip anything you can safely default and change later.
3. Name the hidden assumptions: scale, consumer, failure behavior, success test, and non-goals. Confirm or correct each.
4. Stop early. When the requirement fits in three sentences and every remaining unknown is reversible, say so and stop asking.

## Output format

- Requirement: what is being built, for whom, in one to three sentences.
- Success test: the observation or check that proves it works.
- Non-goals: what is out of scope.
- Open decisions: any question still unanswered, with the safe default you will use if it stays open.

## Stop conditions

- Stop asking at whichever comes first: the requirement fits in three sentences with only reversible unknowns left, or four questions are spent, in which case state your assumptions and proceed.
- Do not start building inside this prompt. Hand the hardened requirement to plan-change.
