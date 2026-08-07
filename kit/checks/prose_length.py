"""A paragraph in tracked markdown clears a mechanical word-count ceiling, so the house voice's
concision rule (docs/writing-standard.md) has a gate behind it, not editorial judgment alone.
Append-only historical ledgers are exempt: an old entry there cannot be rewritten to comply
without breaking the record's own append-only rule (docs/decisions/, docs/DEBT.md,
docs/dogfooding.md, docs/audit/).

A paragraph is a maximal run of consecutive non-blank lines that are not a heading, a list item,
a table row, a blockquote, or inside a fenced code block: the prose a reader reads as one block,
not a structured element with its own shape.
"""
from __future__ import annotations

import pathlib
import re

from . import split_frontmatter, walk_markdown

MAX_PARAGRAPH_WORDS = 100

EXEMPT_DIRS = ("docs/decisions", "docs/audit")
EXEMPT_FILES = ("docs/DEBT.md", "docs/dogfooding.md")

_STRUCTURAL = re.compile(r"^(#|-|\*|\||>|\d+\.)")


def is_exempt(rel: str) -> bool:
    if rel in EXEMPT_FILES:
        return True
    return any(rel == d or rel.startswith(d + "/") for d in EXEMPT_DIRS)


def paragraphs(body: str) -> list[str]:
    """Every prose paragraph in a markdown body, joined to one line each, in source order."""
    result: list[str] = []
    current: list[str] = []
    in_code = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            if current:
                result.append(" ".join(current))
                current = []
            continue
        if in_code:
            continue
        if not stripped or _STRUCTURAL.match(stripped):
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
