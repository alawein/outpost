# Claude prompt overlay

The core pack in `prompts/core/` is the default prompt set. The Claude adapter installs each core prompt as a Claude skill at `.claude/skills/<name>/SKILL.md`. It keeps the prompt text the same. The frontmatter `description` becomes the skill trigger, so Claude can load the right prompt on its own.

Put a file here only when Claude needs a different prompt. A file with the same name as a core prompt, for example `code-review.md`, overrides the core version when the Claude adapter installs. Keep overrides rare so the adapters stay aligned.

This directory is empty on purpose. The core pack already covers Claude.
