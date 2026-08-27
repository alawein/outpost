"""A paragraph in tracked markdown clears a mechanical word-count ceiling, so the house voice's
concision rule (docs/writing-standard.md) has a gate behind it, not editorial judgment alone.
Append-only historical ledgers are exempt: an old entry there cannot be rewritten to comply
without breaking the record's own append-only rule (docs/DEBT.md,
docs/decisions/).

A paragraph is a maximal run of consecutive non-blank lines that are not a heading, a list item
(or that item's wrapped continuation lines), a table row, a blockquote, or inside a fenced code
block: the prose a reader reads as one block, not a structured element with its own shape. A
list item's own length is not measured, wrapped or not; only narrative paragraphs are.
"""
from __future__ import annotations

import pathlib
import re

from . import split_frontmatter, walk_markdown

MAX_PARAGRAPH_WORDS = 100

EXEMPT_FILES = ("docs/DEBT.md",)
EXEMPT_DIRS = ("docs/decisions",)

# A marker requires trailing whitespace (or end of line) so it cannot match the start of a
# prose word: "**bold**", "--force", and "1.5 times" are prose, not a heading, list item, or
# ordinal. "|" and ">" (a table row, a blockquote) stay bare: this repo's prose does not open a
# line with either character.
_STRUCTURAL = re.compile(r"^(#+(\s|$)|[-*+](\s|$)|\d+\.(\s|$)|\||>)")
_LIST_ITEM = re.compile(r"^[-*+](\s|$)|^\d+\.(\s|$)")
_FENCE = re.compile(r"^(```|~~~)")


def is_exempt(rel: str) -> bool:
    if rel in EXEMPT_FILES:
        return True
    return any(rel == d or rel.startswith(d + "/") for d in EXEMPT_DIRS)


def paragraphs(body: str) -> list[str]:
    """Every prose paragraph in a markdown body, joined to one line each, in source order."""
    result: list[str] = []
    current: list[str] = []
    in_code = False
    in_list_item = False
    for line in body.splitlines():
        stripped = line.strip()
        if _FENCE.match(stripped):
            in_code = not in_code
            if current:
                result.append(" ".join(current))
                current = []
            in_list_item = False
            continue
        if in_code:
            continue
        if not stripped:
            if current:
                result.append(" ".join(current))
                current = []
            in_list_item = False
            continue
        if _LIST_ITEM.match(stripped):
            if current:
                result.append(" ".join(current))
                current = []
            in_list_item = True
            continue
        if in_list_item:
            # a wrapped continuation of the list item above: still not measured, unless it is
            # itself a new structural line (a heading, a table row, a blockquote)
            if _STRUCTURAL.match(stripped):
                in_list_item = False
            else:
                continue
        if _STRUCTURAL.match(stripped):
            if current:
                result.append(" ".join(current))
                current = []
            continue
        current.append(stripped)
    if current:
        result.append(" ".join(current))
    return result


def run(root: pathlib.Path) -> tuple[bool, str]:
    errors: list[str] = []
    checked = 0
    for p in walk_markdown(root):
        rel = p.relative_to(root).as_posix()
        if is_exempt(rel):
            continue
        checked += 1
        _, body = split_frontmatter(p.read_text(encoding="utf-8"))
        for para in paragraphs(body):
            words = len(para.split())
            if words > MAX_PARAGRAPH_WORDS:
                errors.append(
                    f"{rel}: paragraph too long ({words} words, max {MAX_PARAGRAPH_WORDS}): "
                    f"{para[:60]!r}...")
    if errors:
        return False, "; ".join(errors[:10])
    return True, f"{checked} docs clear the {MAX_PARAGRAPH_WORDS}-word paragraph ceiling"
