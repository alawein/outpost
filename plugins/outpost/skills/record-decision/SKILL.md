---
name: record-decision
description: Use when recording an architecture or structural decision. Captures the context, the decision, and the consequences as a short, append-only record so the why survives.
---

# record-decision

A decision record captures the context, the decision, and the consequences in one short entry.
The goal is for the why to survive after the code and team have moved on. Distinct from
`write-doc`, which produces a full deliverable, and `debt-log`, which marks a known shortcut.

## When to use it

- An architecture or structural decision was made and the reason needs to outlast this session.
- A design was chosen over alternatives and the trade-offs should be visible later.
- Skip it for a reversible implementation detail or a pure style call.

## Required inputs

- The decision in one clear sentence.
- The context: what forced this choice, what constraints applied, and what alternatives existed.
- The consequences: what the decision enables, constrains, or defers.

## Steps

1. Name the decision in one imperative sentence.
2. State the context: the problem, the constraints, and the date.
3. List the alternatives that were considered and the reason each was set aside.
4. Record the consequences: what changes, what is now off-limits, and what follow-up is needed.
5. Write the entry to the repo's own decisions directory as an append-only file. If no such
   directory exists, name the conventional path (for example `docs/adr/` or `docs/decisions/`)
   and create it, or ask where it should live; do not scatter the record elsewhere. Never edit a
   recorded entry; supersede it with a new one.

## Output format

- Decision: one imperative sentence.
- Context: the problem and constraints, in a short paragraph.
- Alternatives: a list, each with the reason it was not chosen.
- Consequences: what changes and what is deferred, in a short paragraph or list.

## Stop conditions

- Do not change code. This prompt records the decision, not the implementation.
- Do not edit an existing record. Write a new one that supersedes it.
- Stop when the record states the why clearly enough that a reader months from now can understand the choice without asking anyone.
