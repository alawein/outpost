"""Every adapter imports, exposes a `plan` interface, and produces valid Actions. The adapters
write to disjoint paths, which is what lets the supported tools coexist in one project. This check
proves that property instead of trusting it.
"""
from __future__ import annotations

import importlib
import pathlib
import tempfile

from ..catalog import load_catalog


def run(root: pathlib.Path) -> tuple[bool, str]:
    try:
        cat = load_catalog(root / "kit" / "catalog" / "catalog.json")
    except ValueError as e:
        return False, str(e)

    errors: list[str] = []
    paths_by_tool: dict[str, set[str]] = {}

    # Plan with terse off and on, so the terse-only actions are also constructed (Action validates
    # its mode at construction) and their paths join the collision check.
    with tempfile.TemporaryDirectory() as tmp:
        project = pathlib.Path(tmp)
        for entry in cat.adapters:
            tool, module_name = entry["tool"], entry["module"]
            try:
                module = importlib.import_module(module_name)
            except ImportError as e:
                errors.append(f"{tool}: cannot import {module_name!r}: {e}")
                continue
            plan = getattr(module, "plan", None)
            if not callable(plan):
                errors.append(f"{tool}: {module_name} has no callable plan()")
                continue
            try:
                actions = plan(root, project) + plan(root, project, terse=True)
            except ValueError as e:
                errors.append(f"{tool}: plan() produced an invalid action: {e}")
                continue
            if not actions:
                errors.append(f"{tool}: plan() produced no actions")
                continue
            paths_by_tool[tool] = {a.path for a in actions}

    tools = sorted(paths_by_tool)
    for i, a in enumerate(tools):
        for b in tools[i + 1:]:
            overlap = paths_by_tool[a] & paths_by_tool[b]
            if overlap:
                errors.append(f"{a} and {b} both write {sorted(overlap)}; they would collide")

    if errors:
        return False, "; ".join(errors[:10])
    return True, f"{len(paths_by_tool)} adapters import, plan, and write disjoint paths"
