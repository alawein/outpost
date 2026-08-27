"""Gemini CLI adapter. Gemini CLI reads its project context from `GEMINI.md` at the project root
and custom commands from `.gemini/commands/<name>.toml`. A subdirectory namespaces a command, so
`.gemini/commands/outpost/plan-change.toml` is `/outpost:plan-change`; the namespace keeps the kit's
commands clear of a user's own. A command file is TOML with a `description` and a `prompt`. The
prompt is the core prompt's body without its frontmatter block: the frontmatter is skill metadata
Gemini has no use for, and its `description` becomes the command's description instead.
"""
from __future__ import annotations

import pathlib
import re

from .base import Action, load_prompts, read_template
from ..checks import frontmatter_field, split_frontmatter

# a raw control character (tab and newline aside) is invalid in both TOML string forms
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def to_command_toml(name: str, content: str) -> str:
    """Render one core prompt as a Gemini command file. The description is a TOML basic string
    (backslash and double quote escaped). The prompt is a TOML multi-line literal string, which has
    no escapes at all, so it cannot hold its own delimiter or a control character. Gemini CLI also
    expands `!{...}` (a shell command) and `@{...}` (a file injection) inside a command prompt, so a
    body carrying either would run at /outpost:<name> time instead of reading as text. Each case
    raises rather than writing a file Gemini would reject or execute."""
    fm, body = split_frontmatter(content)
    if _CONTROL.search(body):
        raise ValueError(f"{name}: prompt body has a control character a TOML literal string "
                         "cannot hold")
    if "'''" in body:
        raise ValueError(f"{name}: prompt body contains ''' and cannot be a TOML literal string")
    for seq in ("!{", "@{"):
        if seq in body:
            raise ValueError(f"{name}: prompt body contains {seq}, which Gemini CLI runs as a "
                             "shell command or file injection")
    lines: list[str] = []
    desc = frontmatter_field(fm, "description")
    if desc is not None:
        if _CONTROL.search(desc):
            raise ValueError(f"{name}: description has a control character a TOML string cannot hold")
        desc = desc.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'description = "{desc}"')
    # TOML drops the newline right after the opening delimiter, so the body starts on its own line
    lines.append("prompt = '''\n" + body.strip("\n") + "\n'''")
    return "\n".join(lines) + "\n"


def plan(kit_root: pathlib.Path, project_root: pathlib.Path, terse: bool = False,
         select=None, tolerant: bool = False) -> list[Action]:
    actions: list[Action] = []

    actions.append(Action(
        path="GEMINI.md",
        content=read_template(kit_root, "GEMINI.md"),
        mode="create",
        note="project guide (left alone if you already have one)",
    ))

    for name, content in load_prompts(kit_root, "gemini", select=select):
        actions.append(Action(
            path=f".gemini/commands/outpost/{name}.toml",
            content=to_command_toml(name, content),
            mode="write",
            note=f"core prompt as a Gemini command, invoked as /outpost:{name}",
        ))
    return actions
