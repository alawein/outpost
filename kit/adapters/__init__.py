"""Per-tool adapters. Each renders the kit into a target project as a list of Actions, so a
dry-run and a real install share one code path. Claude is the primary target; Codex, Cursor,
Copilot, Windsurf, and Gemini CLI are adapters. All write to disjoint paths, so they coexist in one
project.
"""
from __future__ import annotations

from . import claude, codex, copilot, cursor, gemini, windsurf
from .base import source_actions

ADAPTERS = {
    "claude": claude.plan,
    "codex": codex.plan,
    "cursor": cursor.plan,
    "copilot": copilot.plan,
    "windsurf": windsurf.plan,
    "gemini": gemini.plan,
}

TOOLS = tuple(ADAPTERS)


def _plan_one(tool: str, kit_root, project_root, terse, select, tolerant, sources, skipped):
    actions = ADAPTERS[tool](kit_root, project_root, terse=terse, select=select,
                             tolerant=tolerant)
    for source in sources:
        actions.extend(source_actions(tool, source, select, skipped))
    # a source skill named like a core prompt (or like another source's skill, for the two tools
    # that key on the bare name) would plan the same path twice; the last write would win and
    # verify would read the first as drift, so refuse it at plan time
    seen: set[str] = set()
    for a in actions:
        if a.path in seen:
            raise ValueError(f"{tool}: {a.path} is planned twice; a source skill name collides "
                             "with a core prompt or another source")
        seen.add(a.path)
    return actions


def plan_for(tool: str, kit_root, project_root, terse: bool = False, select=None,
             tolerant: bool = False, sources=(), skipped=None):
    """Return the Action list for one tool, or for every tool when tool == 'all'. `select` (a set of
    prompt names, or None for the full pack) is forwarded to each adapter and applied to source
    skills too. `tolerant=True` lets an adapter degrade past a corrupt existing config (the Claude
    settings file) instead of raising, for the remove path (its file back-out and settings
    unmerge), which only needs the prompt-file actions; install, verify, and prune leave it False
    so a corrupt file fails loudly. `sources` (Source objects from kit.sources.discover) append
    their skills after each tool's core actions; what a source leaves out is appended to
    `skipped` as Skip records when a list is given."""
    if tool == "all":
        actions = []
        for name in TOOLS:
            actions.extend(_plan_one(name, kit_root, project_root, terse, select, tolerant,
                                     sources, skipped))
        return actions
    if tool not in ADAPTERS:
        raise ValueError(f"unknown tool {tool!r}; choose one of {TOOLS} or 'all'")
    return _plan_one(tool, kit_root, project_root, terse, select, tolerant, sources, skipped)
