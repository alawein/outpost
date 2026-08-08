---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-07-26
---

# Changelog

Format follows Keep a Changelog (https://keepachangelog.com). The kit uses SemVer.

## [Unreleased]

### Fixed

- `evals/debt-log` checked the eval transcript's chat text for a wording match instead of
  confirming `docs/DEBT.md` was actually modified, a known gap named in ADR-0026's Consequences.
  Added a `file_modified` assertion type to `tools/eval_assertions.py` and switched the eval to
  it; the eval now checks real behavior instead of exact wording.
- `docs/contributing.md` still pointed prompt proposals at the superseded ADR-0013 alone, missing
  the ADR-0025 relaxation every other caller in that PR was updated to reference. The
  prompt-proposal issue form's three recommended fields (binding mechanism, dogfood case,
  deletion condition) were optional with nothing enforcing ADR-0025's own rule that an omission
  must be stated with a named follow-up; they're required again, but a one-line deferral note now
  satisfies the requirement. `docs/how-this-is-built.md` and the issue form also called the same
  field "dogfood run" and "dogfood plan" where the rest of the admission docs say "dogfood case";
  unified on "dogfood case". Caught by a workflow-backed code review.

- `docs/how-this-is-built.md` claimed ADR-0024 named a distinct job, nearest sibling, and unsafe
  default like a prompt admission; it does not, since it adds a check, not a prompt. Corrected,
  along with a hardcoded check count that had no drift protection (now points at
  `docs/ROADMAP.md`'s generated line instead), an absolute claim about the 100-word ceiling that
  omitted its own documented exemptions, and a README line that contradicted `converge`'s
  Claude-only scope stated nine lines above it. Caught by an independent, dogfooded
  `pr-review-toolkit:review-pr` pass on the already-merged PR that introduced them.

### Changed

- ADR-0013's prompt-admission bar relaxed (ADR-0025): distinct job, nearest sibling, and unsafe
  default stay required at admission; binding mechanism, dogfood case, and deletion condition
  become recommended, fillable in a follow-up PR. `docs/how-this-is-built.md`, `README.md`, and
  the prompt-proposal issue form updated to match: the form no longer requires the three
  recommended fields.
- ADR-0013 (prompt admission) moved from Proposed to Accepted: two admissions (ADR-0020,
  ADR-0023) had already followed it as binding.

### Added

- A lightweight behavioral eval harness (`tools/run_evals.py`, `evals/`) for 5 pilot core prompts,
  running each through a real `claude -p` call against a seeded fixture and checking mechanical
  assertions (file created/unmodified, a tool not used, text contains a value). Opt-in, not wired
  into `validate.py` or CI. ADR-0026.
- A house-voice rule in `docs/writing-standard.md`: cite evidence a reader can check, never a
  gitignored scratch path as if it were a verifiable source. Naming the scratch convention itself
  stays fine; citing its content as proof does not.
- `prose_length`, a gate check that fails a markdown paragraph over 100 words (measured against
  the tracked tree; nothing needed a rewrite to adopt it), exempt for the append-only historical
  records (`docs/decisions/`, `docs/DEBT.md`, `docs/dogfooding.md`, `docs/audit/`). ADR-0024.
- `check-intent`, a structured plan-to-diff reconciliation that runs right before `code-review`:
  marks every plan item Done, Missing, or Changed-approach, and every untraceable file Extra.
  ADR-0023 records the admission (independently designed; verified CLEAN-ROOM against ACK's
  equivalent capability after the draft existed) and its first dogfood run.

## [0.3.0] - 2026-08-07

### Added

- Three GitHub-rendered Mermaid diagrams: the workflow path in `docs/workflow.md`, the artifact
  dependency flow in `docs/architecture/topology.md`, and the PR/release state machine in
  `docs/releasing.md`. `docs/brand/flow.svg` stays as the README hero image; a note there records
  why it carries no drift risk (no generated counts) and points to the workflow diagram as the
  reviewable equivalent.

- Five GitHub issue forms under `.github/ISSUE_TEMPLATE/` (bug, feature, prompt proposal,
  hygiene finding, and a config that disables blank issues and links security reports and
  usage questions elsewhere); the four content forms each set a `type:*` label from the
  registry.
- A namespaced label registry (`kit/labels/registry.json`): `type:*`, `area:*`, `priority:*`,
  `status:*`, `release:*`, and `provenance:*`, replacing the flat GitHub defaults. A dry-run-first
  sync tool (`tools/sync_labels.py --apply`) applies it without ever deleting or renaming a label.
  A new `label_refs` check proves issue forms and labeler config name only registered labels.
  Documented in `docs/labels.md`.
- `repo-hygiene-sweep`, an ordered multi-repo inventory, evidence triage, and gated cleanup
  prompt, with ADR-0020 and its first dogfood run.
- ADR-0019, recording the installer path-safety invariant (manifest keys must be project-relative)
  and the v0.2 refinement decisions, including the rejected byte-match ownership fix kept as a
  negative.

### Changed

- Rewrote `.github/PULL_REQUEST_TEMPLATE.md` to request outcome, an intent trace, an evidence
  table, provenance, release impact, and generated-file status, alongside the existing
  what-changed and reviewer-notes sections.

### Fixed

- `docs/adr/0001-repo-architecture.md` no longer contradicts `docs/decisions/`, Outpost's real
  ADR ledger; it is now an explicit compliance stub for the alawein org's doctrine gate. Recorded
  in ADR-0021.

## [0.2.1] - 2026-07-23

### Fixed

- A parent-directory cleanup failure after a successful `unlink` no longer misreports a completed
  delete as failed (which also skipped dropping the file's ownership record). Cleanup is now
  best-effort.

### Changed

- Corrected the `tolerant`-flag comments (prune is fail-loud, not tolerant) and the stale
  `prune_orphans`/`remove_for_tools` return-tuple docstrings.
- Added tests for the `banned_sync` reverse branch, an edited orphan keeping its ownership record
  on prune, and `--remove` leaving a corrupt settings file untouched.

## [0.2.0] - 2026-07-23

### Added

- Three gate checks: `plugin_orphans` (a stale skill in the plugin tree that no longer maps to a
  catalog prompt), `banned_sync` (the banned-word register in `docs/writing-standard.md` must match
  the words the `voice` check enforces), and a wider `doc_truth` that resolves prompt references
  across the instruction docs, not just `workflow.md`.
- `SECURITY.md` (private vulnerability reporting) and `.github/CONTRIBUTING.md`.
- ADR-0018, the solo review model, superseding ADR-0006.

### Changed

- `split-change` and the `/outpost:ship` command are draft-only: neither stages, commits, or opens
  a pull request, matching `prepare-pr`. Opening the PR stays a human action.
- The review-model docs (CLAUDE.md, contributing, CODEOWNERS, the PR template) now describe the
  solo repo honestly instead of an unsatisfiable one-maintainer-approval gate.
- Added missing routing lines between related prompts (refactor-safely to simplify, plan-change to
  interrogate, grill to prove, respond-to-review and triage to each other).
- Consolidated the triplicated per-tool install table and flag reference; `docs/adapters.md` owns
  them and the other docs link to it.

### Fixed

- The installer dropped a de-selected orphan's ownership record on prune, so a file the user later
  creates at that path is no longer overwritten on reinstall.
- A corrupt `.claude/settings.json` no longer crashes `--verify`, `--prune`, or `--remove`; verify
  and prune fail cleanly, and remove still deletes the prompt files while leaving the corrupt
  settings file untouched.

### Security

- The installer now rejects `.outpost/manifest.json` file keys that escape the project root:
  absolute, parent-traversal, Windows backslash, UNC, and drive-letter or embedded-colon paths. A
  crafted manifest in a cloned repo could otherwise have steered `--prune` or `--remove` to unlink a
  file outside the project on Windows. Found and closed before any release carried it.

### Removed

- The unused `cat` parameter on four installer functions and a dead `typing` import.

## [0.1.0] - 2026-07-18

### Added

- Initial public release as Outpost, forked from an internal predecessor kit (ADR-0017). The
  predecessor's own version history is not carried forward; see `docs/decisions/` and
  `docs/audit/` for the design decisions behind this tree.
