---
name: plan-change
description: Use before writing code for any non-trivial change. Turns a request into a short, concrete plan grounded in the actual repo, so the edit is scoped before a line is touched.
---

# plan-change

Most wasted work comes from editing before understanding. Use this before a non-trivial change.
It turns a request into a short plan tied to the real code: what changes, where, in what order,
and how you will verify it.

## When to use it

- A feature, refactor, or fix that spans more than one file or is not obvious.
- A request that is ambiguous, where naming the plan surfaces the missing decision.
- Skip it for a one-line, reversible edit.

## Required inputs

- The request, in the user's words.
- Read access to the repo. Find the files the change touches before planning, do not guess them.

## Steps

1. Restate the goal in one or two sentences. If you cannot, ask one clarifying question.
2. Read the code the change touches. Note the files, functions, and existing patterns to follow.
3. Check the change against the repo's own rules: its checks, CI, contributing guide, and stated conventions. A change that would fail the project's checks or break its rules needs a different plan, or an explicit decision to change the rule first.
4. List the steps in order. Each step should be one coherent edit with a clear boundary.
5. Name how each step is verified: the test, the command, or the observation that proves it.
6. Name the risks and the smallest reversible first step.

## Output format

- Goal: one or two sentences.
- Files: the paths the change touches, with a word on each.
- Steps: an ordered list, each step verifiable on its own.
- Verification: the command or test that proves the whole change.
- Risks: what could break and the rollback.

## Stop conditions

- Stop and ask if the goal needs a decision you cannot make safely.
- Stop when the plan fits in a glance and every step is verifiable. Do not pad it.
- Do not start editing inside this prompt. Planning and editing are separate steps.
