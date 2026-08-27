---
name: implement-change
description: Use when executing an approved plan. Makes the smallest correct edits in order, follows the repo's existing patterns, and keeps the tree runnable at each step.
---

# implement-change

This turns a plan into small, focused edits. Keep the code working as you go so a mistake shows up
at the step that caused it.

## When to use it

- After plan-change, or when the change is small enough to plan in your head.
- For any edit where you want the result verified, not only written.

## Required inputs

- The plan, or a clear one-sentence goal for a small change.
- Read and write access to the repo.

## Steps

Before an edit that changes behavior: write or update the test first so it fails, then make the edit below pass it.

1. Make the smallest edit that completes one step. Match the surrounding code in naming, style, and structure.
2. Do not add a dependency, an abstraction, or a config knob unless the step needs it. Call out added complexity when it is justified.
3. Stay within the repo's version floors and keep output portable. Respect its stated language and dependency versions. Produce identical output on every operating system (line endings, path separators). An API newer than the floor, or a platform-dependent write, is a defect even when your machine passes.
4. Run the relevant check after each step, such as the test, build, or lint. Keep the tree runnable.
5. If a step grows larger than expected, stop and re-plan.

## Output format

- Step notes: what changed and the file.
- Diff: the diff, or the files written.
- Check result: the check you ran after each step and its result.

## Stop conditions

- Stop when every planned step is done and its check passes.
- Stop and re-plan if the change grows past the plan or reveals a wrong assumption.
- Do not claim done without running the verification. A diff is not a result.
