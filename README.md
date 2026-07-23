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

</div>

**Outpost is a personal prompt pack for coding agents: read a repo, plan, build, test, review, ship, hand off.**

The core prompts install under Claude Code, Codex, Cursor, and GitHub Copilot. Claude Code gets the fullest path: skills that load on their own and a safe settings merge. The other tools install the same core prompts as files, except `converge`, which ships to Claude only. One install gives each tool the same path, so every tool works the same way and spends fewer tokens.

Maintained by the handle in [.github/CODEOWNERS](.github/CODEOWNERS).

<div align="center">

<img src="docs/brand/flow.svg" alt="The flow: orient, plan, build, test, review, ship, hand off, with debug-failure, write-tests, and converge beneath, and scrutiny prompts that pressure-test any step" width="100%">

</div>

## Quick start

```bash
# clone the kit, then install into your repo (or --tool all)
git clone https://github.com/alawein/outpost
cd outpost
python install.py --tool claude --project /path/to/your/repo
```

Use the prompt that matches the next step. In Claude, prompts load by description. In the other tools, point at the matching file.

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

Confirm the install from the kit checkout:

```bash
python install.py --tool claude --project /path/to/your/repo --verify
```

`python validate.py` (run from the kit checkout) proves the kit source tree itself, not an install.

## Install options

Use `--tool codex`, `--tool cursor`, `--tool copilot`, or `--tool all`. `--dry-run` previews without writing.

Install a subset with `--only plan-change,write-tests` or `--exclude grill`. The full pack is the default. The installer records the choice. `--verify` checks that install, `--prune` removes prompt files left by a narrower re-install, and `--remove` uninstalls a tool.

For the full install path, see [docs/onboarding.md](docs/onboarding.md).

## The prompt pack

The kit ships <!-- GENERATED:core-count-words -->twenty-four<!-- /GENERATED:core-count-words --> prompts, one per step from first repo read to handoff: start, plan, build, check, ship, with scrutiny and record around them.

In Claude Code the common sequences are one command: `/outpost:drive` to plan, build, and test, and `/outpost:ship` to review and draft the PR (a human opens it).

See [docs/workflow.md](docs/workflow.md) for the ordered path, the Claude Code shortcuts, and the full prompt list.

## Claude Code plugin commands

Claude Code adds typed shortcuts: `/outpost:drive`, `/outpost:ship`, `/outpost:stress`, `/outpost:doctor`, and the review suite. See [docs/workflow.md](docs/workflow.md) for what each one runs.

## Best practices

Use the kit and the model with fewer tokens and fewer dead ends.

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

Each tool writes to its own paths, so they can live in one project. The installer never overwrites a file you own.

## Checks and docs

Run `python validate.py` before you claim a change to the kit is done. It proves the kit source tree: files, counts, prompts, docs, coexistence, secrets, and house voice. It does not check a consumer repo; verify an install there with `python install.py --tool <tool> --project <target> --verify` from the kit checkout. Run `pytest` for the test suite. CI runs both on Linux and Windows.

- New here: [docs/onboarding.md](docs/onboarding.md)
- A change end to end: [docs/workflow.md](docs/workflow.md)
- Choosing a prompt: [docs/workflow.md](docs/workflow.md)
- Add a prompt, tool, or check: [docs/contributing.md](docs/contributing.md)
- How often to commit, PR, and file tracker items: [docs/cadence.md](docs/cadence.md)
- Where it is headed: [docs/ROADMAP.md](docs/ROADMAP.md)

MIT licensed. See [LICENSE](LICENSE).
