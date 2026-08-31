"""outpost: helps coding agents read a repo, plan, edit, test, review, prep PRs,
and hand off. Claude Code is the primary target; Codex, Cursor, GitHub Copilot, Windsurf, and
Gemini CLI are adapters.

The core is stdlib only. `kit.catalog` is the source of truth for what ships, `kit.checks`
validates the repo against it, `kit.installers` merges config safely, and `kit.adapters` renders
the kit into a target project per tool.
"""

KIT_VERSION = "1.0.0"
