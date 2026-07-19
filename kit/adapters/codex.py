"""Codex adapter. Codex reads AGENTS.md and has no skills or plugins, so the prompts install as
plain files under `.agents/prompts/` and AGENTS.md folds them in. No assumption that Codex can load
a Claude skill or plugin.
"""
from __future__ import annotations

import pathlib

from .base import Action, load_prompts, read_template


def plan(kit_root: pathlib.Path, project_root: pathlib.Path, terse: bool = False,
         select=None) -> list[Action]:
    actions: list[Action] = []

    actions.append(Action(
        path="AGENTS.md",
        content=read_template(kit_root, "AGENTS.md"),
        mode="create",
        note="agent guide (left alone if you already have one)",
    ))

    for name, content in load_prompts(kit_root, "codex", select=select):
        actions.append(Action(
            path=f".agents/prompts/{name}.md",
            content=content,
            mode="write",
            note="core prompt for Codex to apply by hand",
        ))
    return actions
