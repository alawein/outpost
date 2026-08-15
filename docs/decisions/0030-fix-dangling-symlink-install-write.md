# 0030: Fix a dangling-symlink install-time write, and close a related open question

Status: Accepted
Date: 2026-08-15

## Context

A follow-up to ADR-0028's Alternatives section, which named an explicitly deferred question:
whether install.py's plan-derived unlink() sites (not manifest-derived, so outside
`_is_contained`'s original coverage) could be redirected outside the project via a pre-planted
symlink at a fixed, kit-owned path.

Investigated by reading `prune_orphans` and `remove_for_tools` in full, not just the line
proximity to `.unlink()`. Both plan-derived delete sites already gate deletion on the target's
content byte-matching the kit's own known-good bytes before ever calling `.unlink()` (guards that
exist to protect a user's hand-edited file, not originally reasoned about as a symlink defense,
but which close the symlink-redirect delete attack as a side effect: an attacker cannot make an
arbitrary outside file's real content byte-match a specific Outpost prompt file's exact bytes).
This differs from the original manifest-derived bug (ADR-0028), where the attacker controlled both
the path and the expected hash via the crafted manifest itself, so no content check could
distinguish a legitimate delete from a malicious one. No code change follows from this question;
it is closed here with reasoning.

While tracing those delete-side guards, `apply()` (the function that writes every plan-derived file
to disk) turned out to have no equivalent guard on its write path, and this is not merely
theoretical. A dangling symlink (target does not yet exist) planted at a plan-derived write path
before a project's first-ever install was live-reproduced in this session crashing
`python install.py` outright: `error: install failed partway: [Errno 22] Invalid argument: '...'`
(Windows; `write_bytes` on a dangling symlink raises rather than following it). POSIX systems were
not directly testable in this environment; standard POSIX `open()` semantics for a dangling symlink
in write mode can create the file at the resolved target path rather than raising, so the practical
failure mode there is plausibly a silent write outside the project root rather than a crash. This
is a reasoned hypothesis from documented POSIX behavior, not reproduced here, and named as such.

Two smaller instances of the identical missing-containment-check shape were found while checking
every `write_bytes` call site in the file individually: `apply_stale_terse`'s clear branch and
`unmerge_kit_settings`'s write-back, both writing to `.claude/settings.json`. Both are narrower in
practice (each only reaches `write_bytes` after a prior read on the same target succeeds) but share
the same gap as `apply`'s own site. Two further `write_bytes` sites exist (the manifest-persist
writes in `--prune` and `--remove`), both at the fixed constant path `.outpost/manifest.json`;
these share ADR-0028's own out-of-scope category (a fixed, kit-owned location) rather than this
fix's target, and stay open the same way ADR-0028 left its own version of this question open.

## Decision

Reuse `_is_contained` (ADR-0028), already proven for the delete side, as a pre-write containment
guard at all three unguarded `write_bytes` call sites: `apply` (the single choke point every
`write`, `create`, and `merge`-mode action funnels through), `apply_stale_terse`'s clear branch,
and `unmerge_kit_settings`'s write-back. An escaping path is silently skipped, consistent with
this file's existing skip-and-continue philosophy for every other per-file problem (an edited
file, a permission failure, a lock), rather than aborting an install that has other, legitimate
files to write. Two of the three sites print a message naming the skip; the third
(`unmerge_kit_settings`) records it internally as a `"skipped"` outcome, matching how that
function already handles its other skip reasons without printing them directly (its one caller
only prints `"removed"`/`"unmerged"`/`"failed"` outcomes).

Three new regression tests in tests/test_install.py:
`test_install_skips_a_plan_derived_path_behind_a_dangling_symlink` (end-to-end, reproduces the
live-confirmed crash), `test_apply_skips_a_write_action_whose_target_escapes_via_a_symlink`
(focused unit test on `apply`), and `test_unmerge_settings_skips_a_write_back_through_a_symlink`
(the narrower existing-target case in `unmerge_kit_settings`).

## Alternatives

- Fix only `apply`'s single call site, leave the other two alone. Rejected: both are cheap, already
  located, and share the identical missing-check shape; leaving a known gap found in the same pass
  unfixed repeats the exact situation this ADR's own delete-side predecessor (ADR-0028) was written
  to close.
- Raise a loud error instead of silently skipping. Rejected for the same reason ADR-0028 rejected
  it: one hostile or accidentally-broken symlink must not abort an install with other legitimate
  files still to write.
- Reproduce the hypothesized POSIX silent-write-through variant directly. Not done: this
  environment is Windows-only. The fix closes the hypothesized POSIX variant by construction (an
  escaping path is skipped before any `write_bytes` call is attempted, regardless of what that call
  would have done on a given platform), so a platform-specific reproduction was not required for
  confidence the fix covers it, though that confidence is reasoned, not this-session-proven, for
  the POSIX case specifically.

## Consequences

A pre-planted symlink (dangling or not) at a plan-derived write path can no longer crash
`install.py` or write kit content to a location outside the project. The delete-side question
ADR-0028 left open is closed with reasoning, not code, since the existing byte-match guards already
cover it. `tests/test_install.py` grows by 3. The CI matrix's `ubuntu-latest` and `windows-latest`
legs both exercise the new tests, giving the POSIX hypothesis real, if not this-session-live,
coverage. A smaller gap stays open the same way: `_is_contained` resolves the target internally but
returns only a bool, and all three call sites then act on the original, unresolved path, which the
operating system resolves again at each later syscall, so a path component swapped between the
check and the write could in principle defeat the guard. That requires an active, concurrent,
adversarial process with live write access to the project during the install itself, a materially
higher bar than the static pre-planted symlink this fix closes: a process already holding that
level of access could write the target directly, no race needed. Named here, not resolved by this
fix, the same treatment ADR-0028 gave its own scoped-out question.
