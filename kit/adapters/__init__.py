"""Per-tool adapters. Each renders the kit into a target project as a list of Actions, so a
dry-run and a real install share one code path. Claude is the primary target; Codex, Cursor, and
Copilot are adapters. All write to disjoint paths, so they coexist in one project.
"""
from __future__ import annotations

from . import claude, codex, copilot, cursor

ADAPTERS = {
    "claude": claude.plan,
    "codex": codex.plan,
    "cursor": cursor.plan,
    "copilot": copilot.plan,
}

TOOLS = tuple(ADAPTERS)


def plan_for(tool: str, kit_root, project_root, terse: bool = False, select=None,
             tolerant: bool = False):
    """Return the Action list for one tool, or for every tool when tool == 'all'. `select` (a set of
    prompt names, or None for the full pack) is forwarded to each adapter. `tolerant=True` lets an
    adapter degrade past a corrupt existing config (the Claude settings file) instead of raising,
    for the remove path (its file back-out and settings unmerge), which only needs the prompt-file
    actions; install, verify, and prune leave it False so a corrupt file fails loudly."""
    if tool == "all":
        actions = []
        for name in TOOLS:
            actions.extend(ADAPTERS[name](kit_root, project_root, terse=terse, select=select,
                                          tolerant=tolerant))
        return actions
    if tool not in ADAPTERS:
        raise ValueError(f"unknown tool {tool!r}; choose one of {TOOLS} or 'all'")
    return ADAPTERS[tool](kit_root, project_root, terse=terse, select=select, tolerant=tolerant)
