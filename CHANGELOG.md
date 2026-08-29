---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-08-27
---

# Changelog

Format follows Keep a Changelog (https://keepachangelog.com). The kit uses SemVer.

## [Unreleased]

### Added

- A Windsurf adapter: `python install.py --tool windsurf` installs an always-on rule at
  `.windsurf/rules/outpost.md` and the prompts as workflows at
  `.windsurf/workflows/outpost-<name>.md`, run as `/outpost-<name>`.
- A Gemini CLI adapter: `python install.py --tool gemini` installs `GEMINI.md` and the prompts
  as custom commands at `.gemini/commands/outpost/<name>.toml`, run as `/outpost:<name>`.
- A drift benchmark under `benchmarks/drift/`: five seeded drift scenarios per adapter, scored
  by `--verify`, `git status`, and copying by hand; `results.json` holds the published rows and CI
  re-runs them with `python benchmarks/drift/run.py --check`.
- `--verify` reports `EDITED` for a guide the kit wrote (`CLAUDE.md`, `AGENTS.md`, and the
  rest) whose bytes no longer match the manifest's `kit_hash`, with a one-line `NOTE:` count.
  The guide is the user's, so the exit code is unchanged.
- `--source <dir>` (repeatable) installs a skill library the kit does not own, a clone in the
  Agent Skills layout such as obra/superpowers, next to the core prompts for every tool. The
  manifest records the source, `--verify` reads each installed copy against the source's
  current state, and a user's own skill of the same name is never overwritten. See
  `docs/sources.md`.

### Changed

- The README leads with the drift benchmark: a headline rendered from
  `benchmarks/drift/results.json` inside a generated span, a transcript of `--verify` catching
  an edited copy and an edited guide, and a redrawn `docs/brand/flow.svg` showing install and
  verify across the six tools. The purpose, architecture, and consumer prose moved out; the
  working-habit lists moved to `docs/workflow.md`.

## [0.1.0] - 2026-08-27

### Added

- The core pack: twenty-eight prompts, one per step from first repo read to handoff, with a
  scrutiny set (`grill`, `self-refute`, `premortem`, `prove`, `panel`) around them.
- `install.py`: installs the pack for Claude Code, Codex, Cursor, and GitHub Copilot into a
  project, with `--dry-run`, `--only` and `--exclude` subsets, `--verify`, `--prune`, and
  `--remove`. It never overwrites a file you own and never writes outside the project.
- `validate.py`: twenty-three checks that prove the kit's own tree (catalog, prompts,
  templates, adapters, docs, generated spans, secrets, voice, labels, issue forms).
- A Claude Code plugin (`plugins/outpost/`) with the prompts as skills, nine commands, one
  read-only agent, one context hook, and one output style.
- Behavioral evals for nine prompts under `evals/`, opt-in and outside CI.
