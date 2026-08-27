# Cursor prompt overlay

The core pack in `prompts/core/` is the default prompt set. The Cursor adapter installs the repo rule at `.cursor/rules/outpost.mdc` and writes each core prompt except `converge` (Claude-only) under `.cursor/rules/outpost/<name>.md`. That kit subdirectory keeps the adapter from overwriting rules you already have. Cursor selects a rule by its description. The repo rule points to the prompt pack for planning, review, testing, and handoff work.

Put a file here only when Cursor needs a different prompt. A file with the same name as a core prompt overrides the core version when the Cursor adapter installs.

This directory is empty on purpose. The core pack already covers Cursor.
