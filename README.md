# Outpost

[![ci](https://github.com/alawein/outpost/actions/workflows/ci.yml/badge.svg)](https://github.com/alawein/outpost/actions/workflows/ci.yml)
![license](https://img.shields.io/badge/license-MIT-2ea043?style=flat-square)

Status:      active
Category:    core
Owner:       alawein
Visibility:  public
Purpose:     Installs one prompt pack into six coding agents and verifies every installed copy still matches the source.
Next action: continue

## Purpose

Outpost installs one prompt pack into six coding agents (Claude Code, Codex, Cursor, Copilot,
Windsurf, Gemini CLI), then verifies every installed copy still matches the source. It is for
one person or a small team running several agents against the same repos who want to edit a
guide once, not six times. Unlike a hand-maintained rules file per tool, the verify step catches
a stale copy before it costs a wrong edit.

It is not a process plugin: a plugin such as superpowers decides how a task gets done, Outpost
decides what runs and proves the copies landed. It is not a sync tool for a rules file you
already wrote: the checks cover only what the kit installed.

- Lifecycle: active
- Verification date: 2026-08-31
- Scope: the installer, six tool adapters, drift verification, a Claude Code plugin, and the
  drift benchmark

Adoption beyond the maintainer is unproven: no sibling repo in this workspace has installed it
yet, and the benchmark measures drift detection, not whether the prompts make an agent better.

Measured by the drift benchmark in `benchmarks/drift/`: <!-- GENERATED:benchmark-headline -->verify caught 30 of 30 seeded drifts across 6 tools; plain git status caught 18 of 30; copying by hand caught 0<!-- /GENERATED:benchmark-headline -->. The last number is a floor, not a run: copying by hand has no source to compare against, so it misses by definition. Reproduce with `python benchmarks/drift/run.py` (git on PATH, under two minutes, writes only to a temp directory); every row is in [benchmarks/drift/README.md](benchmarks/drift/README.md).

## Install

Python 3.9 or newer, nothing to pip install. Confirmed working 2026-08-31 against a scratch
project: the two commands below wrote 31 files, then reported everything `ok` and exited 0.

```bash
git clone https://github.com/alawein/outpost && cd outpost
python install.py --tool claude --project /path/to/your/repo
python install.py --tool claude --project /path/to/your/repo --verify
```

Swap `claude` for `codex`, `cursor`, `copilot`, `windsurf`, `gemini`, or `all`. Narrow with
`--only` or `--exclude`, preview with `--dry-run`, clean up after a narrower re-install with
`--prune`, uninstall a tool with `--remove`. The installer never overwrites a file it did not
write; the one file it edits in place is `.claude/settings.json`, where it adds deny rules for
secrets and leaves existing keys alone. Full walkthrough: [docs/onboarding.md](docs/onboarding.md).

## Supported tools

| Tool | What gets installed |
|---|---|
| claude | a guide, the prompts as skills that load on their own, and safety rules for secrets only |
| codex | a guide and the prompts as files |
| cursor | a repo rule and the prompts as rules |
| copilot | repo instructions and the prompts as prompt files (VS Code, Visual Studio, JetBrains) |
| windsurf | an always-on rule and the prompts as workflows, invoked as `/outpost-<name>` |
| gemini | `GEMINI.md` and the prompts as custom commands, invoked as `/outpost:<name>` |

Each tool writes to its own paths, so several can live in one project. What differs and why:
[docs/adapters.md](docs/adapters.md).

## Watch a library you do not own

Point the installer at a skill library you cloned (obra/superpowers, or any tree in the Agent
Skills layout) and its skills install next to the core prompts, for every tool, checked by the
same `--verify`:

```bash
git clone https://github.com/obra/superpowers /path/to/superpowers
python install.py --tool claude --project /path/to/your/repo --source /path/to/superpowers
python install.py --tool claude --project /path/to/your/repo --verify
```

Outpost never fetches. Pull the clone and every installed copy of a changed skill reads
`DRIFTED` until the next `--source` install. Per-tool paths and limits: [docs/sources.md](docs/sources.md).

## Commands

Ask your agent for the step in front of you. Nine to start with:

```text
orient-repo        map an unfamiliar repo
plan-change        scope before editing
implement-change   small correct edits, runnable tree at each step
write-tests        cover the behavior, not the implementation
simplify           fold duplication, cut waste
grill              try to break it before you trust it
repo-review        audit a whole repo: structure, docs truth, tests, drift
triage             rank findings: fix now, defer, or reject
prepare-pr         commit, PR body, pre-merge checks
```

In Claude Code the prompts are skills and load by description. In Windsurf run
`/outpost-<name>`; in Gemini CLI run `/outpost:<name>`. In Codex, Cursor, and Copilot point the
agent at the matching file. The Claude Code plugin ([docs/plugin.md](docs/plugin.md)) adds nine
commands, tabled in [docs/workflow.md](docs/workflow.md), among them `/outpost:drive` to plan,
build, and test, and `/outpost:ship` to review and draft the PR (a human opens it). The ordered
path and all <!-- GENERATED:core-count-words -->twenty-eight<!-- /GENERATED:core-count-words --> prompts are in [docs/workflow.md](docs/workflow.md).

Working on the kit itself:

```bash
python validate.py
python -m pytest -q
```

Both must pass before a change is done.

## Architecture

```text
outpost/
  install.py        install prompts into a target project
  validate.py       kit source-tree checks
  kit/               catalog, per-tool adapters, checks, doc/plugin/template generators
  prompts/           core prompts plus per-tool overlays
  plugins/outpost/   generated Claude Code plugin (skills, commands, hooks)
  templates/         consumer guide templates
  evals/             behavioral eval fixtures per piloted prompt
  benchmarks/drift/  the drift benchmark and its reproduction script
  docs/              onboarding, workflow, decisions, releasing
  tests/             pytest
  tools/             build.py, the eval runner, label sync
```

For Claude Code the prompts install as `SKILL.md` files in the open Agent Skills layout, the
same layout `--source` reads; the other five tools get the same text in the format each one
reads. Role boundaries and the generation flow (catalog to prompts, adapters, plugin, docs):
[docs/architecture/topology.md](docs/architecture/topology.md).

## Docs map

- [docs/onboarding.md](docs/onboarding.md)
- [docs/workflow.md](docs/workflow.md)
- [docs/adapters.md](docs/adapters.md)
- [docs/sources.md](docs/sources.md)
- [docs/plugin.md](docs/plugin.md)
- [benchmarks/drift/README.md](benchmarks/drift/README.md)
- [docs/architecture/topology.md](docs/architecture/topology.md)
- [docs/how-this-is-built.md](docs/how-this-is-built.md)
- [docs/writing-standard.md](docs/writing-standard.md)
- [docs/contributing.md](docs/contributing.md)
- [docs/releasing.md](docs/releasing.md)
- [docs/decisions/](docs/decisions/README.md)
- [docs/DEBT.md](docs/DEBT.md)
- [docs/ROADMAP.md](docs/ROADMAP.md)
- [docs/token-budget.md](docs/token-budget.md)
- [docs/labels.md](docs/labels.md)
- [AGENTS.md](AGENTS.md)
- [CLAUDE.md](CLAUDE.md)

This repo has no `docs/README.md`, `SSOT.md`, or `LESSONS.md`; `docs/decisions/` and
`docs/DEBT.md` carry that role instead.

## Consumers

- No sibling repo in this workspace has installed it yet. `.claude/` and `.outpost/` are
  gitignored in this repo itself (see `.gitignore`): Outpost is not installed into its own
  tree, so it is not its own consumer.

## Release and versioning

- Version source: `kit/catalog/catalog.json`, `pyproject.toml`, `kit/__init__.py`, and the
  latest `CHANGELOG.md` heading, which must agree (`python validate.py` checks it).
- SemVer, tracked in [CHANGELOG.md](CHANGELOG.md) (Keep a Changelog format). Current release:
  v1.0.0, tagged 2026-08-31.
- Publish mode: clone and run, no PyPI package. Cut steps: [docs/releasing.md](docs/releasing.md).

`python validate.py` and `pytest` prove the kit's own tree, not a consumer repo. CI runs both
plus `python benchmarks/drift/run.py --check` on Linux and Windows.

MIT licensed. See [LICENSE](LICENSE).
