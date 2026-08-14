"""GitHub issue forms have a valid structural shape: no duplicate id: within one form, and every
dropdown or checkboxes field has at least one options: entry. GitHub only surfaces these errors in
the browser at "New issue"; nothing in this repo's own gate did until now. Scoped to
.github/ISSUE_TEMPLATE/*.yml, matching label_refs.py's regex-line-scan style rather than a YAML
parser, per the kit's stdlib-only constraint.
"""
from __future__ import annotations

import pathlib
import re

_ID = re.compile(r"^\s*id:\s*(\S+)\s*$")
_TYPE = re.compile(r"^\s*-\s*type:\s*(?P<kind>\S+)\s*$")
_OPTIONS_KEY = re.compile(r"^\s*options:\s*$")
_LIST_ITEM = re.compile(r"^\s*-\s*\S")

_OPTIONED_KINDS = {"dropdown", "checkboxes"}


def duplicate_ids(lines: list[str]) -> list[str]:
    """Every id value that appears more than once, each named the first time it repeats."""
    seen: dict[str, int] = {}
    dupes: list[str] = []
    for line in lines:
        m = _ID.match(line)
        if not m:
            continue
        value = m.group(1)
        seen[value] = seen.get(value, 0) + 1
        if seen[value] == 2:
            dupes.append(value)
    return dupes


def _blocks(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Split into (kind, block_lines) per body item: from each '- type: <kind>' line up to just
    before the next one, or end of file. A GitHub issue-form body is always a flat list of field
    objects, so a new '- type:' line always starts the next field."""
    starts = [(i, m.group("kind")) for i, line in enumerate(lines) for m in [_TYPE.match(line)] if m]
    blocks = []
    for idx, (start, kind) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        blocks.append((kind, lines[start:end]))
    return blocks


def fields_missing_options(lines: list[str]) -> list[str]:
    """The kind (dropdown/checkboxes) of every field block that has no options: key followed by
    at least one list item, in the order the blocks appear."""
    missing: list[str] = []
    for kind, block in _blocks(lines):
        if kind not in _OPTIONED_KINDS:
            continue
        seen_options_key = False
        has_option_item = False
        for line in block:
            if _OPTIONS_KEY.match(line):
                seen_options_key = True
                continue
            if seen_options_key and _LIST_ITEM.match(line):
                has_option_item = True
        if not (seen_options_key and has_option_item):
            missing.append(kind)
    return missing


def run(root: pathlib.Path) -> tuple[bool, str]:
    forms_dir = root / ".github" / "ISSUE_TEMPLATE"
    if not forms_dir.is_dir():
        return True, "no issue forms yet; nothing to check"
    files = sorted(forms_dir.glob("*.yml"))
    if not files:
        return True, "no issue forms yet; nothing to check"
    errors: list[str] = []
    for p in files:
        lines = p.read_text(encoding="utf-8").splitlines()
        rel = p.relative_to(root).as_posix()
        for dup in duplicate_ids(lines):
            errors.append(f"{rel}: duplicate id {dup!r}")
        for kind in fields_missing_options(lines):
            errors.append(f"{rel}: a {kind} field has no options")
    if errors:
        return False, "; ".join(errors[:10])
    return True, f"{len(files)} issue form(s) have no duplicate ids and every dropdown/checkboxes has options"
