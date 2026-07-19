"""The committed plugin tree stays in sync with the generator. Three failure modes:

1. A generated file on disk differs from `build_plugin` output (drift after a prompt edit).
2. The plugin manifest version disagrees with the catalog version.
3. A command file under `plugins/outpost/commands/` names a backtick token that is
   not a catalog prompt.

Run `python tools/build.py plugin` to regenerate after any catalog or prompt change.
"""
from __future__ import annotations

import pathlib

from ..catalog import load_catalog
from ..plugin import build_plugin
from . import SKILL_REF, compare_generated


def run(root: pathlib.Path) -> tuple[bool, str]:
    try:
        cat = load_catalog(root / "kit" / "catalog" / "catalog.json")
    except ValueError as e:
        return False, str(e)

    prompt_names = {p["name"] for p in cat.prompts}
    errors: list[str] = []

    generated = build_plugin(root)
    n_skills = len([k for k in generated if k.startswith("plugins/outpost/skills/")])

    # 1. Drift check: every generated file on disk must equal what the generator produces.
    missing, drifted = compare_generated(root, generated)
    errors += [f"generated plugin file missing: {rel}" for rel in missing]
    errors += [f"plugin drift: {rel} does not match the generator (run the build)" for rel in drifted]

    # 2. Version agreement: plugin.json must match the catalog version.
    plugin_json = root / "plugins" / "outpost" / ".claude-plugin" / "plugin.json"
    if plugin_json.is_file():
        import json
        try:
            manifest = json.loads(plugin_json.read_text(encoding="utf-8"))
            if manifest.get("version") != cat.version:
                errors.append(
                    f"plugin.json version {manifest.get('version')!r} != "
                    f"catalog version {cat.version!r}"
                )
        except (ValueError, KeyError) as e:
            errors.append(f"plugin.json parse error: {e}")

    # 3. Command files: every backtick token must be a catalog prompt name.
    cmd_dir = root / "plugins" / "outpost" / "commands"
    cmd_count = 0
    if cmd_dir.is_dir():
        for cmd_file in sorted(cmd_dir.glob("*.md")):
            cmd_count += 1
            text = cmd_file.read_text(encoding="utf-8")
            for m in SKILL_REF.finditer(text):
                tok = m.group(1)
                if tok not in prompt_names:
                    errors.append(
                        f"command {cmd_file.name} names `{tok}`, "
                        f"which is not a catalog prompt"
                    )

    if errors:
        return False, "; ".join(errors[:10])

    return True, f"plugin in sync with the catalog ({n_skills} skills, {cmd_count} commands)"
