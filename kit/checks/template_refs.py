"""Every prompt a template names resolves to a catalog prompt. The `templates` check confirms a
template references the pack (the two anchor prompts appear); this confirms each prompt name a
template spells out still exists, so renaming a prompt in the catalog cannot leave a dangling
reference in a template.

A template names a prompt as a backtick-wrapped kebab token (`plan-change`). Those are the only bare
kebab backticks the templates use: file paths and config keys carry a dot or slash, so they do not
match. Templates therefore reserve bare kebab backticks for prompt names.
"""
from __future__ import annotations

import pathlib

from . import REF
from ..catalog import load_catalog


def run(root: pathlib.Path) -> tuple[bool, str]:
    try:
        cat = load_catalog(root / "kit" / "catalog" / "catalog.json")
    except ValueError as e:
        return False, str(e)
    names = {p["name"] for p in cat.prompts}

    errors: list[str] = []
    checked = 0
    for p in sorted((root / "templates").glob("*.md")):
        if p.name == "README.md":
            continue
        for m in REF.finditer(p.read_text(encoding="utf-8")):
            token = m.group(1)
            checked += 1
            if token not in names:
                errors.append(f"{p.name}: names `{token}`, which is not a catalog prompt")

    if errors:
        return False, "; ".join(errors[:10])
    return True, f"{checked} template prompt references all resolve to the catalog"
