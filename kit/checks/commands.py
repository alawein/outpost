"""Every plugin command file is well-formed: a frontmatter description long enough to serve as a
real trigger, and a body that is not a stub. Mirrors kit/checks/prompts.py's structural lint,
scoped to plugins/outpost/commands/*.md, which today gets only command_lists' cross-reference
check and no shape check of its own.
"""
from __future__ import annotations

import pathlib

from . import frontmatter_field, split_frontmatter

MIN_DESCRIPTION_CHARS = 40
MIN_BODY_WORDS = 15


def lint_command(text: str, stem: str) -> list[str]:
    errors: list[str] = []
    fm, body = split_frontmatter(text)
    desc = frontmatter_field(fm, "description")
    if not desc:
        errors.append(f"{stem}: missing frontmatter description")
    elif len(desc) < MIN_DESCRIPTION_CHARS:
        errors.append(f"{stem}: description too short to be a real trigger ({len(desc)} chars)")
    if not body.strip():
        errors.append(f"{stem}: body is empty")
    elif len(body.split()) < MIN_BODY_WORDS:
        errors.append(f"{stem}: body too thin ({len(body.split())} words); a command is not a stub")
    return errors


def run(root: pathlib.Path) -> tuple[bool, str]:
    commands = root / "plugins" / "outpost" / "commands"
    files = sorted(commands.glob("*.md"))
    if not files:
        return False, "no command files found under plugins/outpost/commands/"
    errors: list[str] = []
    for p in files:
        errors += lint_command(p.read_text(encoding="utf-8"), p.stem)
    if errors:
        return False, "; ".join(errors[:10])
    return True, f"{len(files)} plugin commands well-formed"
