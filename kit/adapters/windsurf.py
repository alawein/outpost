"""Windsurf adapter. Windsurf reads workspace rules from `.windsurf/rules/*.md` (the frontmatter
`trigger` says when a rule applies) and workflows from `.windsurf/workflows/*.md`, each invoked as
`/<file-stem>`. The rule installs with `trigger: always_on`, so the pack is in every session. The
prompts install as workflows named `outpost-<name>`: the prefix keeps every file at the top level
(subdirectory scanning is undocumented) and can never overwrite a user's own workflow. Windsurf
caps a rule or workflow at 12,000 characters; the core prompts sit well under that, and the
adapter refuses one over the cap rather than install a file Windsurf would reject. `.devin/rules/`
is a newer alias with precedence, but `.windsurf/rules/` is still read, so the older path is the
one both product names honor.
"""
from __future__ import annotations

import pathlib

from .base import Action, load_prompts, read_template

# the documented per-file cap; the test suite imports this so the two cannot drift
WINDSURF_LIMIT = 12000


def plan(kit_root: pathlib.Path, project_root: pathlib.Path, terse: bool = False,
         select=None, tolerant: bool = False) -> list[Action]:
    actions: list[Action] = []

    actions.append(Action(
        path=".windsurf/rules/outpost.md",
        content=read_template(kit_root, "windsurf-rules.md"),
        mode="create",
        note="always-on rule (left alone if you already have one)",
    ))

    for name, content in load_prompts(kit_root, "windsurf", select=select):
        if len(content) > WINDSURF_LIMIT:
            raise ValueError(f"{name}: {len(content)} characters exceeds Windsurf's "
                             f"{WINDSURF_LIMIT}-character workflow cap")
        actions.append(Action(
            # a prompt already carries name and description frontmatter, which is what a
            # workflow wants, so the content installs unchanged
            path=f".windsurf/workflows/outpost-{name}.md",
            content=content,
            mode="write",
            note=f"core prompt as a Windsurf workflow, invoked as /outpost-{name}",
        ))
    return actions
