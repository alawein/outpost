"""The user-facing docs name the same tools and prompts the catalog ships, both ways. `docs_sync`
guards the advertised prompt total and `template_refs` guards prompt names inside templates; this is
the inverse for the docs. It pulls every name from the catalog (the SSOT) and hardcodes no display
map: a tool's catalog key sits inside its display name (`Claude Code` contains `claude`), so a
case-insensitive match over the tool table is enough.

Checks:
- every catalog adapter tool is named in the README "Supported tools" table and the
  docs/adapters.md "What each tool gets" table;
- every backtick-wrapped prompt reference in docs/workflow.md resolves to a catalog prompt.

Scope is the current-state, user-facing docs. workflow.md names prompts as backtick tokens, some
hyphenated (`plan-change`) and some single-word (`grill`, `premortem`), so SKILL_REF is used to
catch both shapes: a typo to a non-existent name, hyphenated or not, fails the gate.
The prompt-pack table's generated span lives in docs/workflow.md now (header and rows, all
generated inside the markers). docs_sync byte-checks that span against the catalog generator,
and the workflow scan above also covers it (the span is part of workflow.md), so the two
overlap rather than leave a gap.
"""
from __future__ import annotations

import pathlib

from . import SKILL_REF, table_after
from ..catalog import load_catalog


def run(root: pathlib.Path) -> tuple[bool, str]:
    try:
        cat = load_catalog(root / "kit" / "catalog" / "catalog.json")
    except ValueError as e:
        return False, str(e)
    core_names = {p["name"] for p in cat.prompts}
    tools = {a["tool"] for a in cat.adapters}

    readme = (root / "README.md").read_text(encoding="utf-8")
    adapters_doc = (root / "docs" / "adapters.md").read_text(encoding="utf-8")
    workflow = (root / "docs" / "workflow.md").read_text(encoding="utf-8")

    errors: list[str] = []

    # 1. Tools: each catalog tool key appears (case-insensitive) in both tool tables.
    readme_tools = "\n".join(table_after(readme, "Supported tools")).lower()
    adapters_tools = "\n".join(table_after(adapters_doc, "What each tool gets")).lower()
    for t in sorted(tools):
        if t not in readme_tools:
            errors.append(f"README 'Supported tools' table does not name the {t!r} tool")
        if t not in adapters_tools:
            errors.append(f"docs/adapters.md 'What each tool gets' table does not name the {t!r} tool")

    # 2. workflow.md: every backtick-wrapped prompt reference resolves to a core catalog prompt.
    for m in SKILL_REF.finditer(workflow):
        if m.group(1) not in core_names:
            errors.append(f"docs/workflow.md names `{m.group(1)}`, which is not a core catalog prompt")

    if errors:
        return False, "; ".join(errors[:10])
    return True, (f"{len(tools)} tools named consistently across the README and adapters docs, and "
                  f"every backtick prompt reference in workflow.md resolves to the catalog")
