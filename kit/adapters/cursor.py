"""Cursor adapter. Installs the repo rule at `.cursor/rules/outpost.mdc` and the core prompts
under `.cursor/rules/outpost/`, so Cursor applies the kit's plan, review, test, and handoff
discipline. No unsupported Cursor features: just rule files and the prompt pack.
"""
from __future__ import annotations

import pathlib

from .base import Action, load_prompts, read_template


def plan(kit_root: pathlib.Path, project_root: pathlib.Path, terse: bool = False,
         select=None, tolerant: bool = False) -> list[Action]:
    actions: list[Action] = []

    actions.append(Action(
        path=".cursor/rules/outpost.mdc",
        content=read_template(kit_root, "cursor-rules.md"),
        mode="create",
        note="repo rule (left alone if you already have one)",
    ))

    for name, content in load_prompts(kit_root, "cursor", select=select):
        actions.append(Action(
            # namespaced under a kit subdir so an install never overwrites a user's own rule of the
            # same name (the other two adapters isolate their files the same way)
            path=f".cursor/rules/outpost/{name}.md",
            content=content,
            mode="write",
            note="core prompt for Cursor to reference",
        ))
    return actions
