---
name: handoff-session
description: Use when wrapping a work session or passing work to another agent, or to re-ground a drifting long task mid-flight. Produces a short handoff so the next session resumes with no context loss.
---

# handoff-session

This writes a short handoff for the next session or the next person. Say what is done, what is left,
and what was decided, in that order. The goal is a clean restart.

## When to use it

- Wrapping up a session, before a context reset, or passing work to another agent.
- Mid-task, when a long-running task needs re-grounding because context has drifted (absorbs the `checkpoint` use case; the output is still a single handoff, not a separate file).
- Not for a finished, merged change that needs no follow-up.

## Required inputs

- The work done this session and its current state (branch, what runs, what is red).
- The open decisions and the next concrete step.

## Steps

1. State the goal and its current state in one or two sentences.
2. List what is done, with evidence such as the branch, passing tests, and merged or open PR.
3. List what is left as concrete next steps. Put the first ready step first.
4. Record the decisions made and the decisions still open.
5. Name the risks: anything red, fragile, or surprising, plus the relevant files.

## Output format

- Status: goal and one-line state.
- Done: bullets with evidence.
- Next: ordered steps, the first one actionable.
- Decisions: settled and open.
- Watch out for: risks and file pointers.

## Stop conditions

- Stop when a fresh reader could resume from the handoff alone.
- Keep it to state and pointers. Do not restate the whole diff.
- Do not claim a step is done without the evidence that proves it.
