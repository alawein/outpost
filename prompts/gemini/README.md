# Gemini CLI prompt overlay

The core pack in `prompts/core/` is the default prompt set. The Gemini CLI adapter installs the project guide as `GEMINI.md` and writes each core prompt except `converge` (Claude-only) as a custom command at `.gemini/commands/outpost/<name>.toml`, invoked as `/outpost:<name>`. That namespace keeps the adapter from overwriting commands you already have. The guide points to the prompt pack for planning, review, testing, and handoff work.

Put a file here only when Gemini CLI needs a different prompt. A file with the same name as a core prompt overrides the core version when the Gemini CLI adapter installs.

This directory is empty on purpose. The core pack already covers Gemini CLI.
