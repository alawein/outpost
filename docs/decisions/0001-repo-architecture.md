# 0001: Repo architecture and first release scope

Status: Accepted
Date: 2026-06-28

## Context

The kit is rebuilt around one purpose: help a coding agent read a repo, plan, edit, test, review, prepare a PR, and hand off. It draws on an earlier internal kit as source material. That kit also carried eval tools, a judge engine, guide generation, a held-out data firewall, training export, and project-specific governance. None of that serves the coding-agent purpose. It made the kit heavy and hard to onboard. We want a small, honest kit a newcomer can read in one sitting.

## Decision

Build a fresh repo with a clear shape:

- `prompts/core/` holds the eight tool-neutral prompts.
- `templates/` holds the files installed into a target repo.
- `kit/` holds the catalog, the validation checks, the safe installer, and one adapter per tool.
- `docs/` holds onboarding, the workflow, the writing standard, the adapter model, contributing, and releasing.

At v0.1.0, Claude Code is the primary target, with Codex and Cursor as adapters over the same prompt pack. The catalog is JSON, and the kit is stdlib only, so a clean clone runs with just Python. The installer plans first and then applies. It supports a dry-run, merges the Claude settings file safely, and never overwrites a file the user owns. Deny rules cover secrets only.

Later changes extended this base: v0.3.0 added GitHub Copilot as a fourth adapter, and v0.10.0 added a Claude Code plugin as a second distribution channel.

First release (v0.1.0) scope: the eight prompts, three adapters, the catalog, the checks, the installer, the docs, and the tests. No eval, no judge, no governance.

## Alternatives

- Clean-fork the earlier kit. Rejected: it would carry the plugin, marketplace, and governance shape we are dropping. The eval tools would keep leaking back in.
- YAML catalog with PyYAML. Rejected: a dependency the installer would have to carry, against the stdlib-only goal. JSON is enough.
- Ship only as a Claude plugin. Rejected: it would leave Codex and Cursor without a path and would not cover the settings merge. ADR-0004 later adds a plugin as an extra Claude channel, not as a replacement.

## Consequences

- One prompt pack backs every tool, so the workflow does not change with the tool. Adding a tool is a new adapter, not a new pack.
- The catalog plus checks catch files that fall out of sync with what is listed, so the kit stays honest as it grows.
- This reverses if a future need genuinely requires eval or governance in the same repo. That would be a new decision recorded here.
