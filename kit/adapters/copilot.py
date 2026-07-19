"""GitHub Copilot adapter. Copilot reads repo-wide custom instructions from
`.github/copilot-instructions.md` and reusable prompt files from `.github/prompts/*.prompt.md`. It
has no skills or plugins, so the instructions file folds in the pack and each core prompt installs
as a `.prompt.md` file. A different config shape from the other three (a single instructions file
plus a `.github/prompts/` dir), which is the point: it tests that the adapter model holds.
"""
from __future__ import annotations

import pathlib

from .base import Action, load_prompts, read_template


def plan(kit_root: pathlib.Path, project_root: pathlib.Path, terse: bool = False,
         select=None) -> list[Action]:
    actions: list[Action] = []

    actions.append(Action(
        path=".github/copilot-instructions.md",
        content=read_template(kit_root, "copilot-instructions.md"),
        mode="create",
        note="repo instructions (left alone if you already have one)",
    ))

    for name, content in load_prompts(kit_root, "copilot", select=select):
        actions.append(Action(
            # Copilot's prompt-file extension is `.prompt.md`, kept under .github/prompts/ so it
            # never collides with a user's own instructions file or another tool's paths
            path=f".github/prompts/{name}.prompt.md",
            content=content,
            mode="write",
            note="core prompt as a Copilot prompt file",
        ))
    return actions
