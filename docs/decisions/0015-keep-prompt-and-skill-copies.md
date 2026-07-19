# 0015: Keep the prompt and plugin-skill copies

Status: Accepted
Date: 2026-07-11

## Context

The 24 core prompts exist twice in the tree: authored as `prompts/core/<name>.md`, and mirrored
byte-for-byte as `plugins/ack/skills/<name>/SKILL.md`. `build.py plugin` generates the mirror and
the `plugin_sync` check fails on any drift. A simplification review flagged this as the largest
duplication in the repo and asked whether to collapse it to one home.

## Decision

Keep both copies. `prompts/core` stays the authored source; `plugins/ack/skills` stays the
generated mirror the Claude plugin ships. The Claude plugin format mandates the nested
`skills/<name>/SKILL.md` shape, so the only real lever is which copy is the source. Flat
`prompts/core/<name>.md` is better to author and read than a nested skill directory, and the
prompts are tool-neutral (they install to Codex, Cursor, and Copilot too), so they should not live
under a Claude-plugin path.

## Alternatives

- Collapse to `plugins/ack/skills` as the single home and delete `prompts/core`. Rejected: it
  buries tool-neutral prompts under a Claude-plugin path and forces nested `SKILL.md` authoring,
  trading a worse authoring surface for less tree noise.
- Stop committing the mirror and generate it at package time. Rejected: the marketplace installs
  from the committed `./plugins/ack` directory, so a clone with no `SKILL.md` files cannot install
  the plugin.

## Consequences

- The duplication stays, but it is drift-proof (`plugin_sync` fails on any mismatch) and costs one
  build command (`python tools/build.py plugin`) after a prompt edit.
- The question is closed. A future audit that re-flags the duplication reads this record first.
- Reverse it only if the Claude plugin format stops requiring a committed nested skills tree.
