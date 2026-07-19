# 0008: Eval front door, a quarantined leaf that reverses ADR-0001's eval scope

Status: Accepted
Date: 2026-07-03

## Context

ADR-0001 dropped eval tools and the judge engine from the rebuilt kit: "No eval, no judge,"
reversible only by a new decision recorded here. The kit now ships an eval front door,
`kit.eval`, with four verbs: score, replay, judge, guides-score. That reversal needs a record.

## Decision

`kit.eval` is a quarantined leaf, not a core dependency. It imports the touchstone engine
lazily, only inside functions, and only from `kit/eval/engine.py`; the core package and the
installer stay stdlib-only, enforced by the `eval_isolation` check. The judge panel binds to
the engine's own model list: `ScoringAPI.default_panel` carries the engine's `DEFAULT_PANEL`
rather than the kit defining its own. Kit-side validation uses `ValueError` as its channel; the
taxonomy split that would separate a bad flag from an engine failure is tracked as open debt in
`docs/DEBT.md`, not solved by this decision.

## Alternatives

- Keep the ADR-0001 scope and leave eval entirely out of the kit. Rejected: the eval front door
  already shipped (PRs #77-#82) and is in active use; the record should describe reality.
- Vendor or hard-depend on touchstone in core. Rejected: it would break the stdlib-only
  guarantee the installer and core package promise, and tie the kit's release cadence to a
  private sibling repo.

## Consequences

Core stays portable: a clone with only touchstone missing still installs and validates clean,
`kit.eval` just cannot run. Eval capability follows the engine contract, not a copy of it, so
the judge panel and scoring logic move with touchstone rather than drifting. The leaf can be
dropped without touching core if the eval front door is ever removed. The `ValueError`-only
error channel stays a known gap until the debt entry closes.
