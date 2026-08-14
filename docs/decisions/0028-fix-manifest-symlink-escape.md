# 0028: Fix a manifest-driven symlink escape in prune/remove

Status: Accepted
Date: 2026-08-14

## Context

A live dogfood run of a review prompt against install.py's current code found and
reproduced a real vulnerability: `_retired_paths()` (install.py) turns a manifest's `files` keys
into delete candidates for `prune_orphans` and `remove_for_tools`, validated by `parse_manifest`
as strings only (no absolute path, no .., no backslash or colon). A directory symlink already
present in a project lets a clean-looking relative key resolve outside the project root once the
filesystem actually touches it; `_retired_unedited`'s hash check can be satisfied by an attacker
who controls the manifest and therefore the expected hash. A crafted manifest plus a genuine
Windows directory symlink, run against the real kit code, confirmed a file outside the project
root was actually deleted.

This extends the exact threat model the v0.2.0 Security fix closed (rejecting an
absolute/parent-traversal/backslash/colon manifest key), through a mechanism, symlink indirection,
that fix never checked. It was named as a known gap in docs/dogfooding.md's 2026-08-08 row and
never turned into a test, a fix, or a docs/DEBT.md entry until now.

A related, smaller, already-documented gap: unmerge_kit_settings will delete a settings file for a
tool that was never installed in this project, under the same pre-records fallback that legitimately
applies to a genuine legacy manifest. Its own docstring already named this as intended fallback
behavior, not an accident, but it is the same data-loss shape and this repo already has a proven
fix pattern for it (remove_for_tools's own bool(entry) and files is None guard, from PR #25).

## Decision

Two fixes, one PR, both closing a manifest-driven deletion gap in the same family.

- A new `_is_contained(project_root, path)` helper resolves a path (following any symlink) and
  confirms it is still inside the project root; wired into `_retired_paths` as the deciding check
  both `prune_orphans` and `remove_for_tools` inherit for free, since both only ever act on what
  `_retired_paths` returns. An escaping path is silently excluded, consistent with how every other
  per-file problem in this file already degrades to skip rather than aborting the whole operation.
- `unmerge_kit_settings` gets the same `bool(entry) and files is None` legacy-manifest guard
  `remove_for_tools` already proved, so a never-installed tool's settings file is left alone
  instead of falling through to the byte-match-only rule meant for a genuine pre-records manifest.
- Three new regression tests in tests/test_install.py:
  `test_remove_does_not_delete_a_file_outside_the_project_via_a_symlink` (an end-to-end
  symlink-escape test against `remove_for_tools`),
  `test_retired_paths_excludes_a_path_that_escapes_through_a_symlink` (a focused unit test on
  `_retired_paths`), and `test_unmerge_settings_keeps_a_file_for_a_never_installed_tool` (a
  never-installed-tool test on `unmerge_kit_settings`).

## Alternatives

- Validate containment at parse_manifest time. Rejected: no project_root or live filesystem is
  available at parse time; the question can only be answered against the real, current directory
  tree.
- Raise a loud error on an escaping path instead of silently excluding it. Considered; rejected to
  stay consistent with this file's existing skip-and-continue philosophy for every other per-file
  problem, so one bad manifest entry does not abort an operation with other legitimate files to
  process.
- Also harden every unlink() call site that consumes a plan-derived, not manifest-derived, path,
  against a pre-planted symlink at a fixed kit-owned location. Out of scope: a different, not yet
  demonstrated threat model (requires tampering with the project directory before install ever
  runs), left as a named open question rather than silently folded in or silently dropped.

## Consequences

A crafted manifest can no longer redirect `--prune`/`--remove` outside the project root via a
symlink; a never-installed tool's settings file is no longer deletable via the pre-records
fallback. tests/test_install.py grows by 3. An excluded manifest entry is now silently inert rather
than deleted, and stays invisible to `--verify` too (both consume `_retired_paths`'s filtered
result), so a poisoned key persists across future installs without being flagged for cleanup; this
matches the file's existing skip-and-continue philosophy but is a real, if minor, side effect of
it. The scoped-out broader symlink question (a fixed kit-owned path itself behind a pre-planted
symlink) stays open, named here for whoever picks it up next, not resolved by this fix.
