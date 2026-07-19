"""Claude Code adapter. The primary target.

Installs the project guide, the core prompts as Claude skills (auto-discovered, so the right prompt
loads on its own), a settings merge that adds secret-only deny rules, and an optional terse output
style. No plugin or marketplace machinery: skills plus a settings merge are enough.
"""
from __future__ import annotations

import pathlib

from .base import Action, TERSE_OUTPUT_STYLE, load_prompts, read_template
from ..installers.settings import merged_text


def plan(kit_root: pathlib.Path, project_root: pathlib.Path, terse: bool = False,
         select=None) -> list[Action]:
    actions: list[Action] = []

    actions.append(Action(
        path="CLAUDE.md",
        content=read_template(kit_root, "CLAUDE.md"),
        mode="create",
        note="project guide (left alone if you already have one)",
    ))

    for name, content in load_prompts(kit_root, "claude", select=select):
        actions.append(Action(
            path=f".claude/skills/{name}/SKILL.md",
            content=content,
            mode="write",
            note="core prompt installed as a Claude skill",
        ))

    output_style = "terse" if terse else None
    settings_path = project_root / ".claude" / "settings.json"
    existing = settings_path.read_text(encoding="utf-8") if settings_path.exists() else None
    actions.append(Action(
        path=".claude/settings.json",
        content=merged_text(existing, output_style),
        mode="merge",
        note="add secret-only deny rules" + (" and set the terse output style" if terse else ""),
    ))

    if terse:
        actions.append(Action(
            path=".claude/output-styles/terse.md",
            content=TERSE_OUTPUT_STYLE,
            mode="write",
            note="optional terse output style",
        ))
    return actions
