# 0016: Retire two of the installer's legacy paths, keep the records-less ownership fallback

Status: Accepted
Date: 2026-07-12

## Context

`install.py` carried three paths tied to older kit versions: the `.agi-coding-kit/` manifest
migration (the pre-rename state dir), the v0.24.0 Cursor rule-rename sweep
(`.cursor/rules/agi-coding-kit*`), and the records-less ownership fallback (ownership for a manifest
that has a tool entry but no per-file `files` map). A sweep of the estate found zero `.agi-coding-kit`
manifests and zero legacy Cursor rules; the predecessor kit is gone and ACK is the one kit.

A first attempt retired all three. Review caught that the third is not dead weight: without it, a
reinstall over a records-less `.ack/manifest.json` records the kit's own earlier files as the
user's (`existed: true`), so the reinstall skips updating them and `--verify` then falsely reports
"in sync" on stale content. The records-less fallback is load-bearing for correctness.

## Decision

Retire the two paths that are genuinely dead, and keep the third:

- Remove the `.agi-coding-kit/` manifest migration (`_migrate_legacy_manifest`,
  `LEGACY_MANIFEST_PATH`, and the read fallback). An install under the old state-dir name no longer
  upgrades in place; it does a clean reinstall.
- Remove the v0.24.0 Cursor rename sweep (`LEGACY_CURSOR_PATHS` and its three helpers). A
  pre-rename Cursor install's old files are left for the user to delete.
- Keep the records-less ownership fallback (`_legacy_claim` and the `_file_records` branch). It
  makes a reinstall over a records-less manifest update the kit's own files (the recorded
  footprint) while still protecting a genuine user file outside that footprint.

## Alternatives

- Retire all three. Rejected: the records-less fallback is load-bearing; removing it makes a
  reinstall silently skip updating prompts and `--verify` falsely report "in sync".
- Keep all three. Rejected: the `.agi-coding-kit` migration and the Cursor sweep have zero
  live installs in the estate and only complicate the installer.

## Consequences

- The installer is smaller (the migration and Cursor sweep are gone) and its manifest read has one
  home (`.ack/`), while the one correct records-less ownership claim stays, with its two tests.
- An old-state-dir or pre-rename-Cursor install does a clean reinstall rather than an in-place
  upgrade; a records-less `.ack` manifest still reinstalls correctly.
- Reverse a retirement only if an old-name or pre-v0.24 install must upgrade in place again, which
  would mean restoring that path from git history.
