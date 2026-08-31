"""The three append-only ledgers hold their contract, so a record cannot rot silently.

- Decisions: every `docs/decisions/NNNN-*.md` (minus the template) is in the README index list
  and vice versa; numbers are unique and contiguous from 0001; every record carries a Status
  line (Proposed, Accepted, or Superseded by NNNN, where NNNN exists) and a Date line.
- Debt: `docs/DEBT.md` has its Open and Closed sections, every entry starts with a date, and
  every repo-path-shaped backtick token in an Open entry resolves to a tracked file or
  directory, so a closed or renamed file cannot leave a stale Open entry behind.
- Roadmap: `docs/ROADMAP.md` carries its four required section headings.

Path resolution and the decisions scan prefer git's tracked set, so an untracked local draft
never trips the check; without git they fall back to the working tree, the same trade the
content scans make.
"""
from __future__ import annotations

import pathlib
import re

from . import tracked_files

DECISIONS_DIR = "docs/decisions"
DEBT = "docs/DEBT.md"
ROADMAP = "docs/ROADMAP.md"

RECORD_NAME = re.compile(r"^(\d{4})-.+\.md$")
# An index bullet is `- NNNN: title`. Any README bullet starting with a bare four-digit number
# (a year, say) reads as an index entry, so the decisions README keeps such prose out of
# bullet leads; its intro states that constraint.
INDEX_ENTRY = re.compile(r"(?m)^- (\d{4}):")
STATUS_LINE = re.compile(r"(?m)^Status:\s*(.+?)\s*$")
SUPERSEDED = re.compile(r"^Superseded by (\d{4})$")
DATE_LINE = re.compile(r"(?m)^Date:\s*\d{4}-\d{2}-\d{2}\s*$")
ENTRY_DATE = re.compile(r"^- \d{4}-\d{2}-\d{2}:")
TOKEN = re.compile(r"`([^`\n]+)`")
PATH_SUFFIXES = (".py", ".md", ".json", ".yml", ".toml")
ROADMAP_HEADINGS = ("## Planned", "## Out of scope", "## Idea backlog", "## How an item moves")


def _looks_like_path(token: str) -> bool:
    """A backtick token shaped like a repo path: has a slash or a known file suffix. A flag
    (`--verify`), a bare name (`pct`), a spaced command, or a glob (`*.md`) is prose, not a
    path."""
    if any(ch.isspace() for ch in token) or token.startswith("-"):
        return False
    if any(ch in token for ch in "*?["):
        return False
    return "/" in token or token.endswith(PATH_SUFFIXES)


def _resolves(root: pathlib.Path, tracked: list[str] | None, token: str) -> bool:
    """The token names a tracked file, or a directory some tracked file lives under. Without
    git, existence in the working tree stands in. Backslashes normalize to POSIX first, so
    both modes agree on a Windows-styled token."""
    rel = token.replace("\\", "/").strip("/")
    if tracked is not None:
        return any(f == rel or f.startswith(rel + "/") for f in tracked)
    return (root / rel).exists()


def _sections(text: str) -> dict[str, list[str]]:
    """The lines under each `## <name>` heading, keyed by name."""
    out: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = out.setdefault(line[3:].strip(), [])
            continue
        if current is not None:
            current.append(line)
    return out


def _entries(lines: list[str]) -> list[str]:
    """Each `- ` bullet with its wrapped continuation lines, joined to one string."""
    entries: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("- "):
            if current:
                entries.append(" ".join(current))
            current = [line]
        elif current and line.strip():
            current.append(line.strip())
    if current:
        entries.append(" ".join(current))
    return entries


def _check_decisions(root: pathlib.Path, tracked: list[str] | None,
                     errors: list[str]) -> int:
    ddir = root / DECISIONS_DIR
    tracked_set = set(tracked) if tracked is not None else None
    records: dict[str, str] = {}
    for p in sorted(ddir.glob("*.md")):
        m = RECORD_NAME.match(p.name)
        if not m or p.name == "0000-template.md":
            continue
        if tracked_set is not None and f"{DECISIONS_DIR}/{p.name}" not in tracked_set:
            continue  # an untracked local draft is scratch, not a record under contract
        num = m.group(1)
        if num in records:
            errors.append(f"decision number {num} is used twice "
                          f"({DECISIONS_DIR}/{records[num]} and {DECISIONS_DIR}/{p.name})")
        else:
            records[num] = p.name

    nums = sorted(int(n) for n in records)
    missing = sorted(set(range(1, len(nums) + 1)) - set(nums))
    if missing:
        errors.append("decision numbers are not contiguous from 0001: missing "
                      + ", ".join(f"{n:04d}" for n in missing))

    readme = ddir / "README.md"
    if not readme.is_file():
        errors.append(f"{DECISIONS_DIR}/README.md is missing")
        return len(records)
    indexed = set(INDEX_ENTRY.findall(readme.read_text(encoding="utf-8")))
    for num in sorted(set(records) - indexed):
        errors.append(f"{DECISIONS_DIR}/{records[num]} is not in the index list in "
                      f"{DECISIONS_DIR}/README.md")
    for num in sorted(indexed - set(records)):
        errors.append(f"index entry {num} in {DECISIONS_DIR}/README.md has no record file")

    for num, name in sorted(records.items()):
        text = (ddir / name).read_text(encoding="utf-8")
        m = STATUS_LINE.search(text)
        if not m:
            errors.append(f"{DECISIONS_DIR}/{name}: no Status: line")
        else:
            value = m.group(1)
            if value not in ("Proposed", "Accepted"):
                sup = SUPERSEDED.match(value)
                if not sup:
                    errors.append(f"{DECISIONS_DIR}/{name}: Status {value!r} is not Proposed, "
                                  "Accepted, or Superseded by NNNN")
                elif sup.group(1) not in records:
                    errors.append(f"{DECISIONS_DIR}/{name}: Superseded by {sup.group(1)}, "
                                  "which has no record")
        if not DATE_LINE.search(text):
            errors.append(f"{DECISIONS_DIR}/{name}: no Date: YYYY-MM-DD line")
    return len(records)


def _check_debt(root: pathlib.Path, tracked: list[str] | None,
                errors: list[str]) -> tuple[int, int]:
    p = root / DEBT
    if not p.is_file():
        errors.append(f"{DEBT} is missing")
        return 0, 0
    sections = _sections(p.read_text(encoding="utf-8"))
    for heading in ("Open", "Closed"):
        if heading not in sections:
            errors.append(f'{DEBT} has no "## {heading}" heading')
    open_entries = _entries(sections.get("Open", []))
    closed_entries = _entries(sections.get("Closed", []))
    for section, entries in (("Open", open_entries), ("Closed", closed_entries)):
        for entry in entries:
            if not ENTRY_DATE.match(entry):
                errors.append(f"{DEBT}: {section} entry does not start with a YYYY-MM-DD "
                              f"date: {entry[:50]!r}")
    for entry in open_entries:
        for token in TOKEN.findall(entry):
            if _looks_like_path(token) and not _resolves(root, tracked, token):
                errors.append(f"{DEBT}: Open entry names `{token}`, which is not a tracked "
                              "file or directory")
    return len(open_entries), len(closed_entries)


def _check_roadmap(root: pathlib.Path, errors: list[str]) -> int:
    p = root / ROADMAP
    if not p.is_file():
        errors.append(f"{ROADMAP} is missing")
        return 0
    text = p.read_text(encoding="utf-8")
    headings = {line.strip() for line in text.splitlines() if line.startswith("## ")}
    for h in ROADMAP_HEADINGS:
        if h not in headings:
            errors.append(f'{ROADMAP} is missing the "{h}" heading')
    return len(_entries(_sections(text).get("Idea backlog", [])))


def run(root: pathlib.Path) -> tuple[bool, str]:
    errors: list[str] = []
    tracked = tracked_files(root)
    n_records = _check_decisions(root, tracked, errors)
    n_open, n_closed = _check_debt(root, tracked, errors)
    n_backlog = _check_roadmap(root, errors)
    if errors:
        return False, "; ".join(errors[:10])
    return True, (f"{n_records} decision records indexed; {n_open} open and {n_closed} closed "
                  f"debt entries; {n_backlog} backlog items")
