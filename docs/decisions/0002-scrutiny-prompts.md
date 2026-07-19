# 0002: Scrutiny prompts, a third prompt group

Status: Accepted
Date: 2026-06-28

## Context

The kit ships eight main-flow prompts and three supporting prompts. Two gaps remain in the change loop. Nothing clarifies a vague request before plan-change. review-change checks correctness only, so a design or diff gets no adversarial pass before it is trusted. The earlier internal kit (`agi-claude-kit`) has prompts that fill both gaps. ADR-0001 dropped that kit's eval, judge, guide, and governance tools to keep this core small, so any port must avoid pulling that back in.

## Decision

Add a third prompt group, "scrutiny", with four prompts ported from the earlier kit and rewritten tool-neutral in this kit's prompt anatomy:

- interrogate: clarify a vague request before building.
- grill: hostile stress-test of a design, plan, or diff.
- self-refute: red-team your own fresh output before presenting it.
- premortem: assume a plan failed and turn the likely causes into actions.

Each passes one test: does it serve the coding-change loop without pulling in any dropped tools (no eval, judge, guide, data, or MCP dependence)? All four pass it. They are read-only reasoning prompts with no external tool or data dependency. The catalog grows from eleven prompts to fifteen.

## Alternatives

- Port the whole earlier kit's skill set. Rejected: most of it is the eval, judge, guide, and governance tools ADR-0001 dropped, or duplicates prompts the kit already has, or depends on an MCP integration the stdlib-only kit will not carry.
- Add only interrogate and leave review-change as the sole review prompt. Rejected: review-change confirms correctness; it does not attack. The adversarial gap matters more.
- Keep these as personal habits, not shipped prompts. Rejected: the kit should ship the workflow and load it on its own, the same across tools.

## Consequences

- The prompts stay stdlib-pure and tool-neutral, so they auto-ship to every adapter with no installer change.
- The scrutiny group is the recorded home for this class of prompt. Widening it again is a new decision.
- The other earlier-kit skills, eval, integration, and duplicates, stay out under ADR-0001. This reverses only if a future need genuinely requires one, recorded as a new ADR.
