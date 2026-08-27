# Copilot prompt overlay

The core pack in `prompts/core/` is the default prompt set. GitHub Copilot has no skills or plugins, so the Copilot adapter installs each core prompt except `converge` (Claude-only) as a `.prompt.md` file under `.github/prompts/` and instructions as `.github/copilot-instructions.md`. The instructions file names eight common prompts and their triggers, not the full pack. Copilot adds that instructions file as context automatically. Use the matching prompt file when needed. These prompt files are available in the VS Code, Visual Studio, and JetBrains Copilot integrations.

Put a file here only when Copilot needs a different prompt. A file with the same name as a core prompt overrides the core version when the Copilot adapter installs.

This directory is empty on purpose. The core pack already covers Copilot.
