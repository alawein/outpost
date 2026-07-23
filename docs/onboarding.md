# Onboarding

Clone to a working setup in minutes. Python 3.9 or newer, standard library only.

## Install

```bash
python install.py --tool claude --project /path/to/your/repo
```

`--dry-run` previews the plan without writing. `--tool all` installs every tool. They can live in one repo.

Install a subset with `--only plan-change,write-tests`, or everything but a few with `--exclude grill,premortem`. The full pack is the default. The full flag reference (`--verify`, `--prune`, `--remove`, and how the `.outpost/manifest.json` record works) lives in [docs/adapters.md](adapters.md).

Each tool writes to its own paths, so they coexist in one repo; the per-tool list of what gets installed is in [docs/adapters.md](adapters.md).

The installer writes only kit-owned files. It never overwrites your `CLAUDE.md`, `AGENTS.md`, Cursor rule, or Copilot instructions. It keeps yours and points you to `templates/` to copy any changes by hand.

For tests: `pip install -e ".[dev]"` to get pytest.

## First change

Ask your agent to plan a change. In Claude Code, `plan-change` loads on its own; elsewhere point at the matching prompt file. Full path: [docs/workflow.md](workflow.md).

## Verify

Two different checks prove two different things:

- `python validate.py`, run from the kit checkout, proves the kit source tree. Run `pytest` there for the tests.
- `python install.py --tool <tool> --project /path/to/your/repo --verify`, also run from the kit checkout, proves the install in your repo against its manifest.
