"""No personal trace in the tracked tree. A tracked file that carries the maintainer's email,
home directory, or sync-estate path encodes one person's machine setup as a default and ships it
on every install. This scans the tracked set against a short marker list and fails on any hit
outside an allowed home.

Allowed homes: .github/CODEOWNERS (review routing needs real handles), docs/decisions/ (append-only
records are never edited), CHANGELOG.md (an append-only ledger), and this file (the markers live
here by design). Gitignored scratch never trips the git-tracked scan; the no-git fallback walk
skips the known scratch roots so a working-copy run matches.
"""
from __future__ import annotations

import pathlib
import re

from . import scan_candidates

TRACE_PATTERNS = [
    ("personal email", re.compile(r"(?i)\bmeshal@|@meshal\.ai\b|\bkohyr\.ai\b")),
    ("home directory path", re.compile(r"(?i)[\\/]+(?:Users|home)[\\/]+meshal?\b")),
    ("sync estate path", re.compile(r"(?i)Dropbox[\\/]+Desktop")),
]
ALLOWED = (".github/CODEOWNERS", "kit/checks/traces.py", "CHANGELOG.md")
ALLOWED_DIRS = ("docs/decisions/",)
SCRATCH_DIRS = (".superpowers/", "docs/superpowers/")


def run(root: pathlib.Path) -> tuple[bool, str]:
    files, from_git = scan_candidates(root)
    errors: list[str] = []
    for rel in files:
        if rel in ALLOWED or rel.startswith(ALLOWED_DIRS) or rel.startswith(SCRATCH_DIRS):
            continue
        try:
            raw = (root / rel).read_bytes()
        except OSError as e:
            # fail closed: a file we cannot read is unverifiable, not clean
            errors.append(f"{rel}: unreadable, cannot verify ({e})")
            continue
        # decode latin-1 (1:1, never raises) so a trace in a non-UTF-8 file is still caught
        text = raw.decode("latin-1")
        for label, rx in TRACE_PATTERNS:
            if rx.search(text):
                errors.append(f"{rel}: {label}")
    if errors:
        return False, "; ".join(errors[:10])
    source = "tracked" if from_git else "working-tree (no git)"
    return True, f"{len(files)} {source} files carry no personal trace"
