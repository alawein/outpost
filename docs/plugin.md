---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-07-26
---

# Claude Code plugin

A second install path for Claude Code users. It packages the catalog as plugin skills: <!-- GENERATED:core-count-words -->twenty-four<!-- /GENERATED:core-count-words --> core prompts, one skill each. `install.py` remains the cross-tool path.

## Install

Register the repo as a marketplace, then install the plugin from it. The repo root carries the marketplace manifest (`.claude-plugin/marketplace.json`), so the repo itself is the marketplace:

```bash
claude plugin marketplace add alawein/outpost
claude plugin install outpost@outpost
```

For local development, register your checkout as the marketplace instead:

```bash
claude plugin marketplace add /path/to/outpost
claude plugin install outpost@outpost
```

Skills and commands surface namespaced under the plugin name, as `/outpost:<name>`.

## What it adds

- <!-- GENERATED:core-count-words -->twenty-four<!-- /GENERATED:core-count-words --> skills, one per core prompt. They load by description, the same way the installer loads them.
- Nine commands that chain those prompts into typed shortcuts. See [workflow.md](workflow.md) for what each one runs.

## Hooks

One hook loads automatically when the plugin is installed (via `hooks.json` in `plugins/outpost/hooks/`):

- `nudge_context` (PostToolUse, advisory): after a large Read with no offset or limit, tells the model to read in bounded windows. Warns only; does not block. The size threshold is `OUTPOST_NUDGE_BYTES` (default 100000 bytes).

## Agents

One read-only agent loads automatically when the plugin is installed (via `agents/` in `plugins/outpost/agents/`):

- `architecture-guardian`: checks a change against the repo's decision records and rules, then flags mismatches. Never edits.

## Output style

One output style ships with the plugin: `ledger-voice`. It gives terse, auditable output: findings first, claims tagged, no slop. Toggle with `/output-style`.

## How it stays in sync

Skills and manifests are generated from the catalog and prompt files. Run `python tools/build.py plugin` after any prompt or manifest wording change. The `plugin_sync` check fails if the committed tree drifts from the generator.

The nine command files under `plugins/outpost/commands/` are hand-authored. Keep their prompt names in backticks so `plugin_sync` catches a bad reference.

The decision to package the kit as an additive plugin is recorded in [ADR-0004](decisions/0004-plugin-packaging.md).
