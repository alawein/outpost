"""Doc generator: splice catalog-derived content into hand-authored docs at marked spans.

`build_docs(root)` returns a dict mapping each affected doc's repo-relative path to its full new
content, for every doc whose spliced content differs from what is on disk (mirrors
`templates_sync`'s drift-only reporting). Unlike `kit.plugin.build_plugin` and
`kit.templates_build.build_templates`, this generator reads its own output targets: only the
content between paired `<!-- GENERATED:<key> --> ... <!-- /GENERATED:<key> -->` markers is
replaced, so every hand-written byte outside a marker survives untouched. Run
`python tools/build.py docs` after a catalog change that affects a marked span (a new core
prompt or a stage rename).
"""
from __future__ import annotations

import pathlib
import re
from typing import Callable

from .catalog import load_catalog

MARKER = re.compile(r"<!-- GENERATED:([a-z0-9-]+) -->(.*?)<!-- /GENERATED:\1 -->", re.DOTALL)

DOC_FILES = ("README.md", "docs/onboarding.md", "docs/workflow.md", "docs/plugin.md", "docs/ROADMAP.md")

# The marker keys each doc is expected to carry. build_docs raises ValueError if any of these is
# missing from a doc's real markers, so a stripped marker (e.g. a hand-edit that reflows README.md
# and drops the comment pair around the prompt-pack table) fails the build loudly instead of silently
# un-verifying that content. docs/onboarding.md carries no marker today, so it has no entry here.
REQUIRED_MARKERS = {
    "README.md": {"core-count-words"},
    "docs/workflow.md": {"skills-table", "core-count-digits"},
    "docs/plugin.md": {"core-count-words"},
    "docs/ROADMAP.md": {"core-count-words", "stage-counts", "checks-line"},
}

_WORDS = {
    0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
    7: "seven", 8: "eight",
    9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen",
    15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen",
    20: "twenty", 21: "twenty-one", 22: "twenty-two", 23: "twenty-three", 24: "twenty-four",
    25: "twenty-five", 26: "twenty-six", 27: "twenty-seven", 28: "twenty-eight",
    29: "twenty-nine", 30: "thirty",
}


def _word(n: int) -> str:
    """A small-integer word form. Raises ValueError past the known range rather than guessing,
    so a catalog growth past today's covered range fails loudly instead of rendering a digit."""
    if n not in _WORDS:
        raise ValueError(f"no word form registered for {n}; extend _WORDS in kit/docs_build.py")
    return _WORDS[n]


def _render_skills_table(cat) -> str:
    stage_names = {s["name"] for s in cat.stages}
    for p in cat.prompts:
        if p["stage"] not in stage_names:
            raise ValueError(
                f"core prompt {p['name']!r} has stage {p['stage']!r}, "
                f"which is not in the catalog's stages list"
            )
    by_stage: dict[str, list[dict]] = {s["name"]: [] for s in cat.stages}
    for p in cat.prompts:
        by_stage[p["stage"]].append(p)
    lines = []
    for stage in cat.stages:
        prompts = by_stage[stage["name"]]
        names = " ".join(f"`{p['name']}`" for p in prompts)
        lines.append(f"| {stage['name']} | {names} | {stage['summary']} |")
    header = "| Stage | Prompts | Use them to |\n|---|---|---|"
    return "\n" + header + "\n" + "\n".join(lines) + "\n"


def _render_core_count_words(cat) -> str:
    return _word(len(cat.prompts))


def _render_core_count_digits(cat) -> str:
    return str(len(cat.prompts))


def _render_stage_counts(cat) -> str:
    parts = []
    for stage in cat.stages:
        count = sum(p["stage"] == stage["name"] for p in cat.prompts)
        parts.append(f"{_word(count)} {stage['name'].lower()}")
    if len(parts) < 2:
        return "".join(parts)
    return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def _render_checks_line(cat) -> str:
    names = ", ".join(c["name"] for c in cat.checks)
    return f"{_word(len(cat.checks))} checks ({names})"


_OPEN = re.compile(r"<!-- GENERATED:([a-z0-9-]+) -->")
_CLOSE = re.compile(r"<!-- /GENERATED:([a-z0-9-]+) -->")


def apply_markers(text: str, renderers: dict[str, Callable[[], str]]) -> str:
    """Replace the inner content of every `<!-- GENERATED:<key> -->...<!-- /GENERATED:<key> -->`
    pair in `text` with `renderers[key]()`. Raises ValueError if a marker's key is not in
    `renderers` (an unknown or typo'd key), or if a doc has an unmatched marker (only one of the
    open/close pair present, invisible to `MARKER`'s single combined regex and so checked
    separately here). Both fail the build loudly rather than passing through silently."""
    from collections import Counter
    opens = Counter(m.group(1) for m in _OPEN.finditer(text))
    closes = Counter(m.group(1) for m in _CLOSE.finditer(text))
    if opens != closes:
        unmatched = sorted(set(opens) | set(closes))
        raise ValueError(f"unmatched GENERATED marker(s): {unmatched}")

    def _sub(m: re.Match) -> str:
        key = m.group(1)
        if key not in renderers:
            raise ValueError(f"unknown GENERATED marker key {key!r}")
        return f"<!-- GENERATED:{key} -->{renderers[key]()}<!-- /GENERATED:{key} -->"
    return MARKER.sub(_sub, text)


def build_docs(root: pathlib.Path) -> dict[str, str]:
    """Return {doc path: new full content} for every doc in DOC_FILES whose spliced content
    differs from what is currently on disk. A doc with zero markers is a no-op (not included in
    the result), unless it is listed in REQUIRED_MARKERS, in which case a missing required marker
    raises instead of silently no-op'ing. Raises ValueError (propagated from apply_markers, or
    raised directly here) on an unknown marker key, an unmatched marker pair, or a doc missing one
    of its required markers."""
    cat = load_catalog(root / "kit" / "catalog" / "catalog.json")
    renderers = {
        "skills-table": lambda: _render_skills_table(cat),
        "core-count-words": lambda: _render_core_count_words(cat),
        "core-count-digits": lambda: _render_core_count_digits(cat),
        "stage-counts": lambda: _render_stage_counts(cat),
        "checks-line": lambda: _render_checks_line(cat),
    }
    out: dict[str, str] = {}
    for rel in DOC_FILES:
        p = root / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        missing = REQUIRED_MARKERS.get(rel, set()) - {m.group(1) for m in _OPEN.finditer(text)}
        if missing:
            raise ValueError(f"{rel}: missing required GENERATED marker(s): {sorted(missing)}")
        if not _OPEN.search(text) and not _CLOSE.search(text):
            continue
        new_text = apply_markers(text, renderers)
        if new_text != text:
            out[rel] = new_text
    return out
