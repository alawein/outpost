# 0020: Admit repo-hygiene-sweep

Status: Accepted
Date: 2026-08-06

## Context

Reviewing a workspace of repositories requires more than repeating a single-repo audit. The
sweep must reconcile declared and observed topology, protect unsafe targets, preserve evidence
for every finding, and separate read-only discovery from later cleanup authority. Without one
ordered contract, an agent can treat a stale path as a missing repo, invent stack commands, or
mutate a dirty target while trying to make the fleet consistent.

## Decision

Admit `repo-hygiene-sweep` to the Scrutiny stage.

- Distinct job: orchestrate an ordered multi-repo sweep from topology and catalog through
  workflow triage to gated cleanup.
- Nearest sibling: `repo-review` judges one repo read-only, but does not reconcile a fleet or
  authorize later mutations.
- Unsafe default: the older workspace sweep invented stack commands, edited dirty or archived
  targets, and bundled staging, dependency, or external actions.
- Binding mechanism: protected-target stops, inspection of repo-defined command effects,
  evidence fields, explicit authority, and unchanged-test parity block those unsafe actions.
- Dogfood case: the 2026-08-06 local workspace run recorded in `docs/dogfooding.md` reconciled
  registry and Git topology, found moved and absent targets, and withheld mutation where the
  gates failed.
- Deletion condition: remove this prompt if two recorded fleet runs route entirely to
  `repo-review` plus `triage` and the fleet-specific gates catch no distinct issue.

## Alternatives

- Repeat `repo-review` for every target, then use `triage`. Rejected: that pair does not reconcile
  registry paths with Git identities or bind later mutations to fleet topology and target state.
- Keep the older workspace sweep as an informal procedure. Rejected: its invented commands and
  bundled actions are the unsafe default this decision must prevent.

## Consequences

Fleet review now has one ordered, read-first contract and one report format. Admission adds a
prompt and generated plugin copy to maintain. The deletion condition keeps that cost tied to
evidence from later runs.
