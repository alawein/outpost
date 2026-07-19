# 0004: Package the kit as an additive Claude Code plugin

Status: Accepted
Date: 2026-06-28

## Context

Today the kit reaches a project one way: the per-repo installer (ADR-0001) writes the prompts for the chosen tool. In Claude Code, each prompt lands as a skill under `.claude/skills/<name>/SKILL.md`. It loads on its own from its description, so a user describes a task and the matching prompt activates. The user never types a command. In Codex, Cursor, and GitHub Copilot, the prompts land as files the user points at by hand. There are no typed slash commands anywhere. There is also no single install that a user runs once to get the kit across projects.

Claude Code also supports plugins. A plugin is a packaged bundle: manifest, skills, commands, and hooks. A user installs it once from a marketplace or a path, and it exposes typed `/` commands. The kit does not offer that path today. A plugin would give Claude users one install and named commands, and it would make the kit easier to find. The risk is that a plugin is Claude-only, which cuts against ADR-0001's tool-agnostic choice. Hand-authoring a plugin would also fork the prompt set away from the catalog.

## Decision

Add a Claude Code plugin as a second distribution channel. The per-repo installer stays the cross-tool path and is not replaced. The catalog stays the place that lists shipped prompt names. The plugin is generated from it, never hand-maintained beside it.

- One pack, two channels. The plugin vendors the same prompts the catalog lists, as plugin skills, so the stage prompts keep loading by description.
- A small typed-command set, generated from the catalog, layered on top:
  - `/stress <target> [intensity]`: one adversarial command in place of the four scrutiny prompts (`interrogate`, `self-refute`, `grill`, `premortem`), selected by target (the ask, your own doc, plan, diff, or output) and intensity (quick or extensive).
  - `/ship`: the pre-merge sequence, self-refute then review-change then prepare-pr.
  - `/drive`: an optional walkthrough of plan-change to implement-change to write-tests.
- At acceptance, the build was deferred. It shipped in v0.10.0 as a generated plugin, with later releases adding hooks, agents, and the output style.

Two tests must pass before the build, each named before any code:

- Added channel, not a fork. The plugin must be generated from the catalog and reuse the same prompt files. The stdlib-only installer must keep working unchanged. If building the plugin forces a second copy of the prompts or a non-stdlib dependency, the claim failed and the design is reworked, not shipped.
- The scrutiny merge holds only if it routes right. If folding the four scrutiny prompts into one `/stress` makes the model pick the wrong mode, such as self-refuting when it should question the ask, the merge failed and the four stay separate. This is cheap to test before the command ships.

## Alternatives

- A full pivot: make the plugin the primary distribution and retire the installer. Rejected. It reverses ADR-0001, abandons the Codex, Cursor, and Copilot users, and ties the kit to one tool. The plugin is an added channel, not a replacement.
- Hand-author the plugin separately from the catalog. Rejected. A second hand-maintained list of prompts and commands falls out of sync with the catalog. That is the failure the checks on `template_refs` and the planned doc checks exist to prevent. The plugin must be generated.
- Stay as is: skills plus the installer, no plugin. Rejected as the end state, kept as the baseline. It works, but it offers no one-shot install, no typed commands, and no marketplace discovery. Those are the reasons to add the channel. The status quo remains correct until the plugin is built.
- Composite commands only, with the scrutiny four left separate. A valid smaller option: ship `/ship` and `/drive` without `/stress`. Folded into the decision as the fallback if the scrutiny-merge test fails.

## Consequences

- This widens distribution without reversing ADR-0001. The installer stays the cross-tool path and the recommended start. The plugin is the Claude-only convenience layer.
- The commands are new public API. Adding or removing a command is a recorded decision, not a quiet change, held to the same standard as prompts and adapters.
- The plugin must stay generated from the catalog. If it needs hand-editing per command, it has begun to fall out of sync. That is the signal to stop and reconsider, not to patch by hand.
- If the scrutiny merge passes its test, the plugin keeps one `/stress` in place of four commands, and whether the underlying prompts also merge is a separate decision recorded later.
- A generated plugin needs its own check, so a command that names a missing prompt fails the check the way a dangling template reference does. The later build adds that as `plugin_sync`.
- Widening the commands beyond this set is a new decision recorded here, not a quiet addition.
