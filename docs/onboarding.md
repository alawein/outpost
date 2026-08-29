---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-08-27
---

# Onboarding

Clone to a working setup in minutes. Python 3.9 or newer, standard library only.

## Install

```bash
git clone https://github.com/alawein/outpost && cd outpost
python install.py --tool claude --project /path/to/your/repo
python install.py --tool claude --project /path/to/your/repo --verify
```

`--dry-run` previews the plan without writing. `--tool all` installs every tool; each writes to its own paths, so they coexist in one repo.

Install a subset with `--only plan-change,write-tests`, or everything but a few with `--exclude grill,premortem`. The full pack is the default. The full flag reference (`--verify`, `--prune`, `--remove`, and how the `.outpost/manifest.json` record works) lives in [docs/adapters.md](adapters.md).

The installer writes only kit-owned files. It never overwrites your `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, Cursor rule, Copilot instructions, or Windsurf rule. It keeps yours and prints `skip <path> (exists, left alone)`; the kit's version is in `templates/` if you want to copy changes by hand.

For tests: `pip install -e ".[dev]"` to get pytest.

## First change

Ask your agent to plan a change. In Claude Code, `plan-change` loads on its own. In Windsurf run `/outpost-plan-change`; in Gemini CLI run `/outpost:plan-change`; elsewhere point at the matching prompt file. The ordered path: [docs/workflow.md](workflow.md).

## Verify

Two different checks prove two different things:

- `python validate.py`, run from the kit checkout, proves the kit source tree. Run `pytest` there for the tests.
- `python install.py --tool <tool> --project /path/to/your/repo --verify`, also run from the kit checkout, proves the install in your repo against its manifest.

Verify prints one status per file:

- `ok`: the copy matches the kit (a guide may also be absent, which is fine).
- `DRIFTED`: the copy no longer matches its source. Re-install to restore it.
- `MISSING`: the copy is gone. Re-install to restore it.
- `EXTRA`: a leftover from a narrower re-install. `--prune` removes it.
- `EDITED`: a guide the kit wrote (`CLAUDE.md` and the like) that you changed since. Yours to keep; reported, never a failure.
- `LEFTOVER`: a kit-installed file whose prompt no longer ships to this tool, or a source skill the library dropped. `--prune` removes it when it still matches what the kit wrote; one you edited, or one the kit has no record of writing, is left for you to delete.
- `ESCAPED`: the path resolves outside the project through a symlink. Never touched.

Any status but `ok` and `EDITED` fails the run.
