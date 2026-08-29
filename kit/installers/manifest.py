"""Build and merge the install manifest (.outpost/manifest.json).

Records, per tool, which prompts an install wrote and at what kit version, so a re-install,
--verify, or a teammate can see the project's choice rather than guessing from disk. Mirrors
installers/settings.py: parse existing text, merge this install's per-tool entries, render
canonical JSON. Never drops another tool's entry; idempotent for the same install.
"""
from __future__ import annotations

import json
import posixpath

MANIFEST_PATH = ".outpost/manifest.json"


def is_project_relative(path: str) -> bool:
    """True if `path` is a plain project-relative POSIX path the kit may join to a project root.
    A manifest file key is joined to the root and unlinked by prune and remove, and a source
    skill's supporting file is joined the same way and written, so either would let a crafted
    value reach outside the project. A legit kit path is "/"-joined with no backslash and no
    colon, so reject either character: pathlib on Windows re-anchors on a backslash OR on a drive
    letter ANYWHERE in the path ("a/C:/x" -> drive "C:", root dropped), and a colon also opens an
    NTFS alternate-data-stream ("note:hidden"). The posix checks then catch "/"-absolute, a
    leading "..", and any embedded "/../" (normpath collapses it). A null byte can raise
    mid-join, so it is rejected too."""
    return not ("\\" in path or ":" in path or "\x00" in path
                or path.startswith("/") or path.startswith("..")
                or path != posixpath.normpath(path))


def merge_manifest(existing: dict, updates: dict, kit_version: str, sources=None) -> dict:
    """Return the manifest with each tool in `updates` recorded (selection plus sorted prompts) and
    `kit_version` set, preserving any other tool already present. `updates` maps a tool name to
    `{"selection": str, "prompts": list[str]}`, optionally with a `files` ownership map: per path,
    whether the file existed before the kit first wrote there (a pre-install hash may ride along
    as a forensic record). The existed flag is what lets removal delete only files the kit
    created. A tool entry may also carry `sources`: per source name, the skill names this tool's
    install kept from it (installs are per tool, so the skill list lives with the tool). The
    top-level `sources` maps a source name to `{"path": str}` only, where the clone lives, so a
    later run can re-discover it; it is merged over the recorded sources by name, and None keeps
    the recorded ones as they are, so an install that passes no --source forgets nothing. Raises
    ValueError on a malformed existing manifest."""
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
        if entry.get("sources"):
            record["sources"] = {name: sorted(skills)
                                 for name, skills in entry["sources"].items()}
        tools[tool] = record
    merged = {"kit_version": kit_version, "tools": tools}
    recorded = existing.get("sources") or {}
    if not isinstance(recorded, dict):
        raise ValueError("manifest 'sources' must be a JSON object")
    all_sources = dict(recorded)
    for name, rec in (sources or {}).items():
        all_sources[name] = {"path": rec["path"]}
    if all_sources:
        merged["sources"] = all_sources
    return merged


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
        tool_sources = entry.get("sources")
        if tool_sources is not None:
            # per source name, the skills this tool's install kept; verify and prune read it as
            # the tool's selection, so a wrong shape must fail here
            if not isinstance(tool_sources, dict) or not all(
                    isinstance(skills, list) and all(isinstance(s, str) for s in skills)
                    for skills in tool_sources.values()):
                raise ValueError(f"manifest 'sources' for {tool!r} must map a source name to a "
                                 "list of skill names")
        files = entry.get("files")
        if files is None:
            continue  # a pre-records manifest; removal falls back to the byte-match rule
        if not isinstance(files, dict):
            raise ValueError(f"manifest 'files' for {tool!r} must be a JSON object")
        for path, rec in files.items():
            if not isinstance(rec, dict) or not isinstance(rec.get("existed"), bool):
                raise ValueError(
                    f"manifest file record for {tool!r} at {path!r} needs a boolean 'existed'")
            # A file key must be a plain project-relative POSIX path: prune/remove join it to the
            # project root and unlink it, so an absolute key or one that escapes upward would let a
            # crafted manifest delete files outside the project (the rule is is_project_relative).
            if not is_project_relative(path):
                raise ValueError(
                    f"manifest 'files' key for {tool!r} must be a project-relative path: {path!r}")
    sources = data.get("sources")
    if sources is not None:
        # a source record names where the clone lives, so verify can re-discover it without the
        # flag; a wrong-typed one must fail here, not crash discovery later
        if not isinstance(sources, dict):
            raise ValueError("manifest 'sources' must be a JSON object")
        for name, rec in sources.items():
            if not isinstance(rec, dict) or not isinstance(rec.get("path"), str) or not rec["path"]:
                raise ValueError(f"manifest source {name!r} needs a string 'path'")
    return data


def drop_tool(manifest: dict, tool: str) -> dict:
    """Return the manifest with one tool's entry removed. Used by `--remove` to forget a tool.
    A source's path record stays while any remaining tool still names that source; one no tool
    names any more is forgotten with it, so a later --verify does not go looking for its clone."""
    tools = {t: e for t, e in manifest.get("tools", {}).items() if t != tool}
    out = {"kit_version": manifest.get("kit_version", ""), "tools": tools}
    still_named = set()
    for entry in tools.values():
        still_named |= set((entry or {}).get("sources") or {})
    sources = {n: r for n, r in (manifest.get("sources") or {}).items() if n in still_named}
    if sources:
        out["sources"] = sources
    return out


def dumps(manifest: dict) -> str:
    """Render a manifest dict to canonical JSON text. Pair with merge_manifest to write an install
    record; install.py does exactly that."""
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"
