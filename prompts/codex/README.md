# Codex prompt overlay

The core pack in `prompts/core/` is the default prompt set. Codex has no skills or plugins, so the Codex adapter installs every core prompt except `converge` (Claude-only) as a plain file under `.agents/prompts/` and a guide as `AGENTS.md`. The guide names eight common prompts and their triggers, not the full pack, and carries no file links. Codex reads `AGENTS.md` when a session starts; open the installed prompt file that fits the step by hand.

Put a file here only when Codex needs a different prompt. A file with the same name as a core prompt overrides the core version when the Codex adapter installs.

This directory is empty on purpose. The core pack already covers Codex.
