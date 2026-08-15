#!/usr/bin/env python3
"""Install the kit into a target project for one tool, or all of them.

The installer plans every change first (an Action list from the chosen adapter), then either prints
the plan (--dry-run) or applies it. Both the dry-run and the apply derive each action's effect from
the same precomputed actions and the same `Action.status()`, so a dry-run shows exactly what an
install would do.

Safe and idempotent:
- A user-owned file (CLAUDE.md, AGENTS.md, the Cursor repo rule, the Copilot instructions) is
  written only if absent. An existing one is left alone.
- The manifest records, per path, whether a file existed before the kit first wrote there. The
  existed flag alone drives every ownership decision; the pre-install hash stored beside a
  pre-existing record (pre_hash) is a forensic record for later inspection, read by nothing in
  the installer. A kit-created record's hash (kit_hash) is different: it is read, to tell a
  retired file the kit can still prove unedited from one a user has since hand-edited (a still-
  shipping path is protected the same way, by a live byte match against the current plan).
  A pre-existing file at a kit path is never overwritten: it is
  skipped with a named warning and the skip is recorded. --remove and --prune delete only what the
  manifest proves the kit created and still matches; a manifest from a pre-records kit falls back
  to the old byte-match rule.
- The Claude settings file is merged, never overwritten: secret-only deny rules are added and
  unrelated keys are untouched. Re-running changes nothing. --remove un-merges the kit keys and
  deletes the emptied file only when the manifest records the kit created it; a pre-existing
  settings file is the user's and stays, even byte-equal to the kit's merged output.
- Kit-owned prompt files carry identical content each run, so a re-run is a no-op (an unchanged
  file is skipped, not rewritten).

Claude, Codex, Cursor, and Copilot write to disjoint paths, so they coexist in one project.

Usage:
  python install.py --tool claude --project /path/to/your/repo            # the common case
  python install.py --tool all --project /path/to/your/repo               # every adapter
  python install.py --tool claude --project /path/to/your/repo --dry-run  # print the plan, write nothing
  python install.py --tool claude --project /path/to/your/repo --terse    # also install the terse output style
  python install.py --list                                                 # show what installs, write nothing
  python install.py --tool claude --project /path/to/your/repo --verify   # check kit files are present and unmodified
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

from kit.adapters import TOOLS, plan_for
from kit.adapters.base import Action, TERSE_OUTPUT_STYLE
from kit.catalog import load_catalog
from kit.installers.manifest import (
    MANIFEST_PATH, drop_tool, dumps as manifest_dumps,
    merge_manifest, parse_manifest)
from kit.installers.settings import unmerged_text

KIT_ROOT = pathlib.Path(__file__).resolve().parent


def _parse_names(raw: str) -> list[str]:
    names = [n.strip() for n in raw.split(",") if n.strip()]
    if not names:
        raise ValueError("no prompt names given")
    return names


def resolve_selection(only, exclude, catalog_names):
    """Resolve the --only/--exclude flags to (label, select_set). label is 'full' | 'only' |
    'exclude'; select_set is a set of names, or None for the full pack. Raises ValueError on an
    unknown or empty name list, so a typo fails loudly instead of installing nothing."""
    if only is not None:
        names = _parse_names(only)
    elif exclude is not None:
        names = _parse_names(exclude)
    else:
        return "full", None
    unknown = sorted(n for n in names if n not in catalog_names)
    if unknown:
        raise ValueError("not a catalog prompt: " + ", ".join(unknown))
    if only is not None:
        return "only", set(names)
    return "exclude", set(catalog_names) - set(names)


def _tools_for(tool: str):
    """The tool list a command acts on: every tool for 'all', else just the one named."""
    return TOOLS if tool == "all" else (tool,)


def _existing_manifest_path(project_root: pathlib.Path) -> pathlib.Path | None:
    """The manifest file to read: `.outpost/manifest.json` if present, else None."""
    path = project_root / MANIFEST_PATH
    if path.exists():
        return path
    return None


def _sha256(target: pathlib.Path) -> str:
    return "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()


def _hash_str(content: str) -> str:
    # matches _sha256's format; content is always written via .encode("utf-8") with no newline
    # translation (see the apply write), so this equals _sha256(target) right after the write.
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def _is_contained(project_root: pathlib.Path, path: str) -> bool:
    """True if project_root / path resolves, following any symlink, to somewhere still inside
    project_root. A manifest 'files' key is validated only as a string (no absolute path, no ..,
    no backslash or colon); a symlink already sitting in the project can still redirect a
    clean-looking relative key outside the root once the filesystem actually resolves it. Used
    before any delete or write this file performs on a project-relative path, so a pre-planted
    symlink can redirect neither."""
    root = project_root.resolve()
    target = (project_root / path).resolve()
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False


def _legacy_claim(project_root: pathlib.Path, tool: str, prev_entry: dict) -> set:
    """The paths a records-less install of this tool can prove it wrote: the plan derived from its
    own recorded prompts, guide, and terse flag. A manifest without a `files` map (a kit version
    before per-file ownership records) still names its selection, so its own footprint is
    recoverable; a path outside it was never that install's to write, so disk state decides who
    owns it. Kept for correctness: without it, a reinstall over a records-less manifest would read
    the kit's own earlier files as the user's and never update them (ADR-0016)."""
    sel = set(prev_entry.get("prompts", []))
    terse = bool(prev_entry.get("terse", False))
    return {a.path for a in plan_for(tool, KIT_ROOT, project_root, terse=terse, select=sel)
            if a.mode in ("write", "create")}


def _file_records(project_root: pathlib.Path, tool: str, terse: bool, select_set,
                  prev_manifest: dict) -> dict:
    """Per path this tool's plan touches, whether a file existed there before the kit ever wrote
    it. The existed flag is the ownership proof: apply never overwrites a path recorded as
    pre-existing, and --remove and --prune delete only paths recorded as kit-created. The
    pre-install hash stored with a pre-existing record is a forensic trace of what was on disk,
    not an input to any decision. A prior record wins over disk state, so the original truth
    survives reinstalls. A merge-mode path (the Claude settings file) is recorded too, so
    --remove deletes that file only when the kit created it."""
    prev_entry = prev_manifest.get("tools", {}).get(tool) or {}
    prev_files = prev_entry.get("files")
    records = dict(prev_files) if prev_files else {}
    legacy_claim = None
    for a in plan_for(tool, KIT_ROOT, project_root, terse=terse, select=select_set):
        if a.mode not in ("write", "create", "merge"):
            continue
        target = project_root / a.path
        prior = records.get(a.path)
        if prior is not None:
            if prior.get("existed") and not target.exists():
                # the user's file is gone; the kit creates it
                records[a.path] = {"existed": False, "kit_hash": _hash_str(a.content)}
            continue
        if not target.exists():
            records[a.path] = {"existed": False, "kit_hash": _hash_str(a.content)}
        elif prev_files is None and prev_entry:
            # A records-less install of this tool owned the paths its own recorded plan derives
            # (its prompts, guide, and terse flag); keep that claim rather than reading the kit's
            # own earlier install as user data. A path outside that footprint was never the old
            # install's, so an existing file there is the user's.
            if legacy_claim is None:
                legacy_claim = _legacy_claim(project_root, tool, prev_entry)
            if a.path in legacy_claim:
                # the file already exists (a prior install's own output); hash what is actually
                # on disk now, not a.content, since an older kit version's rendering can honestly
                # differ from this run's without being a user edit.
                records[a.path] = {"existed": False, "kit_hash": _sha256(target)}
            else:
                records[a.path] = {"existed": True, "pre_hash": _sha256(target)}
        else:
            records[a.path] = {"existed": True, "pre_hash": _sha256(target)}
    return records


def _user_owned_paths(manifest: dict, tools) -> set:
    """Paths the manifest records as pre-existing: the user's files, never the kit's to touch."""
    owned = set()
    for t in tools:
        files = (manifest.get("tools", {}).get(t) or {}).get("files") or {}
        owned |= {path for path, rec in files.items() if rec.get("existed")}
    return owned


def manifest_action(prev_manifest: dict, tool, select_label, select_set, cat,
                    terse: bool, records_by_tool: dict) -> Action:
    """One merge Action recording, per installed tool, the resolved prompts, whether terse was used,
    the per-path ownership records, and the kit version."""
    updates = {}
    for t in _tools_for(tool):
        # per tool: a prompt the catalog limits to other hosts (decision 0014: converge is
        # Claude-only) is not eligible here, so --verify never reports it as missing
        eligible = {p["name"] for p in cat.prompts_for(t)}
        installed = sorted(eligible if select_set is None else (eligible & select_set))
        updates[t] = {"selection": select_label, "prompts": installed, "terse": terse,
                      "files": records_by_tool[t]}
    content = manifest_dumps(merge_manifest(prev_manifest, updates, cat.version))
    return Action(path=MANIFEST_PATH, content=content, mode="merge",
                  note="record installed prompts and file ownership per tool")


def _read_manifest(project_root: pathlib.Path) -> dict:
    """The manifest as a validated dict. Absent file returns {} (a legitimate full-pack fallback);
    a corrupt or wrong-shaped file raises ValueError/OSError so the caller fails loudly instead of
    treating a broken manifest as if none were installed. Reads `.outpost/manifest.json`."""
    path = _existing_manifest_path(project_root)
    if path is None:
        return {}
    return parse_manifest(path.read_text(encoding="utf-8"))


def _load_validated_manifest(project_root: pathlib.Path, catalog_names) -> dict:
    """Read the manifest and reject any unknown prompt name, the shared pre-flight for verify and
    prune. Raises ValueError/OSError, which the caller turns into a clean error and exit 1."""
    manifest = _read_manifest(project_root)
    _check_manifest_names(manifest, catalog_names)
    return manifest


def _selection_for(manifest: dict, tool: str):
    entry = manifest.get("tools", {}).get(tool)
    if not entry:
        return None  # no record: verify against the full pack
    return set(entry.get("prompts", []))


def _terse_for(manifest: dict, tool: str, override: bool = False) -> bool:
    """Whether a tool's install is terse: the manifest's recorded flag, or the --terse override.
    Lets verify/prune/remove see and clean the terse output style without re-passing --terse."""
    entry = manifest.get("tools", {}).get(tool)
    recorded = bool(entry.get("terse", False)) if entry else False
    return recorded or override


def _version_tuple(v):
    """A dotted version as a tuple of ints for ordering, or None if it is not plain numeric."""
    try:
        return tuple(int(x) for x in v.split("."))
    except (ValueError, AttributeError):
        return None


def _version_note(manifest: dict, current_version: str):
    """A one-line note when the install was recorded at a different kit version than the one
    running, or None when they match or no version is recorded. The files may still be in sync;
    this flags only that the recorded stamp is stale, so re-installing refreshes it."""
    recorded = manifest.get("kit_version")
    if not recorded or recorded == current_version:
        return None
    rt, ct = _version_tuple(recorded), _version_tuple(current_version)
    if rt is not None and ct is not None:
        rel = "older than" if rt < ct else "newer than"
    else:
        rel = "different from"
    return (f"note: this install was recorded at kit v{recorded}, {rel} the running kit "
            f"v{current_version}; re-install to refresh it")


def _check_manifest_names(manifest: dict, catalog_names) -> None:
    """Raise ValueError if the manifest names a prompt this kit does not ship. The manifest is
    authoritative for verify and prune, so an unknown name (a hand-edit typo, or a cross-version
    file) must fail loudly before either acts: otherwise a typo silently drops a real prompt from
    the selection, and prune deletes it as an orphan. Shape is already validated on read."""
    unknown = set()
    for entry in manifest.get("tools", {}).values():
        unknown |= {p for p in entry.get("prompts", []) if p not in catalog_names}
    if unknown:
        raise ValueError("manifest names prompt(s) not in this kit: " + ", ".join(sorted(unknown)))


def _orphans(project_root: pathlib.Path, tool: str, select_set, terse: bool,
             user_owned=frozenset()) -> list[str]:
    """Kit-owned prompt files on disk that the manifest no longer selects. Narrowing an install
    (`--only`/`--exclude` after a broader one) leaves the de-selected prompt files behind, since the
    installer never deletes. The full plan minus the selected plan gives the de-selected prompt
    paths; the ones that exist on disk are orphans, unless the manifest records them as the user's
    pre-existing files. Empty when nothing was narrowed."""
    if select_set is None:
        return []  # full pack: nothing to de-select
    keep = {a.path for a in plan_for(tool, KIT_ROOT, project_root, terse=terse, select=select_set)}
    extras = []
    for a in plan_for(tool, KIT_ROOT, project_root, terse=terse, select=None):
        if (a.mode == "write" and a.path not in keep and a.path not in user_owned
                and (project_root / a.path).exists()):
            extras.append(a.path)
    return extras


def _retired_paths(project_root: pathlib.Path, tool: str, manifest: dict, terse: bool,
                   tolerant: bool = False) -> list[str]:
    """Manifest-recorded, kit-created files that this tool's current full plan no longer derives:
    the leftovers of a prompt that stopped shipping to this host (decision 0014 retired converge
    from the manual hosts) or left the pack. The plan alone cannot see them, so verify, prune,
    and remove consult the union of the plan and the manifest's file records. Only a kit-created
    record (existed false) qualifies; a pre-existing record is the user's file, never flagged or
    deleted. Returns the paths still on disk, sorted."""
    files = (manifest.get("tools", {}).get(tool) or {}).get("files") or {}
    current = {a.path for a in plan_for(tool, KIT_ROOT, project_root, terse=terse, select=None,
                                        tolerant=tolerant)}
    return [path for path, rec in sorted(files.items())
            if not rec.get("existed") and path not in current
            and (project_root / path).is_file()
            and _is_contained(project_root, path)]


def _retired_unedited(project_root: pathlib.Path, path: str, rec: dict) -> bool:
    """True if a retired kit-created file still matches the hash recorded at install time, so
    deleting it costs nothing the user added. A record with no kit_hash (written before this
    check existed) has no honest way to tell, so it is treated as edited: skip, never guess."""
    kit_hash = rec.get("kit_hash")
    if not kit_hash:
        return False
    try:
        return _sha256(project_root / path) == kit_hash
    except OSError:
        return False


def _remove_empty_parents(target: pathlib.Path, root: pathlib.Path) -> None:
    """Remove now-empty parent dirs of a deleted file, up to but not including the project root.
    Best-effort: the file delete already succeeded, so a locked or racing parent must not raise
    here. It would surface in the caller's unlink try/except and misreport a completed delete as a
    failure (and skip the ownership-record pop). Stop the walk on any filesystem error instead."""
    d = target.parent
    while d != root:
        try:
            if not (d.is_dir() and not any(d.iterdir())):
                break
            d.rmdir()
        except OSError:
            break
        d = d.parent


def prune_orphans(project_root: pathlib.Path, tools, manifest: dict, args_terse: bool):
    """Delete orphan kit-owned prompt files (those the manifest no longer selects), so disk matches
    the recorded selection. Safe: only write-mode prompt files are touched, never a user-owned or
    merged file; an orphan whose content was hand-edited (not the kit version), or that carries no
    ownership record at all, is left in place and reported, so a customization or an unrecorded
    file is never silently lost. Returns (removed, skipped, failed, retired) lists."""
    removed: list[str] = []
    skipped: list[str] = []   # pre-existing, edited, or unrecorded orphans, left in place on purpose
    failed: list[str] = []    # could not delete (locked, permission); one bad file must not abort
    retired: list[str] = []   # kit-created files whose prompt no longer ships to this host
    for t in tools:
        terse = _terse_for(manifest, t, args_terse)
        # Retired files first: a kit-created record whose path even the full plan no longer
        # derives (the prompt left this host or the pack). The manifest record is the ownership
        # proof, but a hand edit since install is still the user's: only an unedited retired file
        # is deleted, matching the de-selected-orphan check just below.
        retired_files = (manifest.get("tools", {}).get(t) or {}).get("files") or {}
        for path in _retired_paths(project_root, t, manifest, terse):
            if not _retired_unedited(project_root, path, retired_files.get(path, {})):
                skipped.append(path)  # edited retired file: a possible customization, user decides
                continue
            target = project_root / path
            try:
                target.unlink()
                _remove_empty_parents(target, project_root)
            except OSError:
                failed.append(path)
            else:
                retired.append(path)
                # a completed delete ends the kit's ownership claim (the F32 residual pattern):
                # the record must not linger and seize a file the user later creates here. The
                # caller persists the mutated manifest when anything was retired.
                files_map = (manifest.get("tools", {}).get(t) or {}).get("files")
                if files_map:
                    files_map.pop(path, None)
        sel = _selection_for(manifest, t)
        if sel is None:
            continue  # no narrowing recorded: no de-selected orphans to prune
        files = (manifest.get("tools", {}).get(t) or {}).get("files")
        keep = {a.path for a in plan_for(t, KIT_ROOT, project_root, terse=terse, select=sel)}
        for a in plan_for(t, KIT_ROOT, project_root, terse=terse, select=None):
            if a.mode != "write" or a.path in keep:
                continue
            target = project_root / a.path
            if not target.exists():
                continue
            rec = files.get(a.path) if files is not None else None
            if rec is not None and rec.get("existed"):
                skipped.append(a.path)  # recorded as pre-existing: the user's file, never pruned
                continue
            if rec is None and files is not None:
                # a modern manifest exists but never recorded this path (excluded from every
                # install this project has run): no record is no proof the kit ever owned it, so
                # a byte match alone must not authorize deletion (ADR-0019). Only a manifest with
                # no files map at all (files is None) still falls back to byte-match-only, below --
                # and unlike remove_for_tools, files is None here only for a genuine pre-records
                # manifest: sel (above) is None, and this loop never reached, for a tool with no
                # manifest entry at all, so there is no never-installed-tool case to guard against.
                skipped.append(a.path)
                continue
            if a.status(project_root) != "unchanged":
                skipped.append(a.path)  # edited orphan: a possible customization, user decides
                continue
            try:
                target.unlink()
                _remove_empty_parents(target, project_root)
            except OSError:
                failed.append(a.path)  # report and keep going, do not abort the whole prune
            else:
                removed.append(a.path)
                # a completed delete ends the kit's ownership claim, the same as the retired loop
                # above: the record must not linger and seize a file the user later creates here
                files_map = (manifest.get("tools", {}).get(t) or {}).get("files")
                if files_map:
                    files_map.pop(a.path, None)
    return removed, skipped, failed, retired


def _is_kit_content(target: pathlib.Path, content: str) -> bool:
    """True if the file is byte-identical to what the kit would write (newline-normalized on read).
    A modified or undecodable file is not the kit's, so `--remove` must leave it alone."""
    try:
        return target.read_text(encoding="utf-8") == content
    except (UnicodeDecodeError, OSError):
        return False


def remove_for_tools(project_root: pathlib.Path, tools, manifest: dict, args_terse: bool):
    """Back a tool's kit-owned files out of a target: every prompt file (write) and the guide it
    created (create), but only when the file is still the kit version. An edited file is a possible
    customization, so it is left in place and reported. The settings merge is handled separately
    (it is un-merged, not deleted). Returns (removed, skipped, failed, retired) path lists. Only files that
    actually exist on disk and are still the kit version are removed."""
    removed: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []
    retired: list[str] = []   # kit-created files whose prompt no longer ships to this host
    for t in tools:
        # A retired file (kit-created per the manifest, absent from the current full plan) has no
        # plan action to drive the loop below, so it is backed out here on the record's proof --
        # but only when it still matches the hash recorded at install time; a hand edit since is
        # the user's, same as the byte-match guard just below for still-shipping paths.
        retired_files = (manifest.get("tools", {}).get(t) or {}).get("files") or {}
        for path in _retired_paths(project_root, t, manifest, _terse_for(manifest, t, args_terse),
                                   tolerant=True):
            if not _retired_unedited(project_root, path, retired_files.get(path, {})):
                skipped.append(path)  # edited retired file: a possible customization, never deleted
                continue
            target = project_root / path
            try:
                target.unlink()
                _remove_empty_parents(target, project_root)
            except OSError:
                failed.append(path)
            else:
                retired.append(path)
        entry = manifest.get("tools", {}).get(t) or {}
        files = entry.get("files")
        # A pre-records manifest (this tool was installed here, by a kit version before per-file
        # ownership records existed) still falls back to byte-match below: `entry` is present but
        # `files` is None. A tool with no entry at all was never installed in this project, so
        # there is no proof of authorship and nothing to reclaim (ADR-0019); that must not reuse
        # the legacy fallback just because `files` is also None in that case.
        legacy_manifest = bool(entry) and files is None
        for a in plan_for(t, KIT_ROOT, project_root, terse=_terse_for(manifest, t, args_terse),
                          select=None, tolerant=True):
            if a.mode not in ("write", "create"):
                continue  # the settings merge is un-installed by unmerge_kit_settings
            target = project_root / a.path
            if not target.exists():
                continue
            rec = files.get(a.path) if files is not None else None
            if rec is not None and rec.get("existed"):
                skipped.append(a.path)  # recorded as pre-existing: the user's file, not the kit's
                continue
            if rec is None and not legacy_manifest:
                # no record for this path, and not the legacy-manifest case: either a modern
                # manifest that never recorded this path (excluded from every install this
                # project has run), or this tool was never installed here at all. Either way, no
                # record is no proof the kit ever owned it, so a byte match alone must not
                # authorize deletion (ADR-0019).
                skipped.append(a.path)
                continue
            # Ownership contract: the manifest record proves the kit created the path, and the
            # byte match still protects an edit. A pre-records manifest has no file records, so
            # removal falls back to the old rule alone: delete only what byte-matches the kit
            # version.
            if not _is_kit_content(target, a.content):
                skipped.append(a.path)  # your edit: never silently deleted
                continue
            try:
                target.unlink()
                _remove_empty_parents(target, project_root)
            except OSError:
                failed.append(a.path)
            else:
                removed.append(a.path)
    return removed, skipped, failed, retired


def unmerge_kit_settings(project_root: pathlib.Path, tools, manifest: dict, args_terse: bool):
    """Un-install the kit's settings merge for each tool: strip the kit deny rules, keeping every
    other key. Delete the file only when nothing of the user's remains and the manifest records
    the kit created it; a file recorded as pre-existing is the user's and is left in place (its
    content was never the kit's to reclaim). Only a genuine pre-records manifest (the tool was
    installed here before per-file records existed) falls back to the old rule and deletes an
    emptied file; no manifest entry at all means the tool was never installed here, so the file
    is left alone instead (ADR-0019). Returns a list of (path, outcome) where outcome is
    'removed', 'unmerged', 'unchanged' (no kit rules found), 'skipped', or 'failed'."""
    results = []
    for t in tools:
        files = (manifest.get("tools", {}).get(t) or {}).get("files")
        for a in plan_for(t, KIT_ROOT, project_root, terse=_terse_for(manifest, t, args_terse),
                          select=None, tolerant=True):
            if a.mode != "merge":
                continue
            target = project_root / a.path
            if not _is_contained(project_root, a.path):
                results.append((a.path, "skipped"))
                continue
            if not target.exists():
                continue
            try:
                text = target.read_text(encoding="utf-8")
            except OSError:
                results.append((a.path, "failed"))
                continue
            try:
                new_text = unmerged_text(text)  # None when nothing of the user's remains
            except ValueError:
                results.append((a.path, "skipped"))  # malformed user settings: leave it untouched
                continue
            legacy_manifest = bool((manifest.get("tools", {}).get(t) or {})) and files is None
            rec = files.get(a.path) if files is not None else None
            if new_text is None and rec is not None and rec.get("existed"):
                # the file pre-existed the kit, so what looks like kit-only content is the
                # user's own; never delete it, and strip nothing (the merge was a no-op)
                results.append((a.path, "skipped"))
                continue
            if new_text is None and rec is None and not legacy_manifest:
                # no record for this path, and not a genuine pre-records manifest: this tool was
                # never installed here at all (ADR-0019's rule, the same distinction
                # remove_for_tools already makes), so there is no proof the kit
                # ever owned this file; leave it alone rather than deleting on a byte-match guess
                results.append((a.path, "skipped"))
                continue
            try:
                if new_text is None:
                    target.unlink()
                    _remove_empty_parents(target, project_root)
                    results.append((a.path, "removed"))
                elif new_text == text:
                    results.append((a.path, "unchanged"))  # no kit rules present
                else:
                    target.write_bytes(new_text.encode("utf-8"))
                    results.append((a.path, "unmerged"))
            except OSError:
                results.append((a.path, "failed"))
    return results


TERSE_STYLE_PATH = ".claude/output-styles/terse.md"
CLAUDE_SETTINGS_PATH = ".claude/settings.json"


def _kit_terse_proof(entry) -> bool:
    """True when the manifest proves the kit set the terse state: the prior entry's terse flag is
    on, or the entry records the terse style path as kit-created. Matching the kit's style bytes
    is never proof; a user can place that file by hand."""
    if not entry:
        return False
    if entry.get("terse"):
        return True
    rec = (entry.get("files") or {}).get(TERSE_STYLE_PATH)
    return rec is not None and not rec.get("existed", False)


def stale_terse_state(project_root: pathlib.Path, kit_owned: bool) -> list[tuple[str, str]]:
    """The terse state a non-terse Claude install leaves stale: the kit's own style file and the
    settings outputStyle key. Judged only when `kit_owned` says the manifest proves a prior
    install set the terse state (see _kit_terse_proof); without that proof nothing here is the
    kit's to touch, byte-identical or not. Returns (op, path) pairs: 'remove' for the kit's style
    file, 'clear' for the key (flagged even when the style file is already gone, so a missed
    clear is retried), 'keep' for an edited style file (a possible customization, reported but
    never deleted)."""
    found: list[tuple[str, str]] = []
    if not kit_owned:
        return found
    style = project_root / TERSE_STYLE_PATH
    if style.exists():
        if _is_kit_content(style, TERSE_OUTPUT_STYLE):
            found.append(("remove", TERSE_STYLE_PATH))
        else:
            found.append(("keep", TERSE_STYLE_PATH))
    settings = project_root / CLAUDE_SETTINGS_PATH
    if settings.exists():
        try:
            data = json.loads(settings.read_text(encoding="utf-8"))
        except (ValueError, OSError) as e:
            # malformed settings: not this cleanup's to judge or rewrite, but say so
            print(f"warning: {CLAUDE_SETTINGS_PATH} is unreadable, stale terse check skipped: {e}",
                  file=sys.stderr)
            data = None
        if isinstance(data, dict) and data.get("outputStyle") == "terse":
            found.append(("clear", CLAUDE_SETTINGS_PATH))
    return found


def apply_stale_terse(project_root: pathlib.Path, stale) -> None:
    """Withdraw the terse choice a plain reinstall supersedes: delete the kit's style file and
    clear the kit-set outputStyle key. A failure warns instead of failing the install; --verify
    flags whatever remains."""
    for op, path in stale:
        target = project_root / path
        if op == "keep":
            print(f"  skip   {path} (edited terse style; left in place, remove it by hand)")
        elif op == "remove":
            try:
                target.unlink()
                _remove_empty_parents(target, project_root)
            except OSError as e:
                print(f"warning: could not remove the stale terse style: {e}", file=sys.stderr)
            else:
                print(f"  remove {path} (terse withdrawn by this install)")
        else:  # clear
            if not _is_contained(project_root, path):
                print(f"warning: {path} resolves outside the project via a symlink; left alone",
                      file=sys.stderr)
                continue
            try:
                data = json.loads(target.read_text(encoding="utf-8"))
                data.pop("outputStyle", None)
                target.write_bytes((json.dumps(data, indent=2) + "\n").encode("utf-8"))
            except (ValueError, OSError) as e:
                print(f"warning: could not clear the stale terse outputStyle: {e}",
                      file=sys.stderr)
            else:
                print(f"  update {path} (cleared the stale terse outputStyle key)")


def _withdrawn_terse(project_root: pathlib.Path, prev_manifest: dict, tool: str,
                     args_terse: bool) -> list[tuple[str, str]]:
    """The stale terse state this install must clean: non-empty only for a non-terse Claude
    install over a project with a recorded Claude install (F32). A first install has no record,
    so any terse state already on disk is the user's."""
    if "claude" not in _tools_for(tool) or args_terse:
        return []
    prev_entry = prev_manifest.get("tools", {}).get("claude")
    if not prev_entry:
        return []
    return stale_terse_state(project_root, _kit_terse_proof(prev_entry))


def apply(actions, project_root: pathlib.Path, protected=frozenset()) -> dict:
    """Apply the plan, printing each action as it happens so progress is visible even if a later
    write fails. `protected` paths are recorded as pre-existing user files: they are skipped with
    a named warning, never overwritten. Returns a tally of outcomes by status. Raises OSError if a
    write fails; the caller reports the partial state and exits non-zero."""
    tally = {"create": 0, "update": 0, "skip (exists)": 0, "unchanged": 0}
    for a in actions:
        target = project_root / a.path
        status = a.status(project_root)
        if a.mode == "write" and a.path in protected and target.exists():
            print(f"  skip   {a.path} (pre-existing file, not the kit's; left alone, "
                  "skip recorded in the manifest)")
            tally["skip (exists)"] += 1
            continue
        if status == "skip (exists)":
            print(f"  skip   {a.path} (exists, left alone)")
            tally["skip (exists)"] += 1
            continue
        if status == "unchanged":
            print(f"  ok     {a.path} (unchanged)")
            tally["unchanged"] += 1
            continue
        if status in ("update", "overwrite") and a.mode == "write":
            print(f"  WARN   {a.path} was edited; overwriting with the kit version "
                  f"(to customize a prompt, use the prompts/<tool>/ overlay instead)")
        if not _is_contained(project_root, a.path):
            print(f"  skip   {a.path} (resolves outside the project via a symlink; left alone)")
            tally["skip (exists)"] += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        # Write bytes with explicit LF so the installed files keep the kit's line-ending policy on
        # every platform (pathlib.write_text would translate to CRLF on Windows).
        target.write_bytes(a.content.encode("utf-8"))
        verb = {"create": "create", "update": "update", "overwrite": "write"}.get(status, "write")
        print(f"  {verb:6} {a.path}")
        # any non-create write (update, or the rare overwrite of an undecodable file) folds into update
        tally["create" if status == "create" else "update"] += 1
    return tally


def render_plan(actions, project_root: pathlib.Path, protected=frozenset()) -> list[str]:
    lines: list[str] = []
    for a in actions:
        status = a.status(project_root)
        if a.mode == "write" and a.path in protected and (project_root / a.path).exists():
            status = "skip (exists)"  # a pre-existing user file: apply will not touch it
        lines.append(f"  [{status:14}] {a.mode:6} {a.path}  - {a.note}")
    return lines


def verify(actions, project_root: pathlib.Path, user_owned=frozenset()) -> tuple[bool, list[str]]:
    """Check an existing install against the plan without writing. A kit-owned action (write or
    merge) that is missing or content-drifted is a failure; a user-owned target (a create action,
    or a path the manifest records as pre-existing) is fine present or absent. Returns
    (in_sync, report_lines)."""
    ok = True
    lines: list[str] = []
    for a in actions:
        status = a.status(project_root)
        if a.mode == "create" or (a.mode == "write" and a.path in user_owned):
            where = "present" if (project_root / a.path).exists() else "absent (optional)"
            lines.append(f"  ok      {a.path} ({where})")
            continue
        if status == "unchanged":
            lines.append(f"  ok      {a.path}")
        elif status == "create":
            ok = False
            lines.append(f"  MISSING {a.path}")
        else:  # update | overwrite
            ok = False
            lines.append(f"  DRIFTED {a.path}")
    return ok, lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install outpost into a project.")
    parser.add_argument("--tool", choices=(*TOOLS, "all"),
                        help="which adapter to install, or 'all' for every tool")
    parser.add_argument("--project", default=".", help="target project directory (default: .)")
    parser.add_argument("--terse", action="store_true",
                        help="(claude) also install and default the terse output style")
    select_group = parser.add_mutually_exclusive_group()
    select_group.add_argument("--only", help="install only these comma-separated prompts "
                                             "(plus the tool's guide and settings)")
    select_group.add_argument("--exclude", help="install every prompt except these "
                                                "comma-separated ones")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--list", action="store_true", dest="list_only",
                      help="list what the kit would install, then exit (writes nothing)")
    mode.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    mode.add_argument("--verify", action="store_true",
                      help="check the kit-owned files of an install are present and unmodified; "
                           "write nothing, exit non-zero on drift")
    mode.add_argument("--prune", action="store_true",
                      help="remove orphan prompt files the manifest no longer selects (left by a "
                           "narrower re-install); never touches your own or edited files")
    mode.add_argument("--remove", action="store_true",
                      help="uninstall the kit for a tool: delete its kit-owned prompt files and an "
                           "unmodified guide, un-merge the settings deny rules; keeps edited files")
    args = parser.parse_args(argv)

    if args.list_only:
        cat = load_catalog(KIT_ROOT / "kit" / "catalog" / "catalog.json")
        print(f"outpost v{cat.version}")
        print(f"\nprompts ({len(cat.prompts)}):")
        for p in cat.prompts:
            print(f"  {p['name']:18} {p['summary']}")
        print(f"\ntemplates ({len(cat.templates)}):")
        for t in cat.templates:
            print(f"  {t['name']:18} {t['summary']}")
        print(f"\nadapters ({len(cat.adapters)}): " + ", ".join(a["tool"] for a in cat.adapters))
        return 0
    if not args.tool:
        parser.error("--tool is required (or pass --list to see what installs)")

    project_root = pathlib.Path(args.project).resolve()
    if not project_root.is_dir():
        print(f"error: project {project_root} is not a directory", file=sys.stderr)
        return 1

    cat = load_catalog(KIT_ROOT / "kit" / "catalog" / "catalog.json")

    if args.verify:
        # verify ignores --only/--exclude; the manifest is the record of what was installed
        print(f"verify '{args.tool}' against {project_root} (no files written)")
        try:
            manifest = _load_validated_manifest(project_root, {p["name"] for p in cat.prompts})
        except (ValueError, OSError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        actions = []
        orphans: list[str] = []
        leftovers: list[str] = []
        user_owned = _user_owned_paths(manifest, _tools_for(args.tool))
        try:
            for t in _tools_for(args.tool):
                sel = _selection_for(manifest, t)
                terse = _terse_for(manifest, t, args.terse)
                actions.extend(plan_for(t, KIT_ROOT, project_root, terse=terse, select=sel))
                orphans.extend(_orphans(project_root, t, sel, terse, user_owned))
                # a plan-derived check cannot see a kit-created file whose prompt no longer ships
                # to this host; the manifest's file records surface it as a leftover
                leftovers.extend(_retired_paths(project_root, t, manifest, terse))
        except (ValueError, OSError) as e:
            # a corrupt config (the Claude settings file) can't be planned against; say so cleanly
            print(f"error: {e}", file=sys.stderr)
            return 1
        ok, lines = verify(actions, project_root, user_owned)
        for line in lines:
            print(line)
        for path in orphans:
            print(f"  EXTRA   {path} (installed but not in the manifest; re-install or remove)")
        for path in leftovers:
            print(f"  LEFTOVER {path} (kit-installed, but the prompt no longer ships to this "
                  "host; --prune removes it)")
        # Terse state left behind after the recorded install stopped being terse is drift too
        # (F32): a stale style file or outputStyle key would silently keep changing the agent.
        # An edited style file ('keep') is the user's and is not drift.
        stale = []
        claude_entry = manifest.get("tools", {}).get("claude")
        if ("claude" in _tools_for(args.tool) and claude_entry
                and not _terse_for(manifest, "claude", args.terse)):
            stale = [(op, p) for op, p
                     in stale_terse_state(project_root, _kit_terse_proof(claude_entry))
                     if op != "keep"]
        for op, path in stale:
            if op == "clear":
                print(f"  DRIFTED {path} (kit-set outputStyle key lingers after terse was "
                      "withdrawn; re-install to clear it)")
            else:
                print(f"  DRIFTED {path} (stale terse state from an earlier terse install; "
                      "re-install to clean it)")
        # A stale version stamp is not file drift, so it never changes the verdict: print it as a
        # note after, whether the files are in sync or not.
        note = _version_note(manifest, cat.version)
        # An orphan is drift the other way: a kit-owned prompt the recorded selection excludes is
        # still on disk. verify is a gate, so extras fail it just like a missing or modified file.
        if ok and not orphans and not stale and not leftovers:
            print("in sync (kit files present and unmodified)")
            if note:
                print(note)
            return 0
        if not ok:
            print("DRIFT: re-run install to restore the kit files")
        if orphans:
            print(f"DRIFT: {len(orphans)} kit-owned prompt file(s) on disk are not in the manifest; "
                  "re-install the full pack or remove them")
        if leftovers:
            print(f"DRIFT: {len(leftovers)} kit-installed file(s) belong to a prompt that no "
                  "longer ships to this host; run --prune to remove them")
        if stale:
            print("DRIFT: stale terse state left by an earlier terse install; re-run install "
                  "to clean it")
        if note:
            print(note)
        return 1

    if args.prune:
        # prune reads the manifest (like verify) and removes only the orphan prompt files
        print(f"prune '{args.tool}' in {project_root}")
        try:  # validate names before any deletion
            manifest = _load_validated_manifest(project_root, {p["name"] for p in cat.prompts})
        except (ValueError, OSError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        try:
            removed, skipped, failed, retired = prune_orphans(
                project_root, _tools_for(args.tool), manifest, args.terse)
        except (ValueError, OSError) as e:
            # a corrupt config (the Claude settings file) can't be planned against; say so cleanly
            print(f"error: {e}", file=sys.stderr)
            return 1
        if retired or removed:
            # persist the ended ownership claims: prune_orphans dropped the file records for both
            # retired files and de-selected orphans, so the manifest must be rewritten either way
            mpath = _existing_manifest_path(project_root) or (project_root / MANIFEST_PATH)
            try:
                mpath.write_bytes(manifest_dumps(manifest).encode("utf-8"))
            except OSError as e:
                print(f"warning: could not update the manifest: {e}", file=sys.stderr)
        for p in removed:
            print(f"  remove {p}")
        for p in retired:
            print(f"  remove {p} (retired from this host)")
        for p in skipped:
            print(f"  skip   {p} (not created by the kit, or edited; left in place, "
                  "remove by hand if you do not want it)")
        for p in failed:
            print(f"  FAILED {p} (could not delete; check permissions)")
        if not removed and not retired and not skipped and not failed:
            print("nothing to prune (disk matches the manifest)")
        else:
            print(f"done. {len(removed) + len(retired)} removed, {len(skipped)} skipped, "
                  f"{len(failed)} failed.")
        return 1 if failed else 0

    if args.remove:
        print(f"remove '{args.tool}' from {project_root}")
        tools = _tools_for(args.tool)
        # read the manifest first: it records whether each tool was a terse install, so remove can
        # clean the terse style and outputStyle a plain --remove would otherwise miss
        try:
            manifest = _read_manifest(project_root)
        except (ValueError, OSError) as e:
            print(f"warning: manifest unreadable, left as-is: {e}", file=sys.stderr)
            manifest = {}
        removed, skipped, failed, retired = remove_for_tools(project_root, tools, manifest,
                                                             args.terse)
        settings = unmerge_kit_settings(project_root, tools, manifest, args.terse)
        # forget the removed tools in the manifest; delete it if no tool is left
        if manifest.get("tools"):
            for t in tools:
                manifest = drop_tool(manifest, t)
            mpath = project_root / MANIFEST_PATH
            try:
                if manifest.get("tools"):
                    mpath.parent.mkdir(parents=True, exist_ok=True)
                    mpath.write_bytes(manifest_dumps(manifest).encode("utf-8"))
                elif mpath.exists():
                    mpath.unlink()
                    _remove_empty_parents(mpath, project_root)
            except OSError as e:
                print(f"warning: could not update the manifest: {e}", file=sys.stderr)
        for p in removed:
            print(f"  remove {p}")
        for p in retired:
            print(f"  remove {p} (retired from this host)")
        for p, what in settings:
            if what in ("removed", "unmerged"):
                print(f"  {what:6} {p}")
        for p in skipped:
            print(f"  skip   {p} (not created by the kit, or edited; left in place)")
        for p in failed:
            print(f"  FAILED {p} (could not delete; check permissions)")
        settings_failed = [p for p, w in settings if w == "failed"]
        for p in settings_failed:
            print(f"  FAILED {p} (could not update; check permissions)")
        n_settings = sum(1 for _, w in settings if w in ("removed", "unmerged"))
        if (not removed and not retired and not skipped and not failed and not n_settings
                and not settings_failed):
            print("nothing to remove (no kit files found)")
        else:
            print(f"done. {len(removed) + len(retired) + n_settings} removed, "
                  f"{len(skipped)} kept (edited), "
                  f"{len(failed) + len(settings_failed)} failed.")
        return 1 if failed or settings_failed else 0

    try:
        select_label, select_set = resolve_selection(args.only, args.exclude,
                                                     {p["name"] for p in cat.prompts})
        if select_label == "only":
            # an --only name that is a real prompt but host-limited away from this tool would
            # otherwise install nothing for it silently; say so instead
            for t in _tools_for(args.tool):
                not_shipped = select_set - {p["name"] for p in cat.prompts_for(t)}
                if not_shipped:
                    print(f"warning: {', '.join(sorted(not_shipped))} does not ship to {t}; "
                          "skipped for that tool", file=sys.stderr)
        actions = plan_for(args.tool, KIT_ROOT, project_root, terse=args.terse, select=select_set)
        # inside the try: a corrupt existing manifest must fail cleanly, like a bad settings file
        prev_manifest = _read_manifest(project_root)
        records_by_tool = {t: _file_records(project_root, t, args.terse, select_set, prev_manifest)
                           for t in _tools_for(args.tool)}
        # A path apply() will actually skip (it resolves outside the project via a symlink) must
        # carry no ownership record at all: a false "the kit created this" claim is what lets a
        # later --remove or --prune delete a file this install never touched (the F1/F3 finding
        # from ADR-0030's own risk-review dogfood run). Every consuming guard already treats "no
        # record" as "no proof of ownership, leave it alone", so removing the record is sufficient;
        # no new guard vocabulary is needed downstream.
        for t in _tools_for(args.tool):
            for a in plan_for(t, KIT_ROOT, project_root, terse=args.terse, select=select_set):
                if a.mode in ("write", "create", "merge") and not _is_contained(project_root, a.path):
                    records_by_tool[t].pop(a.path, None)
        # A completed withdrawal (this run deletes the kit's own style file) ends the kit's
        # ownership claim on that path, so it never seizes a later hand-adopted style with the
        # kit's own bytes and the user's own key (the F32 residual, PR 101).
        if ("remove", TERSE_STYLE_PATH) in _withdrawn_terse(project_root, prev_manifest, args.tool,
                                                            args.terse):
            records_by_tool.get("claude", {}).pop(TERSE_STYLE_PATH, None)
        actions.append(manifest_action(prev_manifest, args.tool, select_label, select_set, cat,
                                       args.terse, records_by_tool))
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    protected = {p for recs in records_by_tool.values()
                 for p, rec in recs.items() if rec.get("existed")}

    if args.dry_run:
        print(f"dry-run: install '{args.tool}' into {project_root} (no files written)")
        for line in render_plan(actions, project_root, protected):
            print(line)
        for op, path in _withdrawn_terse(project_root, prev_manifest, args.tool, args.terse):
            verb = {"remove": "remove stale terse style", "clear": "clear stale outputStyle",
                    "keep": "keep edited terse style"}[op]
            print(f"  [{op:14}] clean  {path}  - {verb} (terse withdrawn by this install)")
        return 0

    print(f"install '{args.tool}' into {project_root}")
    try:
        tally = apply(actions, project_root, protected)
    except OSError as e:
        print(f"error: install failed partway: {e}", file=sys.stderr)
        print("some files may be written; fix the cause and re-run (install is idempotent).",
              file=sys.stderr)
        return 1
    apply_stale_terse(project_root,
                      _withdrawn_terse(project_root, prev_manifest, args.tool, args.terse))
    print(f"done. {tally['create']} created, {tally['update']} updated, "
          f"{tally['skip (exists)']} skipped, {tally['unchanged']} unchanged. "
          "restart your agent so it picks up the new files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
