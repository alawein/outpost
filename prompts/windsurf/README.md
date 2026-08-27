# Windsurf prompt overlay

The core pack in `prompts/core/` is the default prompt set. The Windsurf adapter installs the always-on rule at `.windsurf/rules/outpost.md` and writes each core prompt except `converge` (Claude-only) as a workflow at `.windsurf/workflows/outpost-<name>.md`, invoked as `/outpost-<name>`. That prefix keeps the adapter from overwriting workflows you already have. The rule points to the prompt pack for planning, review, testing, and handoff work.

Put a file here only when Windsurf needs a different prompt. A file with the same name as a core prompt overrides the core version when the Windsurf adapter installs.

This directory is empty on purpose. The core pack already covers Windsurf.
