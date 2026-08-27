---
name: debt-log
description: Use when recording a deliberate shortcut or a known limitation so it is tracked, not silently accrued. Writes one entry with the reason, the cost, and the trigger to revisit.
---

# debt-log

A debt entry names what was deferred, why it was deferred, and what would trigger paying it back.
The goal is to keep a shortcut visible. Distinct from
`record-decision`, which captures an architecture decision, and `write-doc`, which produces a
full deliverable.

## When to use it

- A shortcut, workaround, or known limitation was taken and the reason should stay visible.
- A requirement was deferred and a future event should trigger revisiting it.
- Skip it for a fully explored trade-off that belongs in `record-decision`.

## Required inputs

- What was deferred or worked around, in one sentence.
- Why: the constraint, the deadline, or the reason the shortcut was acceptable now.
- The cost: the risk, the fragility, or the burden this adds to future work.
- The revisit trigger: the event, milestone, or condition that would prompt addressing it.

## Steps

1. Name the shortcut in one sentence: what was done instead of the better path.
2. State the reason: the constraint or context that made the shortcut the right call.
3. State the cost: the risk or burden it carries for future work.
4. Name the revisit trigger: the event or condition that would make paying it back worth doing.
5. Append the entry to the repo's debt log, wherever the repo keeps it (a root `DEBT.md`, or a path the repo names such as `docs/DEBT.md`). If none exists yet, create one at the conventional path or ask where it should live. Do not edit existing entries; add new ones.

## Output format

- What: one sentence naming the shortcut or limitation.
- Why: the reason it was taken, in one or two sentences.
- Cost: the risk or burden it carries.
- Trigger: the event or condition that would prompt addressing it.

## Stop conditions

- Do not fix the debt. This prompt records it, not resolves it.
- Do not edit an existing entry. Append a new one.
- Stop when the entry names what was deferred, why, the cost, and the trigger clearly enough that a reader months from now can decide whether to act on it.
