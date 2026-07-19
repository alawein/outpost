# 0003: Team tailoring by prompt subset

Status: Accepted
Date: 2026-06-28

## Context

ADR-0001 ships the kit as one complete pack: the installer writes every prompt for the chosen tool, all or nothing. That works for a newcomer who wants the whole workflow. It does not work for a team that wants only part of it. A team may run its own review process and want the build and test prompts but not `review-change`. It may want the main flow but not the scrutiny group. Today its only option is to install everything and delete what it does not want, which the next install restores. The kit has no supported way to install a subset and no record of what a project chose.

## Decision

Add per-prompt subset selection to the installer, and record the choice in a manifest.

- Two flags: `--only <names>` installs the named prompts, plus the tool's guide and settings. `--exclude <names>` installs everything except the named prompts. They are mutually exclusive. A name that is not a catalog prompt is an error, so a typo fails loudly instead of silently installing nothing.
- An install manifest: the installer writes a small file recording which prompts were installed and at what kit version. A later run, a `--verify`, or a teammate can see the project's choice rather than guessing from what is on disk.
- The full pack stays the default. With no selection flag, the installer behaves exactly as before.

The test this passes: does subset selection stay inside the stdlib-only, plan-then-apply, never-overwrite-a-user-file model, and add no new tools to the prompts themselves? It does. The flags filter the same action list the adapters already produce. The manifest is one more kit-owned file for the existing write and verify paths. No prompt changes, no dependency.

## Alternatives

- Named profiles (for example `--profile minimal`, `--profile full`). Rejected: a profile is a second place that lists what belongs together. It can fall out of sync with the catalog, and every team wants a slightly different set, so the profile list grows without end. `--only`/`--exclude` over the catalog names cover every set with no new list to maintain. A profile is sugar a team can script on top of the flags if it wants one.
- Keep all or nothing and tell teams to delete what they do not want. Rejected: the next install restores the deleted files, because the kit-owned write path is idempotent by design, so deletion is not a stable choice. The whole point is a choice that survives a re-install.
- A config file instead of flags. Rejected for now: a file is the right home once selections get complex, but the manifest already records the outcome, and flags cover the common case without a new format. This reverses if selections grow beyond what a flag can carry.

## Consequences

- This reverses ADR-0001's implicit all-or-nothing install. The complete pack is still the default and the recommended start. Subset selection is opt-in.
- The manifest gives `--verify` and a future update path a record of intent, so a project can be checked against what it chose, not only against the full pack.
- The catalog stays the place that lists shipped prompt names. Selection is a filter over it, so a renamed or dropped prompt shows as a clear error in `--only`/`--exclude`, not a silent miss.
- Widening this to grouped or profile selection is a new decision recorded here, not a quiet addition.
