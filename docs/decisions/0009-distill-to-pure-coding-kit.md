# 0009: Distill to a pure coding kit, removing the eval, guides, device, and ops domains

Status: Accepted
Date: 2026-07-09

## Context

The kit's scope has swung twice. ADR-0001 shipped a tool-agnostic core and dropped eval and the
judge ("No eval, no judge"), reversible only by a new record. ADR-0005 added a domain-group engine:
Claude-only prompt packs (eval, guides, ops, device), opt-in with `--with-domain`. ADR-0007 set the
kit's identity as "lead with the tool-neutral core, wall off the domain packs as a team extension."
ADR-0008 added the `kit.eval` front door, a quarantined leaf importing the touchstone engine,
reversing ADR-0001's eval scope.

The result is a kit that is two things at once: a portable coding-discipline kit for any AI coding
tool (Claude Code, Codex, Cursor), and an AGI-internal eval, guides, and device harness bolted on as
Claude-only packs. The second identity carries weight the first does not need: a domain-routing
engine in the catalog and installer, an eval leaf with a cross-repo dependency on touchstone, and 26
domain prompts that only render under Claude. The eval capability's real home is touchstone; the
kit's domain prompts are a distribution copy.

## Decision

Return the kit to ADR-0001's intent: a pure coding kit of 21 cross-tool coding-discipline skills.
Remove all four domains (eval, guides, device, ops) and the machinery that served them.

- Delete `prompts/domains/` in full (26 prompts) and the `kit.eval` front door with its
  `eval_isolation` check.
- Remove the domain-routing surface: the catalog `domain:` group, the installer `--with-domain` path
  and the `opted_in_domains` manifest field, `docs/domains.md`, the template domain scaffolds, the
  `/eval` and `/session-loop` plugin commands, the `pipeline-auditor` agent, and the three
  eval/device hooks (block_held_out, guard_external_send, check_task_schema); keep nudge_context.
- Core is exactly the 21 skills already under `prompts/core/`. No domain or ops prompt is promoted:
  summarize and digest are reporting skills, file-issue and sync-slack route to an external tracker
  or chat, and none is a coding-discipline skill.

This supersedes ADR-0005 (domain groups) and ADR-0008 (eval front door) in full. It retires the
"team extension" concept of ADR-0007 while affirming that ADR's core principle, lead with the
tool-neutral core. ADR-0003's tailoring axis (`--only`/`--exclude` over the core set) survives
unchanged; only the orthogonal domain axis is removed.

## Alternatives

- Keep the domains as Claude-only opt-in (the ADR-0005/0007 status quo). Rejected: it keeps the kit
  two products, ties a release to the touchstone engine, and ships prompts that render in only one
  tool.
- Relocate the domain prompts to touchstone rather than delete. Rejected by the owner: the eval
  capability already lives in touchstone via the engine, the prompts are a copy, and git history
  preserves them if ever wanted.
- Promote the clean ops prompts (summarize, digest) into core. Rejected: they are reporting, not
  coding-discipline, skills; a minimal pure kit excludes them, and file-issue and sync-slack carry
  tracker and chat wiring that would re-introduce tool-coupling into a cross-tool core, the defect
  ADR-0005 was written to avoid.

## Consequences

The kit becomes one honest thing: 21 tool-neutral coding-discipline skills that install into Claude
Code, Codex, and Cursor alike. The installer and catalog lose the domain axis and get simpler; the
core package stays stdlib-only without needing the `eval_isolation` guard, because there is no eval
leaf to quarantine. The packaging surface shrinks (fewer commands, agents, and hooks).

What this gives up: the AGI-internal eval, guides, and device workflows no longer install from the
kit. They were not shipped dependencies. A scan of 108k+ files across the sibling repos and the hub
found zero external consumers of the cut content, so nothing downstream breaks; teams that ran those
workflows use touchstone directly.

Reversal condition: if a future need requires shipping an eval or device pack from the kit again, a
new ADR reverses this one, as ADR-0008 reversed ADR-0001.

Verification caveat: the pre-cut red-team's premortem pass failed mid-stream, so the keep-side risk
assessment rests on the grill pass plus three impact scans, not a second independent premortem. The
delete-side safety was independently confirmed by the scan.
