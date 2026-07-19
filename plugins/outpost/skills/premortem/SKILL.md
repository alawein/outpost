---
name: premortem
description: Use before committing to a plan that is expensive to reverse. Assume it already failed, work backward to the likely causes, and turn the top ones into preventive actions to take now.
---

# premortem

Use this before a plan, launch, or migration that is hard to undo. Assume it already failed, then
work backward to causes you can still prevent. `grill` and `self-refute` attack something that
already exists. `premortem` looks ahead.

## When to use it

- Before committing to a plan, launch, or migration that is hard to reverse.
- When the cost of a wrong assumption is high enough to pay for prevention now.
- Skip it for a small, reversible change.

## Required inputs

- The plan, in enough detail to name its assumptions and dependencies.
- The stakes and the rough timeline, so failures can be ranked by likelihood and impact.

## Steps

1. Set the scene. State the plan in one line and a date by which it has failed: "it is four weeks out and this migration has gone badly."
2. List the causes. Name how it failed: the broken assumption, the slipped dependency, the production edge case, or the team that was not looped in.
3. Rank by likelihood times impact. Use that ranking to decide what to prevent first.
4. Turn the top causes into actions. For each high-rank cause, name the cheapest preventive step or the early warning signal that would catch it.

## Output format

- Failure modes: a small table of cause, likelihood, impact, and prevention.
- Actions: the two or three preventive steps worth taking now, before committing.

## Stop conditions

- A premortem that ends with fears and no actions is incomplete. Name the actions.
- This is read-only. It names risk and prevention; it does not change the plan on its own.
- Stop once the top causes each have a prevention or a watch signal.
