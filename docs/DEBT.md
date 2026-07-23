# Debt

Deliberate shortcuts and known limitations, tracked here so they are not silently accrued.
One entry per item: the shortcut, why it was taken, and what would close it. Move an entry to
Closed with the PR that closed it; never delete one.

## Open

None.

## Closed

- 2026-07-11, four PRs admin-merged without a second human approval. #111, #113, #114, and this
  recording PR #115 were squash-merged with `--admin`, bypassing the branch-protection review
  requirement, because the author cannot approve their own PR and no maintainer review was
  obtained in session. Taken because the owner directed the finalize and each change was CI-green
  and independently reviewed (Codex plus a review agent, which caught and fixed a real defect in
  #113 and #114 before merge). Cost: four changes reached `main` without the maintainer approval
  the rule requires, this entry among them. Close by routing future PRs through a maintainer
  approval (Omkar or Carlos) rather than an admin bypass. Closed 2026-07-23: overtaken by the fork.
  ADR-0017 moved the kit to a solo repo and ADR-0018 set the solo review model, so the close
  condition (a second approver from the old team) no longer exists; the owner's direct merge on
  green CI is now the sanctioned path, not a bypass.

- 2026-07-13, repeat admin-merge without a maintainer approval. #124, #119, #122, #126, #127,
  #125, and this recording PR #128 were squash-merged with `--admin`, again bypassing the
  branch-protection review requirement: this is the same pattern the 2026-07-11 entry above
  names, and its close-by trigger (route future PRs through Omkar or Carlos) was not followed.
  Taken because the owner explicitly directed the bypass in-session; all seven were CI-green
  (17/17 gate, full suite), and #124 additionally carried an independent per-task and
  whole-branch review before merge. Cost: seven changes reached `main` without the required
  review, and the standing trigger went unenforced a second time. Close the same way: an actual
  maintainer approval lands on the next PR, breaking the pattern instead of re-documenting it.
  Closed 2026-07-23: same resolution as the entry above, overtaken by ADR-0017 and ADR-0018. The
  old team's second-approver pool is gone with the fork, so this pattern cannot recur under the
  solo model, where the owner's direct merge on green CI is the sanctioned path.

- 2026-07-11, doc_truth skips single-word prompt names. The `REF` regex resolves only hyphenated
  backtick tokens, so a single-word prompt name (`grill`, `prove`, `panel`, `triage`, `converge`,
  `simplify`, `interrogate`, `premortem`) in docs/workflow.md was never
  checked against the catalog: a typo to a non-existent one-word name stayed green. Taken because
  the safe broadening (match every single-word backtick token) was assumed to false-fail on
  ordinary prose words (`git`, `main`, a stage name), needing an allowlist of non-prompt backtick
  words. Closed by swapping in `SKILL_REF` (already used for this exact purpose in
  `plugin_sync`): every backtick token in workflow.md resolves to a real catalog prompt name, so
  no allowlist was needed after all.

- 2026-07-11, retired host files skip the edited-file guard. A prompt retired from a host
  (the catalog hosts field) was removed by --prune/--remove on the manifest's kit-created
  proof alone; a user's hand edits to that file were not detected, unlike plan-derived files,
  because the old kit version's bytes were unknowable at the new version. Taken because the
  honest alternative (per-version content hashes in the manifest) was a bigger change than
  the wave allowed. Closed by recording a content hash (kit_hash) per kit-created path at
  install time and checking it before a retired-path delete: a match deletes as before, a
  mismatch skips and reports it the same way an edited still-shipping orphan already is.
  (2026-07-12, PR #119)

- 2026-07-09, dogfooding.md removed-skill markers. Five rows (2026-06-30) name six prompts that
  no longer ship: `review-change`, `sync-slack`, `serve-guides`, `heal-guides`, `guides-watch`,
  `export-training-data`. The ledger is append-only by design, so the rows stay, but nothing
  marks that these left in v0.23.0's distill (or that `review-change` became `code-review`),
  so a new teammate reading the ledger cannot tell a live skill from a retired one without
  cross-checking the catalog. Taken because this is a readability gap, not a factual error,
  and the ledger's own append-only rule forbids editing the historical rows. Closed by the
  dated header note in dogfooding.md naming the v0.23.0 retirements and the `review-change`
  -> `code-review` rename, data rows untouched (2026-07-10, PR #98).

- 2026-07-09, flow.svg counts sit outside the count checks. The README hero image
  (`docs/brand/flow.svg`) carries a prompt count as SVG text, which `docs_sync` and
  `doc_truth` do not read, so it drifted to 21 while the docs said 24 (caught in the v0.25.0
  review, fixed by hand). Taken because the doc generators only rewrite marked markdown
  spans. Closed by replacing the hardcoded number with wording that carries no count ("The
  prompt pack as skills for ..."), so there is nothing left for a check to read or drift.
- 2026-07-09, cursor legacy rule orphans. The v0.24.0 rename moved the installed Cursor rule
  from `.cursor/rules/agi-coding-kit.mdc` (and its prompt dir) to `.cursor/rules/ack.mdc`.
  Orphan detection enumerates paths from the current adapter plan only, so a project that
  installed under the old name and re-installs keeps both rule sets: `--verify` is blind to
  the old files and `--prune`/`--remove` never touch them, and Cursor loads both. Taken
  because the rename PR kept orphan logic name-agnostic; manual cleanup is one delete of
  `.cursor/rules/agi-coding-kit*`. Closed by teaching `--prune` and `--remove` the legacy
  cursor footprint (a `LEGACY_CURSOR_PATHS` constant, swept unconditionally when cursor is in
  scope, so a pre-rename install self-heals), and by adding a stderr warning to the state-dir
  migration's swallowed OSError. `--verify` is unchanged; it does not check these paths.
  Since removed: ADR-0016 retired the sweep (the constant and its helpers) after an estate
  sweep found zero legacy Cursor rules; the entry stays closed, the mechanism is gone.
- 2026-07-02, eval CLI exit codes. Every wired verb returned 0 when traces were skipped (all
  four verbs) or judge input was missing (score, replay, judge), visible only in the summary
  text, so automation keying on exit status read a partial run as success. Closed by the
  eval-CLI-honesty wave: the CLI now exits 2 when a result carries warnings (a trace skip, an
  orphaned judge input, a degraded judge panel) and 0 only on a clean run; 1 stays reserved for
  bad input or a missing engine. (PR #77 review; closed by the eval-CLI-honesty wave.)
- 2026-07-03, eval orphan judge inputs. score and judge iterated the ingested traces and looked
  up judge inputs by trace id; a judge input whose trace was dropped at ingest was never
  visited, counted, or warned, so this direction could hide a malformed trace silently. Closed
  by the eval-CLI-honesty wave: score and judge now count judge inputs with no matching trace
  and add a warning when any exist, which also trips the exit-2 contract above. (PR #81 review;
  closed by the eval-CLI-honesty wave.)
- 2026-07-03, eval gold-input validation. guides-score checked only that answer_key_root and
  guide_library were directories; content errors surfaced late, at the first read inside the
  engine, not at argument-parsing time. Closed by the eval-CLI-honesty wave: both gold inputs
  now load before staging or scoring starts, so a bad answer-key or guide-library directory
  fails fast with the same clean KitInputError naming the directory, instead of surfacing
  mid-run. (Post-eval repo review; closed by the eval-CLI-honesty wave.)
- 2026-07-02, eval CLI error mapping. `python -m kit.eval` caught every ValueError and printed
  it as `error: ...` with exit 1, the style reserved for bad user input, so an engine ValueError
  (a malformed trace, a bad judge response) was indistinguishable from a bad flag and its
  traceback was lost. Closed by the eval-CLI-honesty wave: KitInputError is now the kit-side
  validation channel (score/replay's shared parameter gate, guides-score's directory checks),
  and the CLI catches only `EngineNotFound | KitInputError`, so any other exception propagates
  with its traceback. Replay's `times`/`baseline` checks were converted in the same wave.
  (PR #77 review; closed by the eval-CLI-honesty wave.)
- 2026-07-02, eval CLI flag duplication. `--run-dir`, `--producer`, and `--sample` were defined
  per subparser, four times once the judge verb landed. Closed by the shared parent parser that
  the judge verb introduced; `--dims`/`--judge` stay on the scoring verbs only.
  (Opened by PR #77 and guides-score reviews; closed by the judge-verb PR.)
- 2026-07-03, doc command-list completeness. doc_truth checked that backticked refs resolve, not
  that lists are complete: the README plugin table sat at 3 of 6 commands with the gate green.
  Closed by the new `command_lists` gate check, which fails when a shipped plugin command is
  missing from README.md or docs/when-to-use.md. (Post-eval repo review; closed by the
  command-list-gate PR.)
