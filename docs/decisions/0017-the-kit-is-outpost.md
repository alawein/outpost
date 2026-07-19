# 0017: The kit is Outpost

Date: 2026-07-18. Status: accepted. Supersedes ADR-0010 (the kit is ACK).

## Context

This kit began as an internal tool (ACK, "AGI's Coding Kit") maintained for a company team, with
a proprietary license, company-owned CODEOWNERS, and a Linear-integration workflow tied to that
company's issue tracker. It is being forked into a personal, MIT-licensed open source project so
others outside that company can adopt it.

## Decision

One name: Outpost. The plugin is `plugins/outpost/`, so every command surfaces as `/outpost:*`.
The installer state dir is `.outpost/`. The distribution name is `outpost`. The Python package
stays `kit`, unchanged from ADR-0010's reasoning: internal plumbing, invisible to users.

The fork also drops, rather than renames, everything tied to the company rather than the tool
itself: the Linear issue-sync integration, the proprietary license (now MIT), and the
company-owned CODEOWNERS entries (now `@alawein` alone). The `traces` check's "personal handle"
pattern (ADR-0012) is retired, since `alawein` is now the project's legitimate public owner, not
a leaked personal trace.

The version resets to 0.1.0. The predecessor's version history (v0.1 through v0.25) and its
`CHANGELOG.md` are not carried forward into the public repo; this repo's own `docs/decisions/`
and `docs/audit/` stay as the historical record of the design decisions that produced today's
tree, per this project's own append-only ADR convention.

## Consequences

- Docs, templates, and the plugin/installer identity all say Outpost; `ack`/`ACK`/`AGI` survive
  only in ADR/audit history predating this fork (ADR-0001 through ADR-0016, `docs/audit/`) and in
  this record.
- There is no migration path from an ACK install to an Outpost install (no shared user base to
  migrate); a `.ack/` state dir from an ACK install is simply not recognized.
- The GitHub repo is `alawein/outpost`, unrelated to the predecessor's `agi-inc/ACK`.
