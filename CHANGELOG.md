# Changelog

Format follows Keep a Changelog (https://keepachangelog.com). The kit uses SemVer.

## [Unreleased]

### Added

- ADR-0013 (proposed): prompt 26 and beyond needs an admission record naming the distinct job,
  nearest sibling, unsafe default, binding mechanism, dogfood case, and deletion condition
  (audit ruling 1). Awaits the owner's acceptance.
- `docs/cadence.md`, the contribution-cadence standard: two profiles (team-led and solo repos),
  the evidence behind each number, tips for agent-heavy teams, and the points the evidence does
  not settle. The docs gate now requires it.
- A `traces` gate check that blocks a personal email, handle, home-directory path, or sync-estate
  path from the tracked tree (ADR-0012). The allowed homes are CODEOWNERS, the append-only
  records, and the check's own pattern list.
- The `prompts` gate check now validates every prompt's frontmatter as flat YAML `key: value`
  metadata (audit F3): an unquoted colon inside or at the end of a value, an unterminated quote,
  or a value opening with a YAML indicator fails the gate, since a host parsing real YAML drops
  the whole frontmatter on such a file.
- The `voice` gate check now rejects any non-ASCII character in tracked markdown (audit F24),
  so the plain-ASCII rule is machine-checked instead of review-only. Em and en-dashes and the
  banned-word list keep their named errors; the general scan catches everything else and reports
  the offending codepoints.
- Decision 0014, recording the seven accepted pack-consolidation rulings from the Phase 1
  audit, including the two kept-pair negatives (`simplify` with `refactor-safely`,
  `self-refute` with `grill`) and each ruling's falsifier.

### Changed

- Consolidated the usage docs: `docs/workflow.md` is now the single hub (ordered path,
  Claude Code shortcuts, prompt table); `docs/when-to-use.md` was retired into it; the
  README leads with a recipe and a pointer. The point-in-time audit moved to
  `docs/audit/2026-07-10.md`.

### Removed

- `deassume`, which shipped only in this unreleased cycle. Its unique passes live on as
  `repo-review`'s ownership lens; the pack returns to twenty-four prompts (pack ruling 3,
  decision 0014).

### Fixed

- A prompt file the kit installed for a host it no longer ships to (a `converge.md` on a manual
  host from an earlier version, or a mid-cycle `deassume.md`) is no longer invisible to the
  recovery paths, which derived everything from the current plan: `--verify` reports it as a
  named LEFTOVER instead of in sync, and `--prune` and `--remove` delete it on the manifest's
  kit-created record, printing "retired from this host". A file recorded as pre-existing, or
  with no record at all, is the user's and stays protected exactly as before. A completed
  prune also drops the path's manifest record, so the ended ownership claim can never seize
  a file the user later creates at the retired path.
- `--only` with a prompt that does not ship to the chosen tool now warns and names the tool
  instead of silently installing nothing for that prompt.
- `write-doc` now requires the template as an input (so its check-against-the-template step can
  always execute) and narrows to the named coding artifacts its own body uses as examples, a
  README, a findings note, or a report; the "or other" catch-all is gone, and one boundary line
  each routes decisions to `record-decision`, shortcuts to `debt-log`, PR text to `prepare-pr`,
  and session state to `handoff-session` (pack ruling 7, decision 0014, resolving part of
  audit F20).
- `converge` has one definition of clean (audit F15): zero blockers and zero majors after a
  full check run. Its description now matches its steps, and a confirmed minor is reported,
  not required to be fixed and never a bar to clean (pack ruling 6, decision 0014).
- `panel` keeps its contract (conflicts are the finding; one recommendation naming the accepted
  trade-off and the overridden view) but no longer requires parallel execution: running the
  views in parallel is a strengthener on hosts with subagents, and the sequential fallback
  writes each view before reading the previous ones back and names its mode in the report,
  since sequential independence is an intent, not a proof (pack ruling 5, decision 0014).
- `prove` no longer turns uncertainty into refutation (audit F16): an unsure refutation attempt
  routes the claim to UNKNOWN and names the measurement that would decide it, and REFUTED
  requires a concrete break (a recomputation that disagrees, a contradicting source, or a
  failing check). The parallel-agent fan-out is now an optional strengthener on hosts with
  subagents; the default is a sequential single-agent path where attempts count as independent
  when they use different methods, keeping the two-refutation bar for CONFIRMED (pack ruling 4,
  decision 0014).
- `simplify`'s handoff to `refactor-safely` is now a testable threshold instead of "too large
  for this pass": a cleanup routes out when its reshape would change a test, alter a public
  contract, or grow past the diff under review (pack ruling 1, decision 0014).
- `docs/brand/flow.svg` no longer calls the pack skills for all four tools (audit F31). The
  caption now says the prompts are the pack and Claude installs them as skills, matching the
  prompt-versus-skill vocabulary the README uses.
- The installer no longer treats a reserved path or matching bytes as proof of kit ownership
  (audit F2). The manifest records, per path, whether a file existed before the kit first wrote
  there (the pre-install hash stored alongside is a forensic record for later inspection, not
  part of the ownership decision); a first install skips a pre-existing file with a
  named warning instead of overwriting it and records the skip; `--remove` and `--prune`,
  including the legacy Cursor sweep, delete only what the manifest or a byte match against the
  kit's own content proves the kit created. A manifest from an older kit falls back to the old
  byte-match removal rule.
- The stale-terse check warns on stderr when the Claude settings file is malformed instead of
  skipping it silently; the skip itself stands, and nothing is rewritten.
- `--remove` no longer deletes a pre-existing `.claude/settings.json` that is byte-equal to the
  kit's merged output. The manifest now records whether the settings file existed before the kit
  first touched it, and removal deletes the emptied file only when the kit created it; a
  pre-records manifest keeps the old delete-when-emptied rule.
- A stale `outputStyle` key whose style file is already gone is no longer invisible: when the
  recorded Claude install is non-terse, `--verify` flags a lingering kit-set key as DRIFTED
  (naming the key, style file present or not) and a plain reinstall retries the clear, so a
  missed withdrawal cannot keep restyling the agent silently.
- A plain reinstall no longer deletes a hand-placed terse output style that happens to be
  byte-identical to the kit's (nor clears the user's own `outputStyle` key). Terse ownership is
  proved by the manifest record alone: the prior entry's terse flag, or a kit-created file record
  at the style path. A byte match never claims ownership.
- A full reinstall over a subset install recorded by a pre-records manifest (one without the
  `files` map) no longer claims kit ownership of every path in the new plan. The fallback's claim
  is scoped to the paths the recorded entry itself derives (its prompts, guide, and terse flag);
  a file already on disk outside that footprint is recorded as the user's and skipped with a
  named warning, so a later `--remove` can never delete it.
- `converge`'s description no longer carries an unquoted colon (audit F3), so its generated
  Claude skill has valid YAML frontmatter again and loads by description instead of losing all
  its metadata.
- Reinstalling Claude without `--terse` after a terse install now withdraws the terse choice
  completely (audit F32): the kit's output-style file is removed (an edited one is kept and
  named) and the kit-set `outputStyle` key is cleared, and `--verify` flags leftover terse state
  as DRIFTED instead of passing a non-terse install that still restyles the agent. The withdrawal
  also drops the manifest's style-path record, so the kit's ownership claim ends with it instead
  of lingering forever; without that, a later hand-adopted style with the kit's own bytes and the
  user's own key would be seized (deleted and cleared) by the very next plain reinstall.
- `--prune` no longer reports a deleted legacy Cursor file as FAILED (and no longer exits 1)
  when the file itself was removed and only the empty-parent-dir cleanup raised; the same split
  keeps the state-dir migration's "could not remove the legacy manifest" warning to the case
  where the manifest itself could not be deleted.
- The `/code-review` command file and `docs/plugin.md` now name the verdict set the core prompt
  actually uses: approve, comment, or request changes.
- The `docs/when-to-use.md` job table now carries all shipped prompts; `converge`,
  `record-decision`, `debt-log`, and `write-doc` were prose-only before.
- The plugin and marketplace author field is the org with no email; a personal address had been
  shipping as the kit's contact on every install (ADR-0012).
- The plugin and marketplace descriptions say "the plugin commands" instead of a command count,
  so the generated prose cannot drift when a command is added.
- `--prune` and `--remove` now sweep the pre-rename Cursor rule (`.cursor/rules/agi-coding-kit.mdc`
  and its prompt dir), so a project installed before the v0.24.0 rename self-heals instead of
  keeping both rule sets on disk.
- The state-dir migration's legacy-manifest cleanup now warns on stderr instead of silently
  swallowing the OSError when the old `.agi-coding-kit/manifest.json` cannot be deleted; the
  install still succeeds.
- `docs/brand/flow.svg` no longer carries a prompt count as SVG text, so it cannot drift from
  the docs the way it did before the v0.25.0 review caught it.
- `docs/workflow.md` now names `repo-review`, `simplify`, and `triage` in the flow narrative,
  closing the gap the first repo-review dogfood run found.
- `kit/plugin.py`'s plugin and marketplace descriptions now say "the ledger-voice output
  style" instead of "a terse output style", matching the style actually shipped.
- `docs/ROADMAP.md`'s Docs row now names all twelve shipped docs, including `token-budget.md`
  and `dogfooding.md`.
- Removed the dead `tests/fixtures/eval` fixture, an unreferenced leftover of the ADR-0009
  eval removal.
- Doc truth, from the 2026-07-10 audit: the README opens by naming the kit internal to the AGI
  team and points at CODEOWNERS as the maintainer roster; the quick start clones the kit and
  installs into a consumer repo instead of the kit checkout; the docs separate the kit source
  gate (`python validate.py`) from consumer install verification (the installer's `--verify`),
  and the ROADMAP's proof claim shrinks to packaging and parity; plugin commands are named by
  their invocable `/ack:<name>` form in the shipped doc tables, the local plugin install recipe is the
  supported marketplace path, and the `command_lists` check now requires the namespaced form;
  the Codex and Copilot overlay notes match the eight-prompt guides; the workflow's read-only
  list names the two prompts that write and `interrogate` is the named upstream exception; the
  contributor and release recipes carry the regeneration and final-gate steps they omitted; the
  voice-check sentence and three token-budget tags claim only what their evidence supports; the
  Copilot tool row names its supported IDE integrations; the ROADMAP and workflow say a human
  opens and merges the PR; ADR 0012 joins the decisions index.

### Changed

- `repo-review` gains an opt-in ownership lens for a one-person repo becoming a team surface:
  the personal-trace grep, the allowed-homes input, and the generated-surface pass, carried
  over from the unreleased `deassume` prompt it replaces (pack ruling 3, decision 0014).
- `converge` ships to Claude Code only (pack ruling 6, decision 0014). The catalog prompt
  entry gains an optional `hosts` field, honored by the shared prompt loader, so every
  adapter, the plugin builder, and the install manifest agree; the Codex, Cursor, and Copilot
  installs carry 23 of the 24 prompts, and `--verify` never reports the missing one.
- The context-nudge threshold variable is renamed to `ACK_NUDGE_BYTES` (audit F31). The old
  `AGI_KIT_NUDGE_BYTES` name still works as a fallback and the new name wins when both are set;
  `docs/plugin.md` now names the variable and its default.
- Docs say prompt where they mean the artifact: the README table heading is now "The prompt
  pack", and contributing, ROADMAP, and dogfooding prose follow the same ruling; "skill"
  stays for the Claude-installed form. dogfooding.md gains a dated note naming the retired
  prompts (closing the DEBT entry), and decisions/README now says supersede, never delete.
- `repo-review`: numbered findings (F1, F2, ...) for triage to key on, a three-value
  confidence tag (verified, proposed, unknown), a docs-truth priority (README and install
  claims first), and read-only scope and output destination named in the inputs.
- `triage`: routing now runs against the caller's own bar for fix now, with severity
  deciding order rather than gating a finding out; the counts line now carries the severity
  breakdown of the confirmed findings.

## [0.25.0] - 2026-07-09

### Added

- The review suite (ADR-0011): three new core prompts (`repo-review`, a whole-repo health
  audit; `simplify`, behavior-preserving cleanup of changed code; `triage`, rank and route a
  findings list) and five commands (`/repo-review`, `/code-review`, `/simplify`, `/prove`,
  `/triage`).

### Changed

- `review-change` renamed to `code-review` so the prompt and its command share one name.

## [0.24.0] - 2026-07-09

### Changed

- The kit is ACK (AGI's Coding Kit), matching the renamed repo agi-inc/ACK (ADR-0010). The
  plugin renames to `ack`, so its commands surface as `/ack:*`. The distribution name is
  `ack`; the Python package stays `kit`.
- The installer state dir moves from `.agi-coding-kit/` to `.ack/`. An install over a repo
  with the old dir migrates the manifest and removes the old dir when it is then empty; reads
  fall back to the legacy path until then.

## [0.23.0] - 2026-07-09

### Added

- A `command_lists` gate check: every plugin command file under
  `plugins/agi-coding-kit/commands/` must be named in both README.md and docs/when-to-use.md.

### Changed

- The plugin output style is `ledger-voice`, renamed from `no-blab`: findings first, claims
  tagged, extreme concision. The style file names the banned words to ban them, so it joins
  the voice check's exemption set.
- Distill to a pure coding kit: remove the eval, guides, device, and ops domains; core returns to
  21 cross-tool coding-discipline skills.

### Removed

- The eval front door (`kit.eval`) and its `eval_isolation` gate check. The gate holds at 16 checks:
  `command_lists` added, `eval_isolation` removed.

## [0.22.0] - 2026-07-04

### Added

- A run-from-clone eval front door: `python -m kit.eval score --run-dir R --dims {1,4}` scores
  stored traces through a sibling touchstone checkout (DIMS1 is task pass/fail; DIMS4 adds safety,
  efficiency, and context), with honest abstention, visible trace skips, `--out` rows, and
  `--cards` score cards. `python -m kit.eval replay` re-scores stored traces under the current
  verifier config, checks judge determinism across `--times N` runs, and diffs verdicts against a
  prior `--baseline` rows file. Score-only: the live device rerun stays in agi-lab.
- `python -m kit.eval guides-score` scores a stored run on the four guide seams (retrieval,
  fidelity, adherence, outcome) with per-seam abstention, broken-seam attribution, paired uplift,
  provider-error exclusion made visible, and optional gold inputs (`--answer-key-root`,
  `--guide-library`). Deterministic at scoring time: no judge flag, no key, no cost note.
- `python -m kit.eval judge` runs the judge panel over a run of stored traces and reports, per
  trace, the folded verdict plus each panel member's vote (model, verdict, confidence, why),
  with `--out` rows JSON. A calibration view of the judge, not a scoring path: no dimensions,
  no cards. The shared CLI flags (`--run-dir`, `--producer`, `--sample`) moved to one parent
  parser across all four verbs. A run where every panel member errored is flagged with a
  run-level warning, and a panel/vote length drift fails loud instead of mislabeling votes.
- ADR-0008 records the eval front door (`kit.eval`: score, replay, judge, guides-score) as a
  quarantined leaf that reverses ADR-0001's "No eval, no judge" scope; the core package and
  installer stay stdlib-only.

### Changed

- `python -m kit.eval` exit codes are now honest about partial runs: 0 on a clean run, 1 on bad
  input (including usage errors, which previously exited 2, and a nonexistent run dir on every
  verb), 2 when the run completed with warnings (a trace skip, an orphaned judge input, or a
  degraded judge panel). Engine errors other than a kit input error now propagate with their
  traceback instead of being swallowed as an `error:` line. `replay`'s `times`/`baseline` checks
  route through the same clean input-error path. `score` and `judge` count judge inputs that have
  no matching ingested trace and warn when any exist. `guides-score` loads its gold inputs before
  staging, so a bad answer-key or guide-library directory fails fast.
- The eval and guides prompt example fences now name only real, verified surfaces: the
  scoring fences run `python -m kit.eval score|replay`, the promotion gate shows
  touchstone's real candidate-vs-baseline shape, and every capability without a shipped
  CLI is labeled pseudocode instead of a fake command. score-run now documents which
  dimensions can score on which inputs, so an all-abstain result reads as expected.
- Simplified prose that the v0.21.0 pass missed: repo guide headings, the writing standard intro,
  plugin commands, plugin agents, the no-blab output style, and `premortem`.
- The ROADMAP's current-state counts (the checks line, the core-prompt count, and the plugin
  skill/command counts) are now generated from the catalog via `docs_sync`, not hand-copied, so
  they cannot drift the way the checks line silently did.
- README and onboarding now lead with the tool-neutral core and present the Claude-only domain
  packs as a labeled "team extension", so the front matter no longer implies four-tool parity.
  ADR-0007 records the decision.

### Fixed

- Updated stale adapter and plugin wording in package metadata and ADR notes so they name GitHub
  Copilot, the shipped plugin channel, and the shipped domain packs.
- Post-eval docs-truth wave: the README quick-start comment now prints the real `16/16` gate
  count, the README and docs/when-to-use.md name all six plugin commands (not three), the eval
  pack fences name the `judge` verb and the `--producer` flag, and `interrogate`, `premortem`,
  and `review-change` moved to the catalog stage their own prompt bodies claim.
- Post-eval code-findings wave: `guides-score` answer-key load errors now fail clean naming the
  directory, like the guide-library path already did. Judge summaries flag a partial panel
  (some but not all votes dropped) and a decided trace that lost a panelist, and a decided
  verdict with zero real votes now raises instead of silently reading as split. `--dims` and
  `--judge` document their choices in `-h`. The held-out guard hook no longer blocks reading or
  editing its own source file.

## [0.21.0] - 2026-07-01

### Changed

- Prose across the README, docs, prompts, templates, and generated plugin skills simplified to the
  writing standard. Meaning, paths, command names, flags, code spans, and prompt contract sections
  are preserved; only the wording changed.
- The README Skills table and the prompt/domain/skill counts in README.md, docs/when-to-use.md,
  and docs/plugin.md are now generated from the catalog (`kit/docs_build.py`, the `docs_sync`
  gate check, `python tools/build_docs.py`), not hand-copied. `counts.py` and `fixture_sync.py`
  are retired; `doc_truth.py` and `plugin_sync.py` lose the scope `docs_sync` now covers. The
  gate is 15 checks (was 16).

### Fixed

- The install manifest now records only the prompts a tool actually installed (core plus that
  tool's opted-in domains), not every catalog prompt name. A full core-only install previously
  over-recorded all domain prompts too, so `--verify`/`--prune` could hard-error for a core-only
  user after a future domain-prompt rename or drop. An existing installed project should re-run
  install to refresh a manifest written before this fix.
- `python validate.py` no longer crashes with a traceback on a malformed catalog file; it now
  reports a clean `[FAIL] catalog: ...` line like every other check.
- `check_task_schema`'s hook docstring no longer claims the kit repo "dogfoods" its own task
  schema validation; no repo, including this one, vendors the contract module the claim depended
  on, so the hook is advisory-only everywhere today.
- The prompt lint now requires a real H1 heading; a body with only H2 or deeper headings was
  accepted before, because the substring test matched `## ` too.
- The `doc_truth` scan of `docs/domains.md` reads only the prompt-name table column, so a
  backtick-quoted group name in prose no longer trips a false "not a catalog prompt" error.

## [0.20.2] - 2026-06-30

### Fixed

- Corrected `docs/releasing.md`: the GitHub release title is the plain `vX.Y.Z`, not the summary form (v0.20.1's entry reconciled it backwards). All GitHub release titles were normalized to `vX.Y.Z`.

## [0.20.1] - 2026-06-30

### Added

- ADR-0006 records the maintainer-review-gate decision (CODEOWNERS and branch protection on the kit's own repo); the decisions index now also lists ADR-0005.

### Fixed

- `docs/releasing.md` now matches practice: a feature PR only adds to `[Unreleased]` (no version bump), a release PR batches the accumulated changes, and the GitHub release title is `agi-coding-kit vX.Y.Z: <summary>` (step 7 had said the plain `vX.Y.Z`).

## [0.20.0] - 2026-06-30

### Added

- `.github/CODEOWNERS` naming the maintainers, so a pull request routes a review request to them.
- `templates/README.md` explaining the per-tool guides, and a `templates_sync` gate check that fails when a committed guide drifts from the shared core.
- `docs/dogfooding.md`: an append-only ledger of findings from dogfooding the kit's skills on real work.
- A `device` domain pack (Claude-only, opt-in with `--with-domain device`): `harvest-reset-booklet`, `write-device-task`, `reset-device`, `replay-run`, `pull-traces`, encoding the on-device eval loop and the per-app reset booklet. Domain prompts go from 18 to 23.
- The `device` pack gains its self-heal loop: `triage-reset`, `heal-reset-booklet`, and `reset-watch`, mirroring the guides heal/watch loop for reset booklets. The pack goes from 5 to 8 prompts; domain prompts to 26.

### Changed

- `main` now requires one maintainer approval to merge. The `secrets` gate no longer bans a CODEOWNERS file, since the kit now ships one for its own repo.
- The four guide templates now share one core (`templates/_src/core.md`) built per tool by `tools/build_templates.py`, so their common working-agreement and prompt-list content cannot drift (#51).
- `plan-change`, `implement-change`, and `review-change` each gain a step from dogfooding: check a change against the repo's own gates and rules, stay within version floors with portable output, and review portability and self-consistency.
- `sync-slack` now leaves a Slack draft for the user to send by default, sending directly only on an explicit instruction; previously it sent after an in-chat confirmation.
- The guides serve path gates the live push: `serve-guides` confirms the target runtime and spec count, `heal-guides` inherits the gate, and `guides-watch` treats its schedule as standing consent with cross-run issue dedupe.
- `export-training-data` now confirms the destination and counts, refuses to overwrite a batch, and warns before exporting a held-out run.

### Fixed

- `tools/build_plugin.py` now writes generated files as bytes with LF line endings, so a rebuild on Windows no longer churns the committed plugin tree. Mirrors `tools/build_templates.py`.

## [0.19.0] - 2026-06-29

### Added

- Three `guides` domain prompts that close the rerun/fix/self-heal gap: `triage-guide` (classify the first broken layer when a guide fails to serve, anchor, or confirm), `heal-guides` (re-crawl, regenerate only the drifted specs, re-serve, escalate coverage loss to `write-task`), and `guides-watch` (the scheduled cron skill: serve-check live guides, heal anchor and schema drift, escalate the rest). The `guides` pack goes from 3 to 6 prompts; domain prompts total 18.

## [0.18.0] - 2026-06-29

### Added

- Two read-only plugin agents: `architecture-guardian` (checks a change against the repo's decision records and rules, flags drift) and `pipeline-auditor` (reports the first invalid stage of an eval run, or a stage-contract violation in an eval/guide PR).
- `no-blab` output style: terse, lead-first output; toggle with `/output-style`.
- `docs/token-budget.md`: context-budget guidance for large-file reads and subagent offloading. Completes the salvage of agi-claude-kit's unique assets.

## [0.17.0] - 2026-06-29

### Added

- Three Claude plugin commands: `/doctor` (environment and gate check; runs `python validate.py`), `/eval` (frozen held-out eval runner), and `/session-loop` (eval dev loop: write-task -> run-eval -> score-run -> triage-run). Completes the port of agi-claude-kit's plugin commands alongside the existing `/stress`, `/ship`, and `/drive`.
- Four plugin hooks in `plugins/agi-coding-kit/hooks/`, loading automatically on install: `block_held_out` and `guard_external_send` are hard guards (fail-closed); `check_task_schema` and `nudge_context` are advisory. Core stays at 21 prompts plus 15 domain prompts; this adds plugin commands and hooks only.
- A `roadmap` gate check that fails when the ROADMAP current-release line does not match the kit version.

## [0.16.1] - 2026-06-29

### Fixed

- `--verify`, `--prune`, and `--remove` now account for installed Claude-only domain prompts. Before, a domain ever installed with `--with-domain` was invisible to all three: `--remove` left the domain skills orphaned, and `--prune`/`--verify` missed them. The maintenance modes now compute the full kit footprint over all catalog domains and read the manifest's recorded `opted_in_domains` as the expected set, so a domain skill is removed, pruned, and integrity-checked like a core one.

## [0.16.0] - 2026-06-29

### Added

- 15 Claude-only domain prompts in three functional groups: `eval` (8: write-task, run-eval, score-run, replay, triage-run, check-holdout, export-training-data, gate), `guides` (3: crawl-app, generate-guides, serve-guides), `ops` (4: sync-slack, file-issue, digest, summarize). Opt in with `--with-domain <name>`; the cross-tool installer skips them.
- `docs/domains.md`: reference for the domain packs, their prompts, and opt-in instructions.

### Changed

- The `prompts` lint and a new fixture now cover domain prompts; `doc-truth` checks the `docs/domains.md` surface. Core is unchanged at 21 cross-tool prompts.
- README reframed as AGI Coding Kit: a clearer title and description, a Quick start with example commands, a Best practices section (tokens, errors, parallelizing), and a refined flow figure. Docs only, no functional change.

## [0.15.0] - 2026-06-29

### Added

- Domain-group engine: catalog prompts now carry a `group` field, either `core` (cross-tool default) or `domain:<name>` (Claude-only, opt-in). The engine exposes `core_prompts`, `domain_prompts`, and `domain_names` accessors on the catalog and threads domain filtering through adapters and checks.
- `--with-domain <name>` install flag to opt a tool into a named domain pack.
- The manifest now records `opted_in_domains` per tool, so `--verify`, `--prune`, and `--remove` all see the opted-in set without re-passing the flag.
- ADR-0005 documents the domain-group design decision.

### Changed

- The `counts` check now also covers `docs/when-to-use.md` and `docs/plugin.md` (previously only `README.md` and `docs/adapters.md`). The counts, doc-truth, and fixture-sync checks split core from domain totals.
- No prompt set changed in this release: the kit shipped 21 core prompts and no domain prompts.
  Domain packs landed later, starting in v0.16.0.

## [0.14.0] - 2026-06-29

### Added

- Six prompts added to core: `prove` (multi-source claim verification with adversarial recomputation and a confidence verdict), `panel` (parallel expert-lens synthesis with one adjudicated recommendation), `converge` (lint-test-review loop that runs until clean or a round cap), `record-decision` (architecture decision record scoped to one decision), `debt-log` (deliberate shortcut entry with reason, cost, and revisit trigger), and `write-doc` (findings-first deliverable from a house-voice template).

### Changed

- `prepare-pr` now also covers the standalone commit and PR-draft cases in addition to the full pre-merge sequence.
- `handoff-session` now also covers mid-task re-grounding and not only end-of-session handoffs.
- `docs/releasing.md` now includes the plugin regenerate step (`python tools/build_plugin.py`) in
  the release checklist and corrects the stale "no generated files committed" claim (the plugin tree
  is generated and committed, kept in sync by `plugin_sync`). `docs/adapters.md` notes that the
  manifest records `terse`.

## [0.13.2] - 2026-06-29

### Fixed

- The `--terse` output style is now recorded in the manifest, so `--verify`, `--prune`, and
  `--remove` handle `.claude/output-styles/terse.md` and the `outputStyle` key without re-passing
  `--terse`. Previously `--remove` left the style file behind with a dangling `outputStyle: "terse"`
  pointing at it, and `--verify` could not see the file. `--remove` strips a `terse` output style
  only when the kit's deny rules were also present, so it never touches a settings file you wrote.

### Changed

- The README install section now surfaces the subset-install (`--only`/`--exclude`) and
  `--verify`/`--prune`/`--remove` flags, catching the storefront up to the shipped installer.

## [0.13.1] - 2026-06-29

### Added

- `--verify` notes when an install was recorded at a different kit version than the one running
  (older or newer), suggesting a re-install to refresh it. The files may still be in sync, so the
  note never changes the verdict or the exit code.

## [0.13.0] - 2026-06-29

### Added

- `--remove`: uninstall the kit for a tool. Deletes its kit-owned prompt files and, only if still
  unmodified, the guide it created; un-merges the kit's secret-deny rules from `.claude/settings.json`
  (removing the file only if nothing of yours remains); drops the tool from the manifest. An edited
  file is kept and reported, so a customization is never lost. `--tool all` removes every tool.

## [0.12.1] - 2026-06-29

### Fixed

- `--verify` and `--prune` now reject a manifest that names a prompt this kit does not ship (a
  hand-edit typo or a cross-version file). Without this, a typo'd name silently dropped a real
  prompt from the selection and `--prune` deleted it as an orphan; validation runs before any
  deletion, so a bad name fails loudly and touches nothing.

## [0.12.0] - 2026-06-29

### Added

- `--prune`: remove orphan prompt files left on disk after a narrower re-install (the `EXTRA` set
  `--verify` reports). It deletes only kit-owned prompt files the manifest no longer selects, never
  a user-owned or merged file, and skips a hand-edited orphan so a customization is never lost. A
  file it cannot delete is reported, not fatal. Full uninstall stays out (a later `--remove`).

## [0.11.1] - 2026-06-29

### Added

- `--verify` flags orphan prompt files: kit-owned prompts left on disk after a narrower re-install
  (`--only`/`--exclude` over a broader install) are reported as `EXTRA` and fail verify (orphans are
  drift). The installer still does not delete; pruning is tracked for a later `--remove`.

## [0.11.0] - 2026-06-29

### Added

- `--only` and `--exclude` on the installer to install a subset of the prompt pack; the full pack
  stays the default.
- An install manifest (`.agi-coding-kit/manifest.json`) recording the kit version and the prompts
  installed per tool; `--verify` reads it to check the installed subset.

### Changed

- Tightened every doc to a cheat-sheet register and fixed the ROADMAP's stale v0.1.0 framing.

## [0.10.0] - 2026-06-29

### Added

- A Claude Code plugin channel (`plugins/agi-coding-kit/`): the fifteen prompts as plugin skills
  plus three composite commands. `/stress` routes to the right scrutiny prompt by target and
  intensity (interrogate, self-refute, grill, premortem). `/ship` runs the pre-merge bundle
  (self-refute, review-change, prepare-pr) and stops on a blocker. `/drive` walks a change from
  plan to tests (plan-change, implement-change, write-tests) and hands off to `/ship`. Install
  with `/plugin marketplace add agi-inc/agi-coding-kit` and `/plugin install agi-coding-kit`.
- A `plugin_sync` gate check (the fourteenth): the committed plugin tree must match the generator
  output, the manifest version must agree with the catalog, and every command file must name only
  real catalog prompts. Run `python tools/build_plugin.py` after a prompt or version change.
- `tools/build_plugin.py`: thin writer script over `kit.plugin.build_plugin`; regenerates the
  committed plugin tree from the catalog.
- `docs/plugin.md`: install instructions and description of the plugin channel.

## [0.9.3] - 2026-06-29

### Changed

- The README and docs are tightened for concision and the README skills are regrouped into an
  agi-claude-kit-style catalog (grouped `Skills | Use them to` tables). The when-to-use guide is
  trimmed to a single spine pass. Facts and prompt and tool coverage are unchanged.
- The `doc_truth` check now reads the README prompt set from the grouped `## Skills` catalog
  (every backtick prompt token in the section) rather than the last column of a single table, so
  the catalog can be grouped however reads best without breaking the check.

## [0.9.2] - 2026-06-28

### Added

- A `docs/when-to-use.md` guide that routes a reader to the right prompt by what they are doing,
  mapping the fifteen prompts onto a six-stage spine plus a cross-cutting scrutiny lens. It is a
  gated required doc, and its backtick prompt references are checked against the catalog the same
  way `docs/workflow.md` already is, so a renamed prompt cannot leave a stale reference behind.

## [0.9.1] - 2026-06-28

### Changed

- The README is shortened and each supported tool now gets its own colored badge instead of one
  combined badge. The Install section and the tool and prompt tables are unchanged.

### Fixed

- The `doc_truth` check identifies the skills-table header by its first cell ("Group") instead of
  the literal last cell ("Skills"), so renaming the last column can no longer make the header parse
  as a prompt row.

## [0.9.0] - 2026-06-28

### Added

- A `fixture_sync` gate check (the thirteenth): the `EXPECTED` prompt-name set in
  `tests/test_prompts.py` must equal the catalog prompt names, both ways, so a renamed prompt cannot
  leave a stale test fixture green. Reads the set by AST, never importing the test. Scanning
  `tests/test_check_negatives.py` is deferred (it embeds deliberately-wrong test data); see ROADMAP.
- A `doc_truth` gate check (the twelfth): the user-facing docs name the same tools and prompts the
  catalog ships, both ways. Every catalog tool appears in the README and adapters tool tables, the
  README skills table lists every catalog prompt and only catalog prompts, and every backtick prompt
  reference in `docs/workflow.md` resolves to a real prompt. The inverse of `template_refs`, for docs.

### Fixed

- The voice check now scans only git-tracked markdown. Untracked scratch (an SDD brief, a local
  note) with an em-dash or a banned word no longer trips the gate. When not in a git repo it falls
  back to scanning every non-ignored `.md`, so a source tarball is still judged.

## [0.8.2] - 2026-06-28

### Changed

- The README is repositioned and tightened: it now leads with what the kit is (AGI's internal coding
  kit, installed into any assistant as skills) in the style of the sibling kits, and adds short
  "The workflow", "The skills", and "Best practices" sections so the recommended path and the
  discipline are visible on the page, not only in `docs/`. The facts are unchanged; the prompt and
  tool tables carry the same content.

### Fixed

- `docs/onboarding.md` and `CLAUDE.md` pointed readers to a README section "First 5 minutes" that the
  v0.8.1 rewrite had renamed. Both now point to the current "Install" section.

## [0.8.1] - 2026-06-28

### Changed

- The README is rewritten for a general reader: a centered header with badges, plain language about
  what the kit does and what you get, a quickstart, and an SVG diagram (`docs/brand/flow.svg`) of the
  flow. The install model and the prompt and tool tables carry the same facts as before.

## [0.8.0] - 2026-06-28

### Added

- A `--verify` installer mode: `python install.py --tool claude --project . --verify` checks an
  existing install against the kit and exits non-zero on drift or a missing kit file. It writes
  nothing, so it is safe to run in CI.

### Changed

- The README is now a storefront: CI/python/license badges, a "Why use it" value prop, a grouped
  prompt table, and an ASCII flow diagram. The quickstart uses one consistent install model
  (run from the clone, point `--project` at your repo), fixing the earlier `--project .` contradiction.
- `docs/workflow.md` now documents how GitHub Copilot loads the prompts, alongside the other three
  tools.
- The installer now warns before overwriting a kit-owned prompt you edited, instead of restoring it
  silently. It still restores the kit version; the `prompts/<tool>/` overlay is the supported way to
  customize a prompt.

### Fixed

- The installer compares the merged `settings.json` semantically (parsed JSON), so reformatting it
  or adding unrelated keys no longer triggers a spurious rewrite or a false `--verify` drift. A real
  change (a removed deny rule) is still caught.

## [0.7.0] - 2026-06-28

### Added

- Four scrutiny prompts (interrogate, grill, self-refute, premortem): interrogate hardens a vague
  request before plan-change, grill stress-tests a design or diff, self-refute red-teams your own
  fresh output, and premortem imagines a plan's failure before you commit. The prompt pack grows
  from eleven to fifteen, and they auto-ship to every adapter. See ADR-0002.

## [0.6.0] - 2026-06-28

### Added

- A `--list` flag for the installer: `python install.py --list` prints every prompt, template, and
  adapter the kit ships, then exits without writing anything.
- The installer prints a one-line outcome summary after an install (counts of created, updated,
  skipped, and unchanged files).

### Changed

- The README quickstart is now the single canonical fast path ("First 5 minutes"); onboarding points
  to it instead of repeating the steps.
- The ROADMAP "Where it stands" intro no longer accretes a sentence per release; it points to the
  changelog for version history.

## [0.5.0] - 2026-06-28

### Added

- A `template_refs` gate check: every prompt name a template spells out must resolve to a catalog
  prompt, so renaming a prompt cannot leave a dangling reference in a template.
- A `registries` gate check: the adapter and check registries in the catalog must match the code on
  disk, so a stray unregistered check module (which would silently never run) or adapter package
  fails the gate.

## [0.4.0] - 2026-06-28

### Added

- A `counts` gate check: the prompt total advertised in the README and onboarding must match the
  catalog, so a stale count (the kind a v0.2.0 review caught) fails the gate.

## [0.3.0] - 2026-06-28

### Added

- A fourth adapter, GitHub Copilot: installs `.github/copilot-instructions.md` (repo-wide custom
  instructions) and the core prompts as `.github/prompts/*.prompt.md` files. Disjoint paths, so it
  coexists with the Claude, Codex, and Cursor adapters.

## [0.2.0] - 2026-06-28

### Added

- Three core prompts: `orient-repo` (read-only map of an unfamiliar repo before planning),
  `respond-to-review` (triage review feedback, fix or push back, reply to each), and `split-change`
  (split an over-scoped change into focused, independently revertible units).

## [0.1.0] - 2026-06-28

### Added

- The eight core prompts: plan-change, implement-change, review-change, debug-failure, write-tests,
  refactor-safely, prepare-pr, handoff-session. Each names when to use it, its inputs, steps, output,
  and stop conditions.
- Three project templates: `CLAUDE.md`, `AGENTS.md`, and a Cursor repo rule.
- The installer (`install.py`): per-tool or `all`, with `--dry-run` and safe, idempotent merges. It
  merges the Claude settings file and never overwrites a file you own.
- Adapters for Claude Code (primary), Codex, and Cursor. They write to disjoint paths and coexist.
- The catalog (`kit/catalog/catalog.json`) as the source of truth, and the validation gate
  (`python validate.py`): structure, catalog parity, prompt completeness, template and doc health,
  adapter coexistence, secrets, and house voice.
- Docs: onboarding, the idea-to-PR workflow, the writing standard, the adapter model, contributing,
  releasing, and a roadmap that marks each item built, planned, or idea.
