---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-08-27
---

# Roadmap

What exists now, what comes next. `CHANGELOG.md` records what shipped; this file records intent.

## Where it stands

Current release: v0.1.0. The table is the live state.

| Area | State | What is in it |
|---|---|---|
| Prompt pack | built | The core pack is <!-- GENERATED:core-count-words -->twenty-eight<!-- /GENERATED:core-count-words --> prompts by stage: <!-- GENERATED:stage-counts -->two start, three plan, five build, seven review and ship, one converge, seven scrutiny, two record, and one write<!-- /GENERATED:stage-counts -->, including the review suite's `repo-review`, `simplify`, and `triage` |
| Templates | built | `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, a Cursor repo rule, Copilot instructions, a Windsurf rule |
| Installer | built | `install.py`: per-tool or `all`, dry-run, repeatable, safe settings merge |
| Subset install | built | `--only`/`--exclude` install a subset of the prompt pack. `.outpost/manifest.json` records the choice, `--verify` reads it, `--prune` removes orphan files left by a narrower re-install, and `--remove` uninstalls a tool. Full pack stays the default |
| Adapters | built | Claude Code (primary), Codex, Cursor, GitHub Copilot, Windsurf, Gemini CLI; separate paths, coexist |
| Sources | built | `--source <dir>` installs a skill library the kit does not own (a clone in the Agent Skills layout, such as obra/superpowers) for every tool, records it in the manifest, and `--verify` reads each installed copy against the source's current state; see `docs/sources.md` |
| Catalog | built | `kit/catalog/catalog.json`; lists what ships |
| Checks | built | `python validate.py`: <!-- GENERATED:checks-line -->twenty-three checks (structure, catalog, prompts, templates, adapters, docs, secrets, voice, banned_sync, template_refs, templates_sync, docs_sync, doc_truth, plugin_sync, plugin_orphans, registries, roadmap, command_lists, commands, traces, label_refs, issue_forms, prose_length)<!-- /GENERATED:checks-line --> |
| Docs | built | Onboarding, workflow, writing standard, adapters, sources, contributing, releasing, plugin, token budget, labels, how this is built, debt, roadmap, and the drift benchmark's README |
| Tests | built | The kit's own suite over the installer, adapters, catalog, and checks |
| Claude Code plugin | built | `plugins/outpost/`: the core catalog skills, nine commands (/outpost:stress, /outpost:ship, /outpost:drive, /outpost:doctor, /outpost:repo-review, /outpost:code-review, /outpost:simplify, /outpost:prove, /outpost:triage), one read-only agent (architecture-guardian), one context hook, and a ledger voice output style (ledger-voice); see `docs/plugin.md` |
| Benchmark | built | `benchmarks/drift/`: five seeded drift scenarios per adapter, each scored by three detectors (the installer's `--verify`, `git status`, and copying by hand); `results.json` is the published table, CI re-runs it with `--check`, and a miss stays a published row; see `benchmarks/drift/README.md` |

The smoke proof: a clean clone with only Python installed runs `python install.py --tool all --project <target>` into a scratch repo, then `python validate.py` from the kit checkout, and both pass. That proves packaging and parity (the files, counts, and generated copies agree, and the install lands), not that the prompts make an agent more effective. A consumer repo verifies its own install with `python install.py --tool <tool> --project <target> --verify`.

## Planned

- 1.0, once a release ships the benchmark, the sources mechanism, and the README that leads with the benchmark, with CI green on that release.

## Out of scope

Recorded so no one re-adds them without a decision.

- A bundled judge engine or third-party dependencies in core. Eval scoring, guide generation,
  and project-specific governance stay out of the kit; none serves the coding-agent purpose.
  The kit is stdlib-only.
- Auto-update of an installed kit. Out and not planned.

## Idea backlog

Unscheduled and unproven. An idea moves to Planned only after the smallest test that could prove it wrong is named and survives.

- A worked example per prompt. Open: examples drift from prompts and add text the voice check must police; an example must not be required for use.
- A packaged distribution (pip or single-file). Open: whether the audience wants this over a clone, given the kit is small and mostly cloned rather than installed as a package.
- A prompt-overlay example under `prompts/<tool>/`. Open: overrides are where tools drift, so this stays rare by design.
- An auditable existing-text trimmer, `deblab`: a prompt that shortens a draft and reports what it cut, distinct from `simplify` (code) and `write-doc` (authors, does not condense existing text). Open: it duplicates `ledger-voice` and the writing standard unless an eval first shows real cases where terseness lost meaning that those did not catch. It would also have to clear the full prompt flow (a `prompts/core` source with all five sections, the build, the count-sensitive tests, and a new `/outpost:` command). Deferred until that evidence exists.

## How an item moves

- Idea to Planned: name the smallest test that could prove it wrong, run it, survive, then assign a target version.
- Planned to built: it ships with passing checks and a changelog entry, and this file moves the line.
- A rejected idea stays in the record with its reason, so no one suggests it again.
