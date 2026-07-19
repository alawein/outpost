"""Validation checks. Each module exposes `run(root) -> (ok, detail)`. `run.py` reads the catalog's
check list and runs them in order, so the catalog stays the source of truth for what the gate runs.

Shared helpers live here: the ignore set, a markdown walker, a tracked-file lister, and the banned
register (kept in sync with docs/writing-standard.md).
"""
from __future__ import annotations

import pathlib
import re
import subprocess

IGNORE = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules",
          "build", "dist", ".mypy_cache", ".ruff_cache"}

# The banned register, kept in sync with docs/writing-standard.md (that file is the source of truth
# and is exempt from the scan, since it names these words to ban them).
BANNED = ("comprehensive", "robust", "leverage", "streamline", "seamless", "delve", "holistic",
          "cutting-edge", "powerful", "moreover", "furthermore", "utilize")
BANNED_RE = [(w, re.compile(rf"(?i)\b{re.escape(w)}\b")) for w in BANNED]

# Prompt-reference regexes, shared so doc_truth, template_refs, and plugin_sync key on one shape.
# REF: a backtick kebab token, two or more lowercase words hyphen-joined, no dot or slash (a prompt
# name in prose). SKILL_REF: the same but also matches single-word names (grill, premortem) that
# REF skips; used where the surrounding text is known to name only prompts (a command file scan).
REF = re.compile(r"`([a-z]+(?:-[a-z]+)+)`")
SKILL_REF = re.compile(r"`([a-z]+(?:-[a-z]+)*)`")


def is_ignored(p: pathlib.Path) -> bool:
    return any(part in IGNORE for part in p.parts)


def walk_markdown(root: pathlib.Path):
    """Yield the markdown the gate should judge: git-tracked .md files, minus the IGNORE dirs.
    Untracked scratch (an SDD brief, a local note) must not trip a voice or docs check. When this is
    not a git repo (tracked_files is None), fall back to scanning every non-ignored .md so a clean
    source tarball is still judged honestly."""
    tracked = tracked_files(root)
    tracked_md = None
    if tracked is not None:
        tracked_md = {(root / f).resolve() for f in tracked if f.endswith(".md")}
    for p in sorted(root.rglob("*.md")):
        if is_ignored(p.relative_to(root)):
            continue
        if tracked_md is not None and p.resolve() not in tracked_md:
            continue
        yield p


def banned_hits(text: str) -> list[str]:
    return [w for w, rx in BANNED_RE if rx.search(text)]


def split_frontmatter(text: str) -> tuple[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    return (m.group(1), m.group(2)) if m else ("", text)


def frontmatter_field(frontmatter: str, key: str) -> str | None:
    m = re.search(rf"(?m)^{key}:\s*(.+?)\s*$", frontmatter)
    return m.group(1).strip().strip('"').strip("'") if m else None


def tracked_files(root: pathlib.Path) -> list[str] | None:
    """Return repo-relative POSIX paths git is tracking, or None when this is not a git repo or git
    is unavailable. Checks that depend on what is committed use this so a local cache never trips
    them and a clean clone is judged honestly."""
    try:
        proc = subprocess.run(["git", "-C", str(root), "ls-files"],
                              capture_output=True, text=True)
    except (OSError, FileNotFoundError):
        return None
    if proc.returncode != 0:
        return None
    files = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return files


def table_after(text: str, heading: str) -> list[str]:
    """The markdown table rows (lines starting with '|') in the section under `## <heading>`.
    Shared by the doc checks so the heading-anchored table scan lives in one place."""
    rows: list[str] = []
    in_section = False
    for line in text.splitlines():
        if line.strip().startswith("## "):
            in_section = line.strip().lstrip("#").strip() == heading
            continue
        if in_section and line.lstrip().startswith("|"):
            rows.append(line)
        elif in_section and rows and not line.strip():
            break  # a blank line after the table ends it
    return rows


def compare_generated(root: pathlib.Path, generated: dict) -> tuple[list[str], list[str]]:
    """Compare a builder's {path: content} map against disk. Return (missing, drifted): the
    generated paths absent from disk, and those whose on-disk content differs from the builder
    output. Shared by the *_sync checks that guard a fully generated tree (plugin, templates)."""
    missing: list[str] = []
    drifted: list[str] = []
    for rel, expected in generated.items():
        p = root / rel
        if not p.is_file():
            missing.append(rel)
        elif p.read_text(encoding="utf-8") != expected:
            drifted.append(rel)
    return missing, drifted


def scan_candidates(root: pathlib.Path) -> tuple[list[str], bool]:
    """Return (relative POSIX paths, from_git) for the content scans. Prefer git's tracked set;
    fall back to a working-tree walk minus the ignore set so the scan never silently skips.
    Shared by secrets and traces."""
    tracked = tracked_files(root)
    if tracked is not None:
        return tracked, True
    walked = [p.relative_to(root).as_posix()
              for p in root.rglob("*")
              if p.is_file() and not is_ignored(p.relative_to(root))]
    return walked, False
