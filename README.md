<div align="center">

# Outpost

[![ci](https://github.com/alawein/outpost/actions/workflows/ci.yml/badge.svg)](https://github.com/alawein/outpost/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.9%2B-2f81f7?style=flat-square)
![dependencies](https://img.shields.io/badge/dependencies-none-2ea043?style=flat-square)
![license](https://img.shields.io/badge/license-MIT-2ea043?style=flat-square)

![Claude](https://img.shields.io/badge/Claude-D97757?style=for-the-badge)
![Codex](https://img.shields.io/badge/Codex-10A37F?style=for-the-badge)
![Cursor](https://img.shields.io/badge/Cursor-0098FF?style=for-the-badge)
![Copilot](https://img.shields.io/badge/Copilot-8957E5?style=for-the-badge)
![Windsurf](https://img.shields.io/badge/Windsurf-09B6A2?style=for-the-badge)
![Gemini](https://img.shields.io/badge/Gemini-4285F4?style=for-the-badge)

</div>

## Purpose

**Outpost is a personal prompt pack for coding agents: read a repo, plan, build, test, review, ship, hand off.**

The core prompts install under Claude Code, Codex, Cursor, GitHub Copilot, Windsurf, and Gemini CLI. Claude Code gets the fullest path: skills that load on their own and a safe settings merge. The other tools install the same core prompts as files, except `converge`, which ships to Claude only. One install gives each tool the same path, so every tool works the same way and spends fewer tokens.

Maintained by the handle in [.github/CODEOWNERS](.github/CODEOWNERS). See
[Consumers](#consumers) below for who this is built for.

## Why Outpost

A hand-written CLAUDE.md works for one tool and one repo, until it drifts: a rule gets stale,
nobody deletes it, and the next agent follows advice that no longer applies.

Outpost installs one prompt pack across Claude Code, Codex, Cursor, Copilot, Windsurf, and
Gemini CLI, with a `--verify` step that proves every installed copy still matches the source.
A new prompt needs one answer, not a memo: which existing prompt is closest, and what gap it
leaves. Everything else is mechanical: `validate.py` proves the kit's own tree, and CI runs it
on every change.

Ruler and rulesync sync one rules file into every tool's format. Outpost does something
narrower on purpose: it gates what ships first, then checks the result mechanically, instead
of syncing whatever you already wrote. It is not a replacement for a process-discipline plugin
like superpowers either. That picks how a task gets done; Outpost's prompts and checks pick
what runs and prove it happened. The two run together.

<div align="center">

<img src="docs/brand/flow.svg" alt="The flow: orient, plan, build, test, review, ship, hand off, with debug-failure, write-tests, and converge beneath, and scrutiny prompts that pressure-test any step" width="100%">

</div>

The image above is a hand-drawn hero, not a generated artifact: it names the workflow's phase
words only (no prompt count, no prompt name), so it has nothing left for a check to read or
drift against. For the reviewable, GitHub-rendered version of the same path, see the
Mermaid diagram in [docs/workflow.md](docs/workflow.md#the-path).

## Install

```bash
# clone the kit, then install into your repo (or --tool all)
git clone https://github.com/alawein/outpost
cd outpost
python install.py --tool claude --project /path/to/your/repo
```

Use `--tool codex`, `--tool cursor`, `--tool copilot`, `--tool windsurf`, `--tool gemini`, or `--tool all`. `--dry-run` previews without writing.

Install a subset with `--only plan-change,write-tests` or `--exclude grill`. The full pack is the default. The installer records the choice. `--verify` checks that install, `--prune` removes prompt files left by a narrower re-install, and `--remove` uninstalls a tool.

For the full install path, see [docs/onboarding.md](docs/onboarding.md).

## Commands

```bash
python install.py --tool claude --project /path/to/your/repo
python install.py --tool claude --project /path/to/your/repo --verify
python validate.py   # proves the kit source tree itself, not an install
pytest
```

Use the prompt that matches the next step. In Claude, prompts load by description. In Windsurf and Gemini CLI, run the matching command. In the other tools, point at the matching file.

```text
orient-repo        # map an unfamiliar repo
plan-change        # scope before editing
implement-change   # small correct edits, runnable tree at each step
write-tests        # cover the behavior, not the implementation
simplify           # clean the change: fold duplication, cut waste
grill              # try to break it before you trust it
repo-review        # audit a whole repo: structure, docs truth, tests, drift
triage             # rank findings: fix now, defer, or reject
prepare-pr         # commit, PR body, pre-merge checks
```

In Claude Code the common sequences are one command: `/outpost:drive` to plan, build, and test, and `/outpost:ship` to review and draft the PR (a human opens it). Claude also adds `/outpost:stress`, `/outpost:doctor`, and the review suite. See [docs/workflow.md](docs/workflow.md).

## Architecture

Full layout map: [docs/architecture/topology.md](docs/architecture/topology.md).

Top-level surfaces: `install.py` and `validate.py` at the root; `kit/` (catalog, adapters, installers, checks); `prompts/` (core and per-tool overlays); `plugins/outpost/` (Claude Code plugin); `templates/`; `evals/` (behavioral eval fixtures); `docs/`; `tests/`.

The kit ships <!-- GENERATED:core-count-words -->twenty-eight<!-- /GENERATED:core-count-words --> prompts, one per step from first repo read to handoff: start, plan, build, check, ship, with scrutiny and record around them. See [docs/workflow.md](docs/workflow.md) for the ordered path and the full prompt list.

## Best practices

Spend fewer tokens:
- Install only what you need: `--only` for a focused pack, `--exclude` to drop what you will not use.
- Let skills load by description in Claude rather than pasting prompt text into the chat.
- Run `orient-repo` once to map a repo, then reuse the map; do not re-explore every turn.
- Hand a big file or a wide search to a subagent and keep its conclusion, not the raw context.

Make fewer errors:
- Run `plan-change` before a multi-file edit, then keep the tree runnable at each step.
- `grill` or `self-refute` a risky change before you trust it; `premortem` a plan before you commit to it.
- Run `validate.py` and the tests before you call a change done. Green is the bar, not the diff.
- `prepare-pr` drafts the commit and PR and runs the pre-merge checks, so nothing ships half-checked.

Work in parallel:
- Split independent units across separate agents, one per checkout, and review between them.
- Use `converge` to loop a diff, plan, or doc to clean while you move on to the next unit.
- `panel` gathers several expert views at once for a wide decision instead of one slow pass.

## Supported tools

| Tool | What gets installed |
|---|---|
| claude | a guide, the prompts as skills that load on their own, and safety rules for secrets only |
| codex | a guide and the prompts as files |
| cursor | a repo rule and the prompts as rules |
| copilot | repo instructions and the prompts as prompt files, for the VS Code, Visual Studio, and JetBrains Copilot integrations |
| windsurf | an always-on rule and the prompts as workflows, invoked as `/outpost-<name>` |
| gemini | `GEMINI.md` and the prompts as custom commands, invoked as `/outpost:<name>` |

Each tool writes to its own paths, so they can live in one project. The installer never overwrites a file you own.

## Docs map

- [docs/onboarding.md](docs/onboarding.md)
- [docs/workflow.md](docs/workflow.md)
- [docs/writing-standard.md](docs/writing-standard.md)
- [docs/architecture/topology.md](docs/architecture/topology.md)
- [docs/contributing.md](docs/contributing.md)
- [docs/releasing.md](docs/releasing.md)
- [docs/ROADMAP.md](docs/ROADMAP.md)
- [benchmarks/drift/README.md](benchmarks/drift/README.md)
- [docs/adapters.md](docs/adapters.md)
- [docs/how-this-is-built.md](docs/how-this-is-built.md)
- [docs/plugin.md](docs/plugin.md)
- [docs/labels.md](docs/labels.md)
- [docs/token-budget.md](docs/token-budget.md)
- [docs/DEBT.md](docs/DEBT.md)
- [docs/decisions/](docs/decisions/README.md)
- [AGENTS.md](AGENTS.md)
- [CLAUDE.md](CLAUDE.md)

Run `python validate.py` before you claim a change to the kit is done. It proves the kit source tree: files, counts, prompts, docs, coexistence, secrets, and house voice. It does not check a consumer repo; verify an install there with `python install.py --tool <tool> --project <target> --verify` from the kit checkout. CI runs `validate.py`, `pytest`, and the drift benchmark's `--check` on Linux and Windows.

## Consumers

- Personal and team coding-agent workflows that need one prompt pack across Claude, Codex, Cursor, Copilot, Windsurf, and Gemini CLI
- The maintainer's other repos, product and tooling alike, which install Outpost the same way

## Release and versioning

- Version source: `pyproject.toml` (must agree with `kit/catalog/catalog.json` and `kit/__init__.py`)
- Publish mode: public GitHub repo; consumers clone and run `install.py`
- Release process: [docs/releasing.md](docs/releasing.md)

MIT licensed. See [LICENSE](LICENSE).
