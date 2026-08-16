# 0030: Fix a dangling-symlink install-time write, and close a related open question

Status: Accepted
Date: 2026-08-15

## Context

A follow-up to ADR-0028's Alternatives section, which named an explicitly deferred question:
whether install.py's plan-derived unlink() sites (not manifest-derived, so outside
`_is_contained`'s original coverage) could be redirected outside the project via a pre-planted
symlink at a fixed, kit-owned path.

Investigated by reading `prune_orphans` and `remove_for_tools` in full, not just the line
proximity to `.unlink()`. Both plan-derived delete sites already gated deletion on the target's
content byte-matching the kit's own known-good bytes before ever calling `.unlink()`, guards built
to protect a user's hand-edited file, not reasoned about as a symlink defense, but which appeared
to close the symlink-redirect delete attack as a side effect: unlike ADR-0028's manifest-derived
bug, where a crafted manifest let the attacker control both the path and the expected hash, an
attacker here cannot make an arbitrary outside file's real content byte-match a specific Outpost
prompt file's exact bytes. That reasoning held for an attacker-crafted target. It does not hold for
a real, non-malicious one, below.

While tracing those delete-side guards, `apply()` (the function that writes every plan-derived file
to disk) turned out to have no equivalent guard on its write path, confirmed by directly
reproducing both a crash and a silent outside-project write against the real `install.py`. What
decides whether `write_bytes` raises or follows a dangling symlink is not dangling-vs-existing or
inside-vs-outside the project; it is whether the symlink's own stored target string uses a forward
slash. A forward-slash-relative target, escaping or not, makes `write_bytes` raise `OSError:
[Errno 22] Invalid argument` before writing anything; a bare filename, a backslash-relative target,
or an absolute path all make it follow the symlink and write at the resolved location instead, with
no error at all. A dangling symlink at a plan-derived write path, planted before a project's first
install, reproduced both failure modes this way. POSIX's `open()` has no such forward-slash quirk,
so a silent outside-project write is plausibly the only failure mode there, for any relative or
absolute dangling symlink; that POSIX-specific claim stays a reasoned hypothesis, not a direct
reproduction, since this kit is developed on Windows.

Two smaller instances of the identical missing-containment-check shape existed at the time:
`apply_stale_terse`'s clear branch and `unmerge_kit_settings`'s write-back, both writing to
`.claude/settings.json`. Two further sites at the fixed constant path `.outpost/manifest.json` (the
manifest-persist write in `--prune`, the manifest write-or-delete in `--remove`) were scoped out as
sharing ADR-0028's own "fixed, kit-owned location" out-of-scope category. That categorization did
not hold up; see below.

A `risk-review` dogfood run (ADR-0027) against the pull request carrying the fix above, run before
it merged, attacked its claims instead of just reading them, and broke three.

First, the delete side was not actually closed. The byte-match reasoning above fails in a real,
non-malicious setup: a project whose `.claude/` is a directory symlink to a location shared with
another project. The shared location's content is not an attacker's arbitrary bytes; it is the
kit's own bytes, genuinely written there by installing into the other project. Reproduced end to
end: installing into the symlinked project correctly skipped writing (the bug above, now fixed),
but a later `--remove` in that same project still deleted the file at the shared location. The root
cause: `main()` computes each path's manifest ownership record before `apply()` decides, later in
the same run, to skip that path for escaping containment. The record step never learns about that
skip, so an escaping path was still recorded as `{"existed": false, "kit_hash": ...}`, identical to
a path the kit genuinely wrote. That false record is what authorized the delete: `remove_for_tools`'s
own `rec is not None and rec.get("existed")` skip-guard did not fire, because `existed` was false,
so it fell through to the byte-match check, which passed because the content really was the kit's
own bytes.

A fix that simply stops the manifest from recording that false claim is necessary, but proved not
sufficient by itself. `_file_records` seeds each install's records with `dict(prev_files)`,
deliberately carrying every prior install's records forward, so that a narrower reinstall
(`--only`/`--exclude`) does not mistake old ownership history for the user's data. A path outside
the current run's own plan, because a narrower reinstall excludes it, is never reached by a
record-time correction either: a path that was legitimately installed, then later symlink-escaped,
then survives a narrower reinstall, keeps its old, now-stale ownership record. A full install, a
symlink planted at an installed path, then a narrower `--only` reinstall, then `--remove`/`--prune`,
reproduced deleting up to 28 real files outside the project this way with a record-time fix alone in
place; adding an independent containment check at the actual point of deletion, regardless of what
the manifest record claims, closed it to 0.

Second, the "fixed, kit-owned location" scoping-out was wrong. `CLAUDE.md` and every `SKILL.md`
path are equally fixed and equally attacker-predictable, and are exactly what this fix already
guards; `.outpost/manifest.json` is no different in kind, only in name. Both its write site (in
`--prune`) and its write-or-delete site (in `--remove`) were reproduced escaping through a
symlinked `.outpost` directory the same way.

The same review pass found a fifth unguarded site outside the four above: `apply_stale_terse`'s
"remove" branch (it deletes the kit's own stale terse-style file when a plain reinstall supersedes
an earlier terse one), sharing the identical missing-check shape as its sibling "clear" branch three
lines below, which already had one. Reproduced with the same non-malicious shared-symlink setup: a
plain reinstall over a project whose `.claude/` is a directory symlink deleted a real file outside
the project.

Third, the reporting gap. Installing into the symlinked project read as an ordinary success, while
`--verify` afterward reported permanent, unfixable drift, and the two never agreed or said why.
Giving an escape its own visible outcome, instead of the same bucket as an ordinary pre-existing-
file skip, surfaced two more corrections. The escape check inside `apply()`'s loop has to run
before the pre-existing-file/WARN logic, not after: checked afterward, a path that both escapes and
happens to look pre-existing or hand-edited misreports, either a spurious overwrite warning or a
false `unchanged` status, instead of the escape itself. And `verify()`'s new `ESCAPED` status must
not fire for a user-owned or create-mode path, one the kit never writes regardless of whether it is
a symlink: a user who symlinks their own `CLAUDE.md` to a shared dotfiles location is not an attack,
and flagging it `ESCAPED` contradicts `verify()`'s own documented contract that a user-owned target
is fine present or absent.

This is the second major revision of this record's technical content: the version above (a write
guard at three sites, the delete side closed by reasoning alone) shipped, then a `risk-review` run
found it incomplete before the pull request carrying it ever merged. That is distinct from the
three earlier rounds already in this file's history, which corrected only the write-side
reproduction's own wording, not its coverage.

## Decision

Close the delete side for real, and give an escape its own outcome, in addition to the original
write guard.

Reuse `_is_contained` (ADR-0028) as a pre-write containment guard at `apply` (the single choke
point every `write`, `create`, and `merge`-mode action funnels through), `apply_stale_terse`'s
clear branch, and `unmerge_kit_settings`'s write-back, same as before.

**Make the manifest truthful.** Before `main()` builds the action that persists the manifest, drop
the ownership record for any path `apply()` will itself skip for escaping containment. No record is
what every consuming guard (`remove_for_tools`, `prune_orphans`, `unmerge_kit_settings`) already
reads as "no proof the kit owns this, leave it alone."

**Check containment independently at every remaining write or delete site**, not only at
record-construction time: `remove_for_tools`'s main loop, `prune_orphans`'s de-selected-orphan loop,
the `--prune` manifest-persist write, the `--remove` manifest write-or-delete, and
`apply_stale_terse`'s remove branch. This is the fix that actually closes the delete side for a path
whose ownership record was carried forward, stale, from before it was symlink-escaped; the manifest
fix above is necessary but, by itself, only ever reaches the current run's own plan.

**Give an escape its own visible outcome.** `apply()` tallies a `"skip (escapes)"` outcome distinct
from `"skip (exists)"`, and checks containment first in its loop, before the pre-existing-file/WARN
logic. `verify()` reports a distinct `ESCAPED` line, checked after its existing user-owned/create
short-circuit so a legitimate symlinked dotfile never misreports. The install summary line names how
many paths were left alone for escaping, when any were.

Fourteen new regression tests in `tests/test_install.py`, plus one pre-existing test rewritten:

- Root cause: `test_manifest_records_no_ownership_for_a_symlink_escaped_path`.
- The four independent sites: `test_remove_for_tools_skips_a_path_that_escapes_via_a_symlink`,
  `test_prune_orphans_skips_a_path_that_escapes_via_a_symlink`,
  `test_prune_does_not_persist_the_manifest_through_an_escaping_symlink`, and, for `--remove`'s
  manifest guard, two tests since the guard has both a delete branch and a write branch (only the
  delete branch, the harmless one, was covered at first):
  `test_remove_does_not_delete_the_manifest_through_an_escaping_symlink` and
  `test_remove_does_not_overwrite_the_manifest_through_an_escaping_symlink`.
- The fifth site: `test_apply_stale_terse_skips_a_remove_through_a_symlink`.
- Closing a test gap on an already-shipped guard that had never had its own regression test:
  `test_apply_stale_terse_skips_a_clear_through_a_symlink`.
- The reporting fix and two refinements found only once it was in place:
  `test_install_reports_a_symlink_escape_distinctly_from_an_ordinary_skip`,
  `test_verify_reports_escaped_distinctly_from_missing`,
  `test_install_summary_notes_an_escape_when_one_occurs`,
  `test_install_summary_omits_the_escape_note_when_nothing_escapes`,
  `test_apply_checks_containment_before_the_pre_existing_and_warn_logic` (pins the ordering), and
  `test_verify_reports_ok_for_a_user_owned_or_create_path_that_escapes_via_a_symlink` (pins the
  user-owned exception).
- Rewritten, not new: `test_unmerge_settings_skips_a_write_back_through_a_symlink`'s original
  symlink target used a Windows-style backslash-relative string. POSIX treats a backslash as an
  ordinary filename character, not a separator, so the target never actually left the project under
  POSIX path rules, the guard never fired, and the test passed on 3 of this repo's 4 CI legs without
  exercising it. Rewritten to an absolute target, which escapes on every platform.

## Alternatives

- Fix only `apply`'s single call site, leave the rest alone. Rejected: every other site shares the
  identical missing-check shape and was cheap to close once found; leaving a known gap unfixed
  repeats the exact situation ADR-0028 itself was written to close, now with more sites found the
  same way.
- Raise a loud error instead of silently skipping. Rejected for the same reason ADR-0028 rejected
  it: one hostile or accidentally-broken symlink must not abort an install with other legitimate
  files still to write.
- Reproduce the hypothesized POSIX silent-write-through variant directly. Not done: this kit is
  developed on Windows. The fix closes the hypothesized POSIX variant by construction, since an
  escaping path is skipped before any write or delete is attempted regardless of platform, but that
  confidence is reasoned, not this-repo-proven, for the POSIX case specifically. Two of this
  revision's own regression tests initially relied on the same Windows-only path-separator quirk to
  look like they proved the POSIX case, and did not (see the rewritten test above), a concrete
  reminder that this gap is real, not academic.
- Fix only the containment checks at each delete/write site, without also making the manifest
  truthful. Rejected: it closes the immediate reproductions but leaves the manifest permanently
  lying about a skipped path's ownership, a correctness problem in its own right regardless of
  whether every future consumer of that record happens to also check containment.
- Fix only the manifest's truthfulness, without the independent checks at each site. Rejected:
  sound reasoning alone said this should be enough, but it was proven wrong by the carried-forward-
  records case above (28 files deleted with only that fix in place), and this fix's own history,
  three ADR-text rounds each correcting a claim that did not hold up, then a fourth finding the code
  itself had gaps, argues against trusting one non-redundant mechanism for a security property this
  significant. The extra checks are cheap and the pattern is already proven.
- Treat the reporting gap as out of scope, matching the original silent-skip philosophy. Rejected:
  "silent" always meant "does not abort the operation," not "reports success indistinguishably from
  a real install, while `--verify` reports permanent, unexplained drift afterward." The latter is a
  usability regression this fix introduces into an ordinary, non-malicious workflow (shared
  dotfiles via symlinks), not a property inherited from the rest of the file's existing behavior.

## Consequences

A pre-planted symlink at a plan-derived write path can no longer write kit content there or crash
`install.py`. A project whose kit-managed directory is a symlink shared with another project, a
real, non-malicious setup, is now handled correctly end to end: install skips writing through it,
the manifest records no false ownership for the skipped path, and a later `--remove` or `--prune`
cannot delete anything at the shared location, even when an older, now-stale ownership record from
before the symlink was planted would otherwise have survived a narrower reinstall along the way.
`_is_contained` is now checked at 15 call sites across the file: the 3 original write guards, 5
more added by this revision (4 defense-in-depth sites plus the fifth site found during its own
review), `_retired_paths` (ADR-0028), the reporting-only checks in `verify()` and `main()`'s own
record correction, and 4 more from three later rounds holding dry-run, orphan, and `--verify`
reporting to the same standard: `_orphans()`'s escaped split and `render_plan()`'s dry-run check,
then `main()`'s own separate dry-run preview for stale-terse withdrawal (a second code path
`render_plan()` does not reach), then that same stale-terse gap in `main()`'s `--verify` branch,
which `verify()` itself does not reach either.

An install or `--verify` run now says plainly when a path was left alone for escaping the project,
instead of reporting success or unexplained drift; a user-owned symlinked dotfile is unaffected by
this, on purpose. `tests/test_install.py` grew from 124 to 138 tests across this revision (17
total across this record's history to that point: 3 from the first version, 14 from this
revision), plus the one rewritten test above. Four later rounds then closed the same reporting gap
at four more surfaces, adding 9 more tests (4 for `_orphans()`'s escaped split and
`render_plan()`'s dry-run check, 1 for `main()`'s own separate dry-run stale-terse preview, 2 for
`verify()`'s own summary split between an escaping action and a genuinely fixable one, 2 for
`main()`'s `--verify` branch making that same split for stale-terse withdrawal state): 147
tests total as of this fix. Two of this revision's own new tests initially shared the same
Windows-only path-separator blind spot as the rewritten one, caught and fixed before this record
was written, not after.

A narrower, more benign residual stays open, unaffected by this revision: a dangling symlink that
resolves safely inside the project is correctly judged contained and let through, so a
forward-slash-relative one still crashes the install with the same `[Errno 22]` error as before;
this is a locally broken symlink crashing its own install, not an attacker redirecting a write. Also
unaffected: `_is_contained` resolves its target internally but returns only a bool, and every call
site then acts on the original, unresolved path, which the operating system resolves again at each
later syscall, so a path component swapped between the check and the write could in principle defeat
the guard. That requires an active, concurrent, adversarial process with live write access to the
project during the install itself, a materially higher bar than the static pre-planted symlink this
fix closes: a process already holding that level of access could write the target directly, no race
needed. Named here, not resolved by this fix, the same treatment ADR-0028 gave its own scoped-out
question.
