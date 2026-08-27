"""The required files and directories are present. A missing one is a broken clone, caught here
before any other check tries to read it."""
from __future__ import annotations

import pathlib

REQUIRED_FILES = (
    "README.md", "CLAUDE.md", "install.py", "validate.py", "pyproject.toml", "CHANGELOG.md",
    "LICENSE", ".gitignore",
    "docs/onboarding.md", "docs/workflow.md", "docs/writing-standard.md", "docs/adapters.md",
    "docs/contributing.md", "docs/releasing.md", "docs/ROADMAP.md",
    "docs/decisions/0000-template.md", "docs/decisions/README.md",
    "templates/CLAUDE.md", "templates/AGENTS.md", "templates/cursor-rules.md",
    "templates/copilot-instructions.md", "templates/windsurf-rules.md", "templates/GEMINI.md",
    "kit/catalog/catalog.json",
)
REQUIRED_DIRS = (
    "kit", "kit/catalog", "kit/checks", "kit/installers", "kit/adapters",
    "prompts/core", "prompts/claude", "prompts/codex", "prompts/cursor", "prompts/copilot",
    "prompts/windsurf", "prompts/gemini",
    "templates", "docs", "docs/decisions", "tests",
)


def run(root: pathlib.Path) -> tuple[bool, str]:
    missing = [f for f in REQUIRED_FILES if not (root / f).is_file()]
    missing += [f"{d}/" for d in REQUIRED_DIRS if not (root / d).is_dir()]
    if missing:
        return False, "missing: " + ", ".join(missing[:12])
    return True, f"{len(REQUIRED_FILES)} files and {len(REQUIRED_DIRS)} directories present"
