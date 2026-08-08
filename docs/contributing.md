---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-07-26
---

# Contributing

How to add to the kit without breaking it. The catalog lists what ships, and `python validate.py` enforces that list.

## Ground rules

- One concern per PR. Done means `python validate.py` and `pytest` pass.
- No em-dashes, no banned register, plain ASCII. The `voice` check rejects any non-ASCII character in tracked markdown, with named errors for the two dash characters and the banned-word list.

## Add a prompt

1. Write `prompts/core/<name>.md`: frontmatter (`name` matching the file, a real `description`) and five sections (when to use, required inputs, steps, output format, stop conditions).
2. Add it to `kit/catalog/catalog.json` under `prompts`. A core prompt's entry must include a `stage` field naming one of the `stages` list entries, or the prompt-pack table generator will not place it anywhere.
3. Regenerate the generated copies: `python tools/build.py plugin` writes the prompt's plugin skill, and `python tools/build.py docs` updates the prompt-pack table and the prompt counts. Without them, `plugin_sync` and `docs_sync` fail.
4. Run `python validate.py`. The `prompts` check rejects a stub; `catalog` rejects missing or extra entries.

## Edit a template

The four guide templates (`CLAUDE.md`, `AGENTS.md`, `cursor-rules.md`, `copilot-instructions.md`) are generated, not hand-edited. Edit the sources under `templates/_src/`:

- `_src/core.md` is the shared core, identical in every guide. It names the prompt pack, so the `templates` and `template_refs` checks pass.
- `_src/head/<tool>.md` is the per-tool head: title, where the file and prompts live, how they load.

Run `python tools/build.py templates`, then `python validate.py`. The `templates_sync` check fails if a committed guide no longer matches the source. To add a guide for a new tool, add a catalog `templates` entry and a `_src/head/<name>.md`, then wire the adapter that installs it.

## Edit a generated doc span

The prompt-pack table in `docs/workflow.md`, the prompt-total counts in `README.md`, `docs/workflow.md`,
and `docs/plugin.md`, and the ROADMAP's current-state counts in `docs/ROADMAP.md` (its checks
line and core-prompt count) are generated from the catalog, marked with
`<!-- GENERATED:<key> -->...<!-- /GENERATED:<key> -->` comments. Do not hand-edit the content
between a marker pair; edit the catalog instead (a core prompt's `stage`, the top-level `stages`
list, or the prompt and check sets follow automatically from the catalog's contents).

Run `python tools/build.py docs`, then `python validate.py`. The `docs_sync` check fails if a
committed span drifts from the generator.

## Add an adapter

1. Create `kit/adapters/<tool>.py` with `plan(kit_root, project_root, terse=False)` returning Actions. Reuse `kit/adapters/base.py`.
2. Register the tool in `kit/adapters/__init__.py` and in the catalog under `adapters`.
3. Keep its paths separate from the others; `adapters` proves the tools can coexist.
4. Name the tool in the README "Supported tools" table and the docs/adapters.md "What each tool gets" table; the `doc_truth` check fails while either misses it.
5. Add a test that the new adapter and the existing ones coexist.

## Add a check

1. Write `kit/checks/<name>.py` with `run(root) -> (ok, detail)`.
2. List it in the catalog under `checks`; the runner picks it up in catalog order.
3. Regenerate the ROADMAP's checks line with `python tools/build.py docs`; `docs_sync` fails while the committed line lags the catalog.
4. Add a test that it passes on a clean tree and fails on a seeded violation.

## Report a bug or propose work

Open an issue from one of the forms under `.github/ISSUE_TEMPLATE/`: bug report, feature
request, prompt proposal (must clear `docs/decisions/0025-relax-prompt-admission.md`, which
relaxed `docs/decisions/0013-prompt-admission.md`), or a repo-hygiene finding. See
`docs/labels.md` for how labels route them.

## Before a PR

Run `python validate.py` and `pytest`, then follow `prepare-pr` to draft the commit and PR.

This is a solo repo (ADR-0018). An outside PR gets the owner's review before merge; the owner's own
PRs merge on green CI without a second approval, since GitHub allows no self-approval.
`.github/CODEOWNERS` names the owner and routes the review request. No automated PR reviewer is
wired for this repo, and CodeRabbit is off (`.coderabbit.yaml`).

## Behavioral evals (optional)

`python tools/run_evals.py` runs 6 pilot prompts through a real `claude -p` call against a seeded
fixture and checks the result. Requires the `claude` CLI installed and authenticated; not part of
`validate.py` or CI, since it costs real usage and is not deterministic. Run it by hand after
touching one of the piloted prompts (`interrogate`, `plan-change`, `record-decision`,
`write-tests`, `debt-log`, `orient-repo`); `python tools/run_evals.py --only <name>` runs just one.
