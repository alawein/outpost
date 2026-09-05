---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-09-05
---

# Contributing

How to add to the kit without breaking it. The catalog lists what ships, and `python validate.py` enforces that list.

## Ground rules

- A change is done when `python validate.py` and `python -m pytest -q` pass. CI runs both on
  Linux and Windows, then `python benchmarks/drift/run.py --check`.
- Standard library only. No third-party imports in the core, the installer, or the checks.
- One concern per pull request; target 400 changed lines and 20 files or fewer, and say why in
  the body when you exceed it. Delete the branch on merge.
- Stage exact paths. Keep `.env` and secrets out of the tree.
- Follow the repository's conventional commit format in [CLAUDE.md](../CLAUDE.md).
  Keep existing history unchanged; the format applies to new commits.
- A deliberate shortcut lands in `docs/DEBT.md` in the same PR.
- Plain ASCII, no em dashes, none of the banned words in `docs/writing-standard.md`.

## Add a prompt

1. Write `prompts/core/<name>.md`: frontmatter (`name` matching the file, a real `description`) and five sections (when to use, required inputs, steps, output format, stop conditions).
2. Add it to `kit/catalog/catalog.json` under `prompts`. A core prompt's entry must include a `stage` field naming one of the `stages` list entries, or `python tools/build.py docs` fails with a stage error.
3. Regenerate the generated copies: `python tools/build.py plugin` writes the prompt's plugin skill, and `python tools/build.py docs` updates the prompt-pack table and the prompt counts. Without them, `plugin_sync` and `docs_sync` fail.
4. Run `python validate.py`. The `prompts` check rejects a stub; `catalog` rejects missing or extra entries.
5. In the pull request body, name the closest existing prompt and the gap it leaves, in one
   sentence. That is the whole admission check; if the closest prompt already does the job,
   extend it instead.

## Edit a template

The six guide templates (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `cursor-rules.md`, `copilot-instructions.md`, `windsurf-rules.md`) are generated, not hand-edited. Edit the sources under `templates/_src/`:

- `_src/core.md` is the shared core, identical in every guide. It names the prompt pack, so the `templates` and `template_refs` checks pass.
- `_src/head/<tool>.md` is the per-tool head: title, where the file and prompts live, how they load.

Run `python tools/build.py templates`, then `python validate.py`. The `templates_sync` check fails if a committed guide no longer matches the source. To add a guide for a new tool, add a catalog `templates` entry and a `_src/head/<name>.md`, then wire the adapter that installs it.

## Edit a generated doc span

The prompt-pack table in `docs/workflow.md`, the prompt-total counts in `README.md`, `docs/workflow.md`,
and `docs/plugin.md`, and the ROADMAP's current-state counts in `docs/ROADMAP.md` (its checks
line, core-prompt count, and per-stage counts) are generated from the catalog, marked with
`<!-- GENERATED:<key> -->...<!-- /GENERATED:<key> -->` comments. Do not hand-edit the content
between a marker pair; edit the catalog instead (a core prompt's `stage`, the top-level `stages`
list, or the prompt and check sets follow automatically from the catalog's contents).

Run `python tools/build.py docs`, then `python validate.py`. The `docs_sync` check fails if a
committed span drifts from the generator.

## Add an adapter

1. Create `kit/adapters/<tool>.py` with `plan(kit_root, project_root, terse=False, select=None, tolerant=False)` returning Actions. Reuse `kit/adapters/base.py`.
2. Register the tool in `kit/adapters/__init__.py` and in the catalog under `adapters`.
3. Keep its paths separate from the others; `adapters` proves the tools can coexist.
4. Name the tool in the README "Supported tools" table and the docs/adapters.md "What each tool gets" table; the `doc_truth` check fails while either misses it.
5. Add a test that the new adapter and the existing ones coexist.

A new adapter joins the drift benchmark by existing: the runner reads its paths from
`plan_for`, not from a table. After adding one, run `python benchmarks/drift/run.py --write`
and commit `benchmarks/drift/results.json` (plus the table it rewrites in
`benchmarks/drift/README.md`), or the CI `--check` step fails on the new rows.

## Add a check

1. Write `kit/checks/<name>.py` with `run(root) -> (ok, detail)`.
2. List it in the catalog under `checks`; the runner picks it up in catalog order.
3. Regenerate the ROADMAP's checks line with `python tools/build.py docs`; `docs_sync` fails while the committed line lags the catalog.
4. Add a test that it passes on a clean tree and fails on a seeded violation.

## Report a bug or propose work

Use the issue forms: bug, feature, prompt proposal, or hygiene finding. Security issues go
through `SECURITY.md`, never a public issue.

## Before a PR

Run both gates, then follow `prepare-pr`: it drafts the commit and the body from the template.

## Behavioral evals (optional)

`python tools/run_evals.py` runs the nine piloted evals through a real agent CLI. Not part of
the gate or CI.
