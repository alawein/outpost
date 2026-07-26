---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-07-26
---

# Roadmap

What exists now, what comes next. `CHANGELOG.md` records what shipped; this file records intent.

The kit helps a coding agent read a repo, plan a change, edit, test, review, draft the PR text, and hand off. A human opens and merges the PR. Claude Code is the main target. Codex, Cursor, and GitHub Copilot are adapters over the same prompt pack.

## Where it stands

Current release: v0.2.1. The table is the live state.

| Area | State | What is in it |
|---|---|---|
| Prompt pack | built | The core pack is <!-- GENERATED:core-count-words -->twenty-four<!-- /GENERATED:core-count-words --> prompts: one maps the repo, two plan, five build and test, five review and ship, one loops checks until clean, seven add scrutiny, two record decisions and debt, and one writes docs, widened by the review suite's `repo-review`, `simplify`, and `triage` (ADR-0011) |
| Templates | built | `CLAUDE.md`, `AGENTS.md`, a Cursor repo rule, Copilot instructions |
| Installer | built | `install.py`: per-tool or `all`, dry-run, repeatable, safe settings merge |
| Subset install | built | `--only`/`--exclude` install a subset of the prompt pack. `.outpost/manifest.json` records the choice, `--verify` reads it, `--prune` removes orphan files left by a narrower re-install, and `--remove` uninstalls a tool. Full pack stays the default (ADR-0003) |
| Adapters | built | Claude Code (primary), Codex, Cursor, GitHub Copilot; separate paths, coexist |
| Catalog | built | `kit/catalog/catalog.json`; lists what ships |
| Checks | built | `python validate.py`: <!-- GENERATED:checks-line -->nineteen checks (structure, catalog, prompts, templates, adapters, docs, secrets, voice, banned_sync, template_refs, templates_sync, docs_sync, doc_truth, plugin_sync, plugin_orphans, registries, roadmap, command_lists, traces)<!-- /GENERATED:checks-line --> |
| Docs | built | Onboarding, workflow, writing standard, adapters, contributing, releasing, plugin, token budget, dogfooding, cadence, debt, roadmap |
| Tests | built | The kit's own suite over the installer, adapters, catalog, and checks |
| Claude Code plugin | built | `plugins/outpost/`: the core catalog skills, nine commands (/outpost:stress, /outpost:ship, /outpost:drive, /outpost:doctor, /outpost:repo-review, /outpost:code-review, /outpost:simplify, /outpost:prove, /outpost:triage), one read-only agent (architecture-guardian), one context hook, and a ledger voice output style (ledger-voice); see `docs/plugin.md` and ADR-0004 |

The smoke proof: a clean clone with only Python installed runs `python install.py --tool all --project <target>` into a scratch repo, then `python validate.py` from the kit checkout, and both pass. That proves packaging and parity (the files, counts, and generated copies agree, and the install lands), not that the prompts make an agent more effective. A consumer repo verifies its own install with `python install.py --tool <tool> --project <target> --verify`.

## Out of scope

Recorded so no one re-adds them without a decision.

- A bundled judge engine or third-party dependencies in core. Eval scoring, guide generation, a
  held-out data firewall, training export, device automation, team-ops prompts, and
  project-specific governance stay out of the kit; none serves the coding-agent purpose (ADR-0001).
  The kit is stdlib-only.
- Auto-update of an installed kit, and a packaged distribution. Out and not planned.

## Planned

Nothing is scheduled for the next release yet; candidates live in the idea backlog below.

v0.1.0 is Outpost's first public release, forked from an internal predecessor kit (ADR-0017).
That predecessor's own version history (v0.1 through v0.25) does not carry forward; see
`docs/decisions/` for the design decisions that still hold.

Rule for adding a check: it catches a mismatch the current checks miss, runs on the Python standard library only, and ships with a test that passes clean and fails on a seeded violation.

## Idea backlog

Unscheduled and unproven. An idea moves to Planned only after the smallest test that could prove it wrong is named and survives.

- A worked example per prompt. Open: examples drift from prompts and add text the voice check must police; an example must not be required for use.
- A packaged distribution (pip or single-file). Open: whether the audience wants this over a clone, given the kit is small and mostly cloned rather than installed as a package.
- A prompt-overlay example under `prompts/<tool>/`. Open: overrides are where tools drift, so this stays rare by design.
- An auditable existing-text trimmer, `deblab`: a prompt that shortens a draft and reports what it cut, distinct from `simplify` (code) and `write-doc` (authors, does not condense existing text). Open: it duplicates `ledger-voice` (itself the renamed `no-blab`) and the writing standard unless the dogfooding ledger first shows real cases where terseness lost meaning that those did not catch. It would also have to clear the full prompt flow (a `prompts/core` source with all five sections, the build, the count-sensitive tests, and an ADR for the new `/outpost:` command). Deferred until that evidence exists.

## How an item moves

- Idea to Planned: name the smallest test that could prove it wrong, run it, survive, then assign a target version.
- Planned to built: it ships with passing checks and a changelog entry, and this file moves the line.
- A rejected idea stays in the record with its reason, so no one suggests it again.
