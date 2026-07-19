# 0007: Kit identity, tool-neutral core with a walled-off team extension

Status: Accepted
Date: 2026-07-01

## Context

The catalog is 21 tool-neutral core prompts plus four Claude-only domain packs (eval, guides, ops, device). Only Claude Code gets auto-loading skills, the settings merge, the domain packs, and the terse output style; the other three tools install byte-identical core prompt text with no overrides. The README's headline and four equal-weight tool badges presented four-tool parity the shipped catalog does not have, and met a newcomer with one team's internal infrastructure as if it were shared core. ADR-0005's reversal clause ("widening the domain set is a new decision recorded here") came due.

## Decision

Keep both identities but make the split visible where it matters. Lead the README and onboarding with the tool-neutral core as the primary path, and present the Claude-only domain packs as a clearly labeled, secondary "team extension" section, out of the headline sentence and the badge row. No repo split. No change to the domain-pack mechanism, the gate, or the catalog engine.

## Alternatives

- Split the repo: move domain packs into a separate team-scoped extension, leaving a pure tool-neutral core. Rejected for now: real cost to extract the catalog and plugin machinery across two repos, with no near-term outside-adoption plan to justify it.
- Own the identity: reframe as this team's coding-plus-eval harness and drop the neutral-core lead. Rejected: the core prompts genuinely are tool-neutral and worth leading with, and ADR-0001's small cross-tool core ambition still holds.

## Consequences

Cheapest honest fix, reversible, and does not foreclose the split later. It fixes framing, not engineering surface: the gate and the contract weight on domain prompts are unchanged. It stays honest only while the extension section stays walled off and labeled Claude-only. If domain packs keep growing past the core, or an outside-adoption or open-source plan appears, revisit the split.
