# 0005: Domain groups for Claude-only prompts

Status: Accepted
Date: 2026-06-29

## Context

ADR-0001 built the kit as a tool-agnostic core: the same prompts install under codex, cursor,
copilot, and claude. ADR-0003 added subset selection so a team installs part of the catalog.
ADR-0004 added a Claude Code plugin as a second distribution channel, keeping the installer as
the cross-tool path.

Absorbing claude-kit's eval/guides and ops skills changes the picture. Those skills are Claude-specific and tied to an internal evaluation system. They rely on Claude Code commands and domain knowledge that the codex, cursor, and copilot adapters cannot render. Adding them to the core catalog would ship Claude-only prompts into Codex and Cursor projects, where they do nothing and add noise. Excluding them entirely denies the Claude users who need them. Neither is right.

## Decision

Add a second prompt class through a `group` field on each catalog entry.

- `core` is the default, meaning cross-tool. A prompt without a `group` field is treated as
  `core`, so the change is backward compatible with every existing entry.
- `domain:<name>` means Claude-only and opt-in. A user passes `--with-domain <name>` to the
  claude adapter to install a domain alongside the core set.

Routing by adapter: codex, cursor, and copilot install core prompts only and ignore all domain
entries, regardless of any `--with-domain` flag. The claude adapter installs core plus any
opted-in domains. The plugin vendors core plus all domains.

On disk, domain prompts live under `prompts/domains/<name>/`. The `group` value in the catalog
keeps the colon (`domain:eval`) because that is how the engine reads it. The directory
name drops the colon (`prompts/domains/eval/`) because Windows forbids `:` in file paths.
The two forms are distinct; the installer maps one to the other.

The install manifest gains an `opted_in_domains` list recording which domains the user chose.
That lets `--verify` and a future update path check intent rather than guessing from what is on
disk.

At acceptance, this sub-project shipped the engine only. The domain prompts landed later: `eval`, `guides`, and `ops` in v0.16.0, guide repair prompts in v0.19.0, and the `device` pack in v0.20.0. The default cross-tool install still stays on core prompts unless a Claude install opts into a domain.

Two falsifiers, each checkable before any domain prompt lands:

- A codex, cursor, or copilot install ships zero domain files regardless of `--with-domain`. If
  any domain file appears under those adapters, the routing failed.
- With no domain prompts present, a default install and the gate produce output byte-identical to
  v0.14.0. Any diff there signals a regression in the core path.

## Alternatives

- Keep all prompts in one flat core and install everywhere; let Claude-only prompts be no-ops
  elsewhere. Rejected: silent no-ops are noise for Codex and Cursor users and make the kit
  harder to audit. A prompt that does nothing under one adapter is a defect, not a feature.
- A separate repo for Claude-only prompts, outside the kit. Rejected: two catalogs to maintain
  fall out of sync, which is exactly what the template-ref check exists to prevent. One catalog,
  one check, two classes.
- Domains as a separate install command rather than a flag on the existing one. Rejected for now:
  a new command adds one more interface with no gain at this scale. The existing installer keeps the
  model consistent with `--only`/`--exclude` (ADR-0003). This reverses if domain installs grow
  complex enough to need their own flow.

## Consequences

- Backward compatible by default. An absent `group` is `core`, so all existing catalog entries
  and all v0.14.0 installs are unchanged.
- Domains extend the tailoring axis from ADR-0003. Subset selection (`--only`/`--exclude`)
  applies within the set a user opted into; the two are orthogonal.
- The counts and doc-truth checks must account for the split. A check that only counts total prompts can pass while a domain prompt leaks into a core install.
- The manifest grows one field. Readers of older manifests must treat its absence as no
  opted-in domains.
- The plugin grows as new domain prompts are added. That is expected.
- Widening the domain set or adding an adapter that handles domains differently is a new
  decision recorded here, not a quiet addition.
