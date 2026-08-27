"""The banned register in docs/writing-standard.md matches the one the voice check enforces.

The word list lives in two places: `BANNED` in kit/checks/__init__.py (what the gate rejects) and
the "Banned register" section of docs/writing-standard.md (the source of truth a human reads). If a
word is added to the doc but not the code, the gate never enforces it; the reverse silently rejects
a word the standard never named. Nothing tied them together, the same drift class as a count living
outside what the checks read. This check parses the doc's list and requires set-equality both ways.
"""
from __future__ import annotations

import pathlib
import re

from . import BANNED

# The doc names the words on one line in the "Banned register" section, after a colon, comma-
# separated, ending in a period: "... do not swap the word: comprehensive, robust, ... utilize."
_SECTION = "## Banned register"


def _doc_words(text: str) -> set[str] | None:
    start = text.find(_SECTION)
    if start == -1:
        return None
    section = text[start + len(_SECTION):]
    # the first line in the section that carries a colon then a comma-separated run of words
    for line in section.splitlines():
        if ":" in line and line.count(",") >= 2:
            listing = line.rsplit(":", 1)[1].strip().rstrip(".")
            return {w.strip() for w in listing.split(",") if w.strip()}
    return None


def run(root: pathlib.Path) -> tuple[bool, str]:
    doc = root / "docs" / "writing-standard.md"
    try:
        text = doc.read_text(encoding="utf-8")
    except OSError as e:
        return False, f"cannot read {doc.name}: {e}"
    words = _doc_words(text)
    if words is None:
        return False, "could not find the banned-register word list in writing-standard.md"
    code = set(BANNED)
    only_doc = sorted(words - code)
    only_code = sorted(code - words)
    if only_doc or only_code:
        parts = []
        if only_doc:
            parts.append("in the doc but not enforced: " + ", ".join(only_doc))
        if only_code:
            parts.append("enforced but not in the doc: " + ", ".join(only_code))
        return False, "banned register out of sync (" + "; ".join(parts) + ")"
    return True, f"banned register in sync ({len(code)} words)"
