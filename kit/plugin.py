"""Plugin generator: build the Claude Code plugin tree from the catalog.

`build_plugin(kit_root)` returns a dict mapping each generated file's repo-relative
POSIX path to its content. The caller writes the files; this function is pure.

Reuses `kit.adapters.base.load_prompts` for the same prompt-to-SKILL.md rendering
the Claude adapter uses, so the plugin skills are derived from `prompts/core/` and
the catalog stays the single source of truth.
"""
from __future__ import annotations

import json
import pathlib

from .adapters.base import load_prompts
from .catalog import load_catalog

_MARKETPLACE_SCHEMA = "https://json.schemastore.org/claude-code-marketplace.json"
_PLUGIN_SCHEMA = "https://json.schemastore.org/claude-code-plugin.json"
_PLUGIN_NAME = "outpost"
_AUTHOR = {"name": "alawein"}
_HOMEPAGE = "https://github.com/alawein/outpost"


def build_plugin(kit_root: pathlib.Path) -> dict[str, str]:
    """Return a map of repo-relative POSIX path -> file content for every generated plugin file.

    Keys produced:
    - `.claude-plugin/marketplace.json`
    - `plugins/outpost/.claude-plugin/plugin.json`
    - `plugins/outpost/skills/<name>/SKILL.md` for each catalog prompt

    Command files are NOT generated (they are hand-authored). Only the manifests and
    skills are in the returned map.
    """
    cat = load_catalog(kit_root / "kit" / "catalog" / "catalog.json")
    version = cat.version

    marketplace = {
        "$schema": _MARKETPLACE_SCHEMA,
        "name": _PLUGIN_NAME,
        "owner": _AUTHOR,
        "plugins": [
            {
                "name": _PLUGIN_NAME,
                "source": "./plugins/outpost",
                "description": (
                    "Outpost as a Claude Code plugin: the core coding-discipline "
                    "prompts as skills, plus the plugin commands, a review agent, a context hook, "
                    "and the ledger-voice output style."
                ),
            }
        ],
    }

    plugin_manifest = {
        "$schema": _PLUGIN_SCHEMA,
        "name": _PLUGIN_NAME,
        "version": version,
        "description": (
            "Outpost: the core coding-discipline prompts as skills, "
            "plus the plugin commands, a review agent, a context hook, and the ledger-voice output "
            "style. Generated from the catalog."
        ),
        "author": _AUTHOR,
        "homepage": _HOMEPAGE,
        "repository": _HOMEPAGE,
        "license": "MIT",
        "keywords": ["claude-code", "coding-agent", "outpost"],
    }

    files: dict[str, str] = {}

    files[".claude-plugin/marketplace.json"] = json.dumps(marketplace, indent=2) + "\n"
    files["plugins/outpost/.claude-plugin/plugin.json"] = (
        json.dumps(plugin_manifest, indent=2) + "\n"
    )

    for name, content in load_prompts(kit_root, "claude"):
        files[f"plugins/outpost/skills/{name}/SKILL.md"] = content

    return files
