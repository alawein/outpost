---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-07-26
---

# Adapters

One prompt pack, four tools. The core prompts live in `prompts/core/`. Each adapter turns them into the files one tool expects.

## The model

An adapter is `plan(kit_root, project_root, terse=False)` returning a list of Actions. Each Action has a path, content, and mode:

- `write`: a kit-owned path, usually a prompt file. Overwritten with rendered content on every install.
- `create`: a user-owned path (`CLAUDE.md`, `AGENTS.md`, the Cursor rule, the Copilot instructions). Written only if absent.
- `merge`: a shared config file (`.claude/settings.json`). Content is the merged result.

The installer plans first, then prints (`--dry-run`) or applies. Both use the same path, so the preview is exact.

## What each tool gets

| Tool | User-owned (create) | Kit-owned (write) | Merged |
|---|---|---|---|
| Claude | `CLAUDE.md` | `.claude/skills/<name>/SKILL.md`, optional `.claude/output-styles/terse.md` | `.claude/settings.json` deny rules |
| Codex | `AGENTS.md` | `.agents/prompts/<name>.md` | none |
| Cursor | `.cursor/rules/outpost.mdc` | `.cursor/rules/outpost/<name>.md` | none |
| GitHub Copilot | `.github/copilot-instructions.md` | `.github/prompts/<name>.prompt.md` | none |

Paths stay separate across tools, so more than one install in the same repo does not collide. The `adapters` check proves this on every `python validate.py` run.

## Flags

- `--tool <name>|all` chooses the target tool; required for every install, verify, prune, or
  remove, unless `--list` is given instead. `--project <path>` chooses the target project
  directory; defaults to `.`.
- `--only <names>` / `--exclude <names>` narrow the pack to a comma-separated subset (mutually
  exclusive with each other); the full pack installs by default.
- `--dry-run` prints the plan and writes nothing.
- `--terse` also installs, and defaults to, the terse output style (Claude only).
- `--list` prints what the kit would install (prompts, templates, and adapters) and writes
  nothing; it needs no `--tool`/`--project`, since it describes the kit itself, not a target
  install.
- `--verify`, `--prune`, and `--remove` are mutually exclusive with each other and with
  `--list`/`--dry-run`; see their own sections below.

## The install manifest

Each install writes `.outpost/manifest.json` at the project root. It records the kit version and, per tool, which prompts were installed, how they were chosen (`full`, `only`, or `exclude`), and whether `--terse` was used. `--verify` reads that record and checks the installed subset, not the full pack. That keeps excluded prompts from being reported as missing. It also lets `--verify`/`--prune`/`--remove` handle the terse output style without re-passing `--terse`. Installing a second tool adds its entry without dropping the first.

The installer never deletes during a normal install. If you narrow an install (`--only`/`--exclude` over a broader one), the de-selected prompt files stay on disk. `--verify` reports them as `EXTRA`, and `--prune` removes them. Prune deletes only kit-owned prompt files the manifest no longer selects. It never deletes a user-owned or merged file, and it skips a hand-edited file. The manifest is the record, so edit prompt names carefully before pruning.

`--remove` uninstalls a tool. It deletes the kit-owned prompt files and the terse output style. It deletes the guide it created only if that guide is still unmodified. It removes the kit's deny rules from `.claude/settings.json` and removes the `outputStyle` the kit set. Your other keys stay. The settings file is removed only if nothing of yours is left. The tool entry is then dropped from the manifest. An edited file is kept and reported, so a customization is not lost.

## Differences that matter

- Only Claude Code loads skills by description, so its prompts load on their own.
- Codex has no skills or plugins here: plain files under `.agents/prompts/`, used by hand;
  `AGENTS.md` names the eight common stage prompts, not the full pack.
- Cursor reads rules, so prompts install as rules.
- Copilot reads `.github/copilot-instructions.md` repo-wide plus prompt files.
- Only Claude carries the settings merge and the optional terse output style. Deny rules cover secrets only.
- `converge` ships to Claude only: its catalog entry carries `hosts: ["claude"]`, which every
  adapter honors, so the Codex, Cursor, and Copilot installs carry every core prompt except it
  (decision 0014). The loop needs a host that runs checks and fixes on its own.
- Do not assume one tool supports another's features. Adapters add only files those tools already read.

## Overriding a prompt for one tool

Put a file in `prompts/<tool>/` with the same name as the core prompt to override it for that tool only. Keep overrides rare because they make tools differ. The overlay directories ship with only a README, and there are no overrides yet.

Editing an installed kit-owned file directly is not supported: a re-install restores the kit version after a warning. The overlay is the supported path.

## Adding an adapter

See `docs/contributing.md`.
