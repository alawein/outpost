"""Every shipped plugin command must be named where a user looks for it: the "Claude Code
shortcuts" table in docs/workflow.md. A command file added to plugins/outpost/commands/ without a
matching table row would ship invisibly; doc_truth and plugin_sync check that existing references
resolve, not that this list is complete. This check closes that gap.

The scan is scoped to the shortcuts table (not the whole file) via the heading-anchored helper
doc_truth uses, so a command dropped from its row but still mentioned in prose elsewhere still
fails.
"""
from __future__ import annotations

import pathlib
import re

from . import table_after

# a backtick-wrapped namespaced plugin command token, e.g. `/outpost:doctor`.
CMD_REF = re.compile(r"`/outpost:([a-z]+(?:-[a-z]+)*)`")


def _row_commands(line: str) -> set[str]:
    """Command names (`/outpost:name`, namespace dropped) found anywhere in one table row line."""
    return {m.group(1) for m in CMD_REF.finditer(line)}


def run(root: pathlib.Path) -> tuple[bool, str]:
    commands = sorted(p.stem for p in (root / "plugins" / "outpost" / "commands").glob("*.md"))

    workflow_text = (root / "docs" / "workflow.md").read_text(encoding="utf-8")
    named: set[str] = set()
    for row in table_after(workflow_text, "Claude Code shortcuts"):
        named.update(_row_commands(row))

    missing = [c for c in commands if c not in named]
    if missing:
        return False, (
            f"docs/workflow.md: missing plugin command(s): {', '.join('/outpost:' + m for m in missing)}")
    return True, f"{len(commands)} plugin commands named in docs/workflow.md"
