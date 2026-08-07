---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-08-07
---

# Labels

Outpost issues and PRs use a small, namespaced label set instead of GitHub's flat defaults. The
registry (`kit/labels/registry.json`) is the source of truth; `tools/sync_labels.py` applies it
to GitHub; `kit/checks/label_refs.py` proves issue forms and labeler config name only registered
labels. Rationale and rejected alternatives: [ADR-0022](decisions/0022-label-governance.md).

## Families

- `type:*` (bug, feature, docs, refactor, maintenance, security) - what kind of change.
- `area:*` (prompts, adapters, installer, plugin, docs, governance, release) - what it touches.
- `priority:*` (p0-p3) - how urgent, issues only.
- `status:*` (blocked, needs-decision, ready) - added only when it changes routing.
- `release:*` (major, minor, patch) - a user-visible PR's SemVer impact.
- `provenance:*` (clean-room, needs-review) - for work adapted from an external design comparison.

## Rules

- Every issue and every PR gets exactly one `type:*` and one `area:*`.
- An issue may get one `priority:*`.
- Never apply two labels from the same family.
- A user-visible PR gets one `release:*` label.
- Work independently designed from an external capability comparison gets `provenance:clean-room`.

## Migration from the GitHub defaults

`bug` maps to `type:bug`, `enhancement` maps to `type:feature`, `documentation` maps to
`type:docs`. These three are not deleted, only superseded going forward; the sync tool never
deletes or renames a label. `duplicate`, `good first issue`, `help wanted`, `invalid`,
`question`, and `wontfix` are retained as-is; they have no namespaced equivalent and stay useful
without one.

## Syncing to GitHub

`python tools/sync_labels.py` prints the plan (labels to create, labels to update, labels
already correct) without writing anything. `python tools/sync_labels.py --apply` applies it via
the `gh` CLI. The tool never deletes or renames a label, on either path; a live label with no
registry match is reported, not touched.

## Path-based auto-labeling

Evaluated and deferred: PR volume on this solo repo is low enough that manual labeling costs
less than a labeler workflow, its pinned-action maintenance, and a second label-to-path mapping
to keep in sync with this registry. Revisit if PR volume or contributor count grows enough that
manual labeling becomes the bottleneck.
