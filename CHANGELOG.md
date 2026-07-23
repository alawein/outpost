# Changelog

Format follows Keep a Changelog (https://keepachangelog.com). The kit uses SemVer.

## [Unreleased]

### Added

- ADR-0019, recording the installer path-safety invariant (manifest keys must be project-relative)
  and the v0.2 refinement decisions, including the rejected byte-match ownership fix kept as a
  negative.

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
