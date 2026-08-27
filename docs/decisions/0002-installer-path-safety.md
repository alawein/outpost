# 0002: Installer path safety

Status: Accepted
Date: 2026-08-27

## Context

`install.py` writes, verifies, prunes, and removes files inside a consumer project, driven by
a manifest it reads from that project. A crafted manifest, or a symlink planted at an install
path, could otherwise steer a write or a delete outside the project root.

## Decision

Four rules, each enforced in code and covered by `tests/test_install.py`:

- A manifest `files` key is a project-relative POSIX path. `parse_manifest` (in
  `kit/installers/manifest.py`) rejects an absolute path, parent traversal, a backslash, a
  colon (drive letter or NTFS stream), or a null byte.
- Every write and every delete site checks containment on its own, through `_is_contained`,
  which resolves symlinks before comparing against the project root. Sites: `apply`,
  `apply_stale_terse`, `unmerge_kit_settings`, `remove_for_tools`, `prune_orphans`,
  `_orphans`, `render_plan`, `verify`, both manifest write sites, and `main`.
- The manifest never records ownership of a path that was skipped for escaping, so a later
  prune or remove cannot treat it as kit-owned.
- An escape is visible, never silent: `skip (escapes)` in a plan, `ESCAPED` in verify, and a
  summary note. A path with no record proving kit authorship is never deleted; a settings
  file for a tool that was never installed is left alone.

## Alternatives

Validate only at manifest parse time (misses a symlink planted after install); trust the
manifest (the project is the untrusted input).

## Consequences

Every new write or delete path in the installer must call `_is_contained` and add a test
that seeds an escaping path and shows it skipped and reported.
