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
