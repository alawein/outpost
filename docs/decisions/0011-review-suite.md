# 0011: The review suite

Date: 2026-07-09. Status: accepted. Widens the prompt-pack scope of ADR-0002.

## Context

The kit reviewed one change well (`code-review`, `grill`) but had no whole-repo audit, no
behavior-preserving cleanup pass, and no way to rank a findings list before acting on it.
Findings piled up unranked or were fixed ad hoc. The ROADMAP rule says further prompts stay
out unless a new ADR widens scope.

## Decision

Add three core prompts and expose a five-command review suite under `/ack:*`:

- `repo-review` (new): health audit of a whole repo; findings shaped for triage.
- `simplify` (new): reuse and simplification cleanups on changed code, behavior preserved.
- `triage` (new): confirm, rank, and route a findings list; nothing dropped silently.
- `code-review` (rename of `review-change`, so the command and prompt share one name).
- `prove` (existing): claims checked against the source of truth.

All five are core prompts, so every adapter ships them; the commands are the Claude Code
front door.

## Consequences

- The core pack is 24 prompts; the plugin has 9 commands.
- `review-change` no longer exists as a name; docs and templates say `code-review`. ADRs and
  CHANGELOG history keep the old name unedited.
- The suite composes: repo-review or code-review find, triage ranks, simplify and the build
  prompts fix, prove checks the claims that ship.
