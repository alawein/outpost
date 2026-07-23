"""The user-facing docs name the same tools and prompts the catalog ships, both ways. `docs_sync`
guards the advertised prompt total and `template_refs` guards prompt names inside templates; this is
the inverse for the docs. It pulls every name from the catalog (the SSOT) and hardcodes no display
map: a tool's catalog key sits inside its display name (`Claude Code` contains `claude`), so a
case-insensitive match over the tool table is enough.

Checks:
- every catalog adapter tool is named in the README "Supported tools" table and the
  docs/adapters.md "What each tool gets" table;
- every backtick-wrapped prompt reference in docs/workflow.md resolves to a catalog prompt;
- every hyphenated prompt-shaped backtick token in the instruction docs (README, onboarding,
  adapters, plugin) resolves to a catalog prompt or a real plugin component, so a rename or typo
  leaving a dangling ref there fails the gate, not only in workflow.md.

Scope is the current-state, user-facing docs. workflow.md names prompts as backtick tokens, some
hyphenated (`plan-change`) and some single-word (`grill`, `premortem`), so SKILL_REF is used to
catch both shapes: a typo to a non-existent name, hyphenated or not, fails the gate. The wider
instruction-doc scan uses REF (hyphenated only): those docs carry ordinary single-word backtick
tokens (`verify`, `prune`, a flag), so matching single words would false-fail on prose; a
hyphenated token is prompt-shaped and safe to resolve. The valid set is the catalog prompts plus
the plugin's own component names, derived from the plugin tree (the `agents/` and `output-styles/`
dirs) rather than hardcoded, so a new component never needs an allowlist edit. Append-only ledgers
(dogfooding, DEBT, audit, decisions) and the ROADMAP idea backlog legitimately name retired prompts
in prose, so they stay out of this scan.
The prompt-pack table's generated span lives in docs/workflow.md now (header and rows, all
generated inside the markers). docs_sync byte-checks that span against the catalog generator,
and the workflow scan above also covers it (the span is part of workflow.md), so the two
overlap rather than leave a gap.
"""
from __future__ import annotations

import pathlib

from . import REF, SKILL_REF, table_after
from ..catalog import load_catalog


# Instruction docs whose hyphenated prompt refs must resolve. These name prompts as directions to
# the reader, unlike the append-only ledgers and the ROADMAP backlog, which discuss retired names.
_INSTRUCTION_DOCS = ("README.md", "docs/onboarding.md", "docs/adapters.md", "docs/plugin.md")


def _plugin_components(root: pathlib.Path) -> set[str]:
    """Non-prompt kit component names a doc may reference (a plugin agent, an output style),
    derived from the plugin tree so a new component never needs an allowlist edit here."""
    comps: set[str] = set()
    for sub in ("agents", "output-styles"):
        d = root / "plugins" / "outpost" / sub
        if d.is_dir():
            comps |= {f.stem for f in d.glob("*.md")}
    return comps


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

    # 3. instruction docs: every hyphenated prompt-shaped ref resolves to a prompt or a component.
    valid = core_names | _plugin_components(root)
    for rel in _INSTRUCTION_DOCS:
        try:
            text = (root / rel).read_text(encoding="utf-8")
        except OSError:
            continue
        for m in REF.finditer(text):
            if m.group(1) not in valid:
                errors.append(f"{rel} names `{m.group(1)}`, which is not a catalog prompt "
                              "or a plugin component")

    if errors:
        return False, "; ".join(errors[:10])
    return True, (f"{len(tools)} tools named consistently across the README and adapters docs, and "
                  f"every backtick prompt reference in workflow.md and the instruction docs resolves")
