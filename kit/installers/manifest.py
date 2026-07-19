"""Build and merge the install manifest (.outpost/manifest.json).

Records, per tool, which prompts an install wrote and at what kit version, so a re-install,
--verify, or a teammate can see the project's choice rather than guessing from disk. Mirrors
installers/settings.py: parse existing text, merge this install's per-tool entries, render
canonical JSON. Never drops another tool's entry; idempotent for the same install.
"""
from __future__ import annotations

import json

MANIFEST_PATH = ".outpost/manifest.json"


def merge_manifest(existing: dict, updates: dict, kit_version: str) -> dict:
    """Return the manifest with each tool in `updates` recorded (selection plus sorted prompts) and
    `kit_version` set, preserving any other tool already present. `updates` maps a tool name to
    `{"selection": str, "prompts": list[str]}`, optionally with a `files` ownership map: per path,
    whether the file existed before the kit first wrote there (a pre-install hash may ride along
    as a forensic record). The existed flag is what lets removal delete only files the kit
    created. Raises ValueError on a malformed existing manifest."""
    if not isinstance(existing, dict):
        raise ValueError("manifest must be a JSON object")
    raw_tools = existing.get("tools")
    if raw_tools is None:
        raw_tools = {}
    if not isinstance(raw_tools, dict):
        raise ValueError("manifest 'tools' must be a JSON object")
    tools = dict(raw_tools)
    for tool, entry in updates.items():
        record = {
            "prompts": sorted(entry["prompts"]),
            "selection": entry["selection"],
            "terse": bool(entry.get("terse", False)),
        }
        if "files" in entry:
            record["files"] = dict(entry["files"])
        tools[tool] = record
    return {"kit_version": kit_version, "tools": tools}


def parse_manifest(text: str) -> dict:
    """Parse and shape-validate a manifest, so a corrupt or hand-edited file fails loudly at the
    read site instead of crashing or silently misleading a later step. Raises ValueError on
    malformed JSON or a wrong-typed top level, `tools`, entry, or `prompts` list."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"manifest is not valid JSON: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    tools = data.get("tools", {})
    if not isinstance(tools, dict):
        raise ValueError("manifest 'tools' must be a JSON object")
    for tool, entry in tools.items():
        if not isinstance(entry, dict):
            raise ValueError(f"manifest entry for {tool!r} must be a JSON object")
        prompts = entry.get("prompts", [])
        if not isinstance(prompts, list) or not all(isinstance(p, str) for p in prompts):
            raise ValueError(f"manifest 'prompts' for {tool!r} must be a list of strings")
        files = entry.get("files")
        if files is None:
            continue  # a pre-records manifest; removal falls back to the byte-match rule
        if not isinstance(files, dict):
            raise ValueError(f"manifest 'files' for {tool!r} must be a JSON object")
        for path, rec in files.items():
            if not isinstance(rec, dict) or not isinstance(rec.get("existed"), bool):
                raise ValueError(
                    f"manifest file record for {tool!r} at {path!r} needs a boolean 'existed'")
    return data


def drop_tool(manifest: dict, tool: str) -> dict:
    """Return the manifest with one tool's entry removed. Used by `--remove` to forget a tool."""
    tools = {t: e for t, e in manifest.get("tools", {}).items() if t != tool}
    return {"kit_version": manifest.get("kit_version", ""), "tools": tools}


def dumps(manifest: dict) -> str:
    """Render a manifest dict to canonical JSON text. Pair with merge_manifest to write an install
    record; install.py does exactly that."""
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"
