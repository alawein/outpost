---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-08-27
---

# Labels

Outpost issues and PRs use a small, namespaced label set instead of GitHub's flat defaults. The
registry (`kit/labels/registry.json`) is the source of truth; `tools/sync_labels.py` applies it
to GitHub; `kit/checks/label_refs.py` proves the issue forms name only registered labels.

## Families

- `type:*` (bug, feature, docs, refactor, maintenance, security) - what kind of change.
- `area:*` (prompts, adapters, installer, plugin, docs, governance, release) - what it touches.
- `priority:*` (p0-p3) - how urgent, issues only.
- `status:*` (blocked, needs-decision, ready) - added only when it changes routing.
- `release:*` (major, minor, patch) - a user-visible PR's SemVer impact.

## Rules

- Every issue and every PR gets exactly one `type:*`.
- Every PR gets one `area:*`. An issue gets one `area:*` too when the form itself makes the area
  unambiguous at filing time (a prompt proposal is always `area:prompts`); when it is not (a bug
  or a feature can touch anything), the issue form applies `type:*` only and `area:*` is added at
  triage.
- An issue may get one `priority:*`.
- Never apply two labels from the same family.
- A user-visible PR gets one `release:*` label.

## Migration from the GitHub defaults

`bug` maps to `type:bug`, `enhancement` maps to `type:feature`, `documentation` maps to
`type:docs`. These three are not deleted, only superseded going forward; the sync tool never
deletes or renames a label. `duplicate`, `good first issue`, `help wanted`, `invalid`,
`question`, and `wontfix` are retained as-is; they have no namespaced equivalent and stay useful
without one.

## Syncing to GitHub

`python tools/sync_labels.py` prints the plan (labels to create, labels to update, labels
already correct) without writing anything. `python tools/sync_labels.py --apply` applies it via
the `gh` CLI. The repo is inferred from the origin remote; pass `--repo owner/name` to point at
another. The tool never deletes or renames a label, on either path; a live label with no
registry match is reported, not touched.

## Path-based auto-labeling

Evaluated and deferred: PR volume on this solo repo is low enough that manual labeling costs
less than a labeler workflow, its pinned-action maintenance, and a second label-to-path mapping
to keep in sync with this registry. Revisit if PR volume or contributor count grows enough that
manual labeling becomes the bottleneck.
