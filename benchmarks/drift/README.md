# Drift benchmark

When an installed prompt and its source stop matching, which tool notices? Five seeded kinds of
drift, applied to each adapter's install, scored by three detectors. The numbers below come
from a real run, and every miss inside these five scenarios is a published row.

## What it measures

One scratch project gets `install.py --tool all` and a git commit. For each scenario and tool,
the runner copies that project, checks the copy is in sync (`--verify` exits 0, `git status`
is clean), applies one seed, proves the seed changed something, then asks each detector.

- `verify`: `python install.py --tool all --project <copy> --verify`. Caught when a report
  line names the seeded path with a status other than `ok`.
- `git`: `git status --porcelain` names the seeded path. The tool most people already have,
  so it is the honest comparison.
- `none`: not run. Copying prompts by hand has nothing to compare against, so every row is
  set to miss by definition; the column is the floor, not a measurement.

The scenarios, each applied once per adapter:

| id | seed |
|---|---|
| `edited-copy` | append one line to the tool's installed copy of `plan-change` |
| `deleted-copy` | delete the tool's installed copy of `write-tests` |
| `source-ahead` | append one line to `prompts/core/plan-change.md` in a copy of the kit, then verify the untouched project from that copy |
| `orphan` | re-install the tool with `--only plan-change` and no prune, so the other prompt files stay on disk |
| `guide-edited` | append one line to the tool's guide (`CLAUDE.md`, `AGENTS.md`, and the rest) |

Prompt and guide paths come from each adapter's plan at run time, never from a table, so a new
adapter joins the benchmark by existing.

## Reproduce

```
python benchmarks/drift/run.py
```

Standard library only, plus `git` on PATH (the baseline commit and the git detector) and
Python 3.9 or later. Under two minutes, and it writes only to a temp directory. `--write`
also rewrites `results.json` and the table below. `--check` (the CI step) runs fresh and exits
1 if anything differs from `results.json` or the table here. `--tools claude,gemini` runs a
subset for a quick print; `--check` compares against the full six-tool results, so do not
combine the two. `--jobs N` sets how many rows run side by side (default 4).

## Results

<!-- RESULTS -->
| scenario | tool | verify | git | none |
|---|---|---|---|---|
| edited-copy | claude | caught | caught | miss |
| edited-copy | codex | caught | caught | miss |
| edited-copy | cursor | caught | caught | miss |
| edited-copy | copilot | caught | caught | miss |
| edited-copy | windsurf | caught | caught | miss |
| edited-copy | gemini | caught | caught | miss |
| deleted-copy | claude | caught | caught | miss |
| deleted-copy | codex | caught | caught | miss |
| deleted-copy | cursor | caught | caught | miss |
| deleted-copy | copilot | caught | caught | miss |
| deleted-copy | windsurf | caught | caught | miss |
| deleted-copy | gemini | caught | caught | miss |
| source-ahead | claude | caught | miss | miss |
| source-ahead | codex | caught | miss | miss |
| source-ahead | cursor | caught | miss | miss |
| source-ahead | copilot | caught | miss | miss |
| source-ahead | windsurf | caught | miss | miss |
| source-ahead | gemini | caught | miss | miss |
| orphan | claude | caught | miss | miss |
| orphan | codex | caught | miss | miss |
| orphan | cursor | caught | miss | miss |
| orphan | copilot | caught | miss | miss |
| orphan | windsurf | caught | miss | miss |
| orphan | gemini | caught | miss | miss |
| guide-edited | claude | caught | caught | miss |
| guide-edited | codex | caught | caught | miss |
| guide-edited | cursor | caught | caught | miss |
| guide-edited | copilot | caught | caught | miss |
| guide-edited | windsurf | caught | caught | miss |
| guide-edited | gemini | caught | caught | miss |
| total | | 30/30 | 18/30 | 0/30 |
<!-- /RESULTS -->

Every scenario reads the same for all six tools, so the tool rows are replicates. Per kind of
drift the score is verify 5 of 5, git 3 of 5; the 30-row totals are those times six. The
per-tool rows stay so a future adapter that differs shows up.

## EDITED and the git misses

`guide-edited` is caught by `verify` as `EDITED`, not `DRIFTED`. A guide is a create-mode
file: the kit writes it once, then leaves it as the user's. The manifest keeps the hash of what
the kit wrote, and verify compares the current bytes to it. A mismatch prints
`EDITED <path> (yours to keep; differs from what the kit wrote)` plus a one-line `NOTE:` count.

The row counts as caught because the path gets a status other than `ok`, but it is not a
failure: the exit code stays 0 and no `DRIFT:` line prints. A guide that existed before the
install has no kit baseline and stays `ok`.

Not measured. Three more edits pass verify and git catches: an extra key in
`.claude/settings.json` (a merge-mode file, re-merged from disk), a deleted guide (create-mode,
optional), and a stray file inside a kit directory (not a kit prompt name). One goes the other
way: an edited copy that was committed is clean for git and DRIFTED for verify. Adding any of
these changes the totals.

`git` misses `source-ahead` and `orphan` because neither seed changes a tracked file the row
names: the source edit lives outside the project, and the narrowed re-install (its manifest
change) is committed as the user's own change before the detectors run, so git is clean; the
leftovers are byte-identical files only the manifest disowns. Only a tool that re-plans from
the kit source sees either.
