"""The ROADMAP current-release line matches the kit version.

The ROADMAP carries a "Current release: vX.Y.Z" line that states what shipped. It goes stale
every release with nothing to catch it. This check reads that line and compares it to the kit
version in the catalog.

Scope is surgical: only the "Current release" line. The per-version history lines in the table
(entries like "v0.1.0 shipped eight prompts") are correct for their time and are excluded.
"""
from __future__ import annotations

import pathlib
import re

from ..catalog import load_catalog

ROADMAP = "docs/ROADMAP.md"
CURRENT_RE = re.compile(r"Current release:\s*v(\d+\.\d+\.\d+)")


def run(root: pathlib.Path) -> tuple[bool, str]:
    try:
        cat = load_catalog(root / "kit" / "catalog" / "catalog.json")
    except ValueError as e:
        return False, str(e)

    p = root / ROADMAP
    if not p.is_file():
        return False, f"{ROADMAP} is missing"

    text = p.read_text(encoding="utf-8")
    m = CURRENT_RE.search(text)
    if not m:
        return False, f'{ROADMAP} has no "Current release: vX.Y.Z" line'

    roadmap_ver = m.group(1)
    if roadmap_ver != cat.version:
        return (
            False,
            f"ROADMAP current release v{roadmap_ver} does not match the kit version v{cat.version}",
        )
    return True, f"ROADMAP current release matches the kit version (v{cat.version})"
