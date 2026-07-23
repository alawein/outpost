"""No stale skill ships in the plugin tree. The plugin's skills are generated from the catalog, but
the generator only writes and compares the skills it knows about (compare_generated is
generated-to-disk). A prompt removed or renamed in the catalog leaves its old
`plugins/outpost/skills/<name>/` directory shipping with the gate green, the same orphan class the
closed Cursor-rule DEBT entry named, now on the plugin side. This check enumerates the shipped skill
directories and rejects any whose name is not a current catalog prompt.
"""
from __future__ import annotations

import pathlib

from ..catalog import load_catalog


def run(root: pathlib.Path) -> tuple[bool, str]:
    try:
        cat = load_catalog(root / "kit" / "catalog" / "catalog.json")
    except ValueError as e:
        return False, str(e)
    names = {p["name"] for p in cat.prompts}
    skills_dir = root / "plugins" / "outpost" / "skills"
    if not skills_dir.is_dir():
        return True, "no plugin skills directory"
    stray = sorted(d.name for d in skills_dir.iterdir()
                   if d.is_dir() and d.name not in names)
    if stray:
        return False, "stale plugin skill(s) not in the catalog: " + ", ".join(stray)
    return True, f"{len(names)} plugin skills all resolve to catalog prompts"
