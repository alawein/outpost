# 0022: Namespaced label governance

Status: Accepted
Date: 2026-08-07

## Context

Outpost used only GitHub's default labels (`bug`, `enhancement`, `documentation`, `duplicate`,
`help wanted`, `good first issue`, `invalid`, `question`, `wontfix`). They do not distinguish
what a change touches (`area`), how urgent an issue is (`priority`), or whether a PR is
user-visible for release notes (`release`). The ACK capability comparison
(`.superpowers/outpost-refinement/ack-capability-matrix.md`) found ACK's label taxonomy has real
signal (component and workflow-state grouping) but is scaled for a team (30+ labels, including
company-specific `ledger:*` tracking) that does not fit a solo public repo.

## Decision

Add a small, namespaced label registry (`kit/labels/registry.json`, GENERAL-PRACTICE provenance,
independently sized for this repo, not copied from ACK's taxonomy): `type:*`, `area:*`,
`priority:*`, `status:*`, `release:*`, `provenance:*`. Every issue and PR gets one `type:*` and
one `area:*`; never two labels from the same family. `bug`, `enhancement`, and `documentation`
are superseded by `type:bug`, `type:feature`, and `type:docs` respectively, recorded as a
migration map; they and the other five defaults are retained, not deleted (the sync tool never
deletes or renames a label, so the migration is additive only). `tools/sync_labels.py` applies
the registry to GitHub, dry-run by default. `kit/checks/label_refs.py` proves issue forms and
labeler config name only registered labels. Full rules and rationale: `docs/labels.md`.

Path-based PR auto-labeling was evaluated and deferred: this repo's PR volume does not yet
justify a labeler workflow, its pinned-action maintenance, and a second path-to-label mapping to
keep in sync with this registry.

## Alternatives

- Adopt ACK's full label taxonomy. Rejected: `ledger:*` and its policy-tracking labels are
  company-scale and REJECTED-FIT for a solo repo; copying the rest verbatim would still be
  oversized for Outpost's issue volume.
- Delete the GitHub defaults and replace them outright. Rejected: this task's granted authority
  and the mission's own rule forbid deleting or renaming an existing label without a separate
  decision; retaining them costs nothing and avoids relabeling closed history.
- Add path-based auto-labeling now. Rejected for now: see Consequences; revisit if PR volume
  grows.

## Consequences

Issues and PRs carry real routing signal (`type`, `area`) without team-scale label sprawl. The
registry is version-controlled and drift-checked (`label_refs`), so a config file cannot silently
reference a label that was never created. What to watch: `status:*` and `release:*` depend on the
labeler applying them by judgment (no code enforces "one issue, one type" at label-apply time,
only that referenced labels exist); if that judgment call proves unreliable, a future decision
could add a live GitHub Actions check instead of relying on `kit/checks/label_refs.py`'s
config-only scope. Reverse the auto-labeling deferral if PR volume grows enough that manual
labeling becomes the bottleneck.
