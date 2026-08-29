"""Doc generator: splice catalog-derived content into hand-authored docs at marked spans.

`build_docs(root)` returns a dict mapping each affected doc's repo-relative path to its full new
content, for every doc whose spliced content differs from what is on disk (mirrors
`templates_sync`'s drift-only reporting). Unlike `kit.plugin.build_plugin` and
`kit.templates_build.build_templates`, this generator reads its own output targets: only the
content between paired `<!-- GENERATED:<key> --> ... <!-- /GENERATED:<key> -->` markers is
replaced, so every hand-written byte outside a marker survives untouched. Run
`python tools/build.py docs` after a catalog change that affects a marked span (a new core
prompt or a stage rename), or after a benchmark rerun changes `benchmarks/drift/results.json`
(the README headline is rendered from its totals).
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Callable

from .catalog import load_catalog

MARKER = re.compile(r"<!-- GENERATED:([a-z0-9-]+) -->(.*?)<!-- /GENERATED:\1 -->", re.DOTALL)

DOC_FILES = ("README.md", "docs/onboarding.md", "docs/workflow.md", "docs/plugin.md", "docs/ROADMAP.md")

BENCHMARK_RESULTS = pathlib.Path("benchmarks") / "drift" / "results.json"

# The marker keys each doc is expected to carry. build_docs raises ValueError if any of these is
# missing from a doc's real markers, so a stripped marker (e.g. a hand-edit that reflows README.md
# and drops the comment pair around the prompt-pack table) fails the build loudly instead of silently
# un-verifying that content. docs/onboarding.md carries no marker today, so it has no entry here.
# README.md's benchmark-headline is the hero claim, rendered from the drift benchmark's results
# file, so the front page cannot quote a number the benchmark no longer produces.
REQUIRED_MARKERS = {
    "README.md": {"core-count-words", "benchmark-headline"},
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


def _group_by_stage(cat) -> dict[str, list[dict]]:
    """Every core prompt bucketed under its stage name. Raises ValueError if a prompt's stage
    is not in the catalog's stages list (a typo'd or renamed stage), so a bad reference fails
    loudly here instead of silently dropping that prompt from every stage-derived render."""
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
    return by_stage


def _render_skills_table(cat) -> str:
    by_stage = _group_by_stage(cat)
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
    by_stage = _group_by_stage(cat)
    parts = [f"{_word(len(by_stage[stage['name']]))} {stage['name'].lower()}" for stage in cat.stages]
    if len(parts) < 2:
        return "".join(parts)
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def _render_checks_line(cat) -> str:
    names = ", ".join(c["name"] for c in cat.checks)
    return f"{_word(len(cat.checks))} checks ({names})"


def _render_benchmark_headline(root: pathlib.Path) -> str:
    """The README's one-sentence claim, rendered from the drift benchmark's `totals` and tool
    list so it can only say what `python benchmarks/drift/run.py` last measured. Every failure
    is a ValueError (a missing or unreadable results file, bad JSON, a totals shape the
    renderer does not understand), so `docs_sync` reports it as a check failure instead of the
    gate crashing."""
    p = root / BENCHMARK_RESULTS
    rel = BENCHMARK_RESULTS.as_posix()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except OSError as e:
        raise ValueError(f"benchmark-headline: cannot read {rel}: {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"benchmark-headline: {rel} is not valid JSON: {e}") from e
    def pair(value):
        # a [caught, seeded] list of two whole numbers; a dict or a string of length two also
        # unpacks into two names, so the shape is checked, not just the arity
        if (isinstance(value, (list, tuple)) and len(value) == 2
                and all(isinstance(n, int) and not isinstance(n, bool) for n in value)):
            return value
        raise ValueError(f"expected a [caught, seeded] pair, got {value!r}")

    try:
        totals = data["totals"]
        verify_caught, verify_seeded = pair(totals["verify"])
        git_caught, git_seeded = pair(totals["git"])
        none_caught, _none_seeded = pair(totals["none"])
        tool_count = len(data["tools"])
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(
            f"benchmark-headline: {rel} needs totals.verify, totals.git, totals.none "
            f"(each a [caught, seeded] pair) and a tools list: {e!r}") from e
    return (f"verify caught {verify_caught} of {verify_seeded} seeded drifts across "
            f"{tool_count} tools; plain git status caught {git_caught} of {git_seeded}; "
            f"copying by hand caught {none_caught}")


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
    raised directly here) on an unknown marker key, an unmatched marker pair, a doc missing one
    of its required markers, or a benchmark results file the headline renderer cannot read."""
    cat = load_catalog(root / "kit" / "catalog" / "catalog.json")
    renderers = {
        "skills-table": lambda: _render_skills_table(cat),
        "core-count-words": lambda: _render_core_count_words(cat),
        "core-count-digits": lambda: _render_core_count_digits(cat),
        "stage-counts": lambda: _render_stage_counts(cat),
        "checks-line": lambda: _render_checks_line(cat),
        # read lazily, so a root without the results file only fails on a doc that uses the key
        "benchmark-headline": lambda: _render_benchmark_headline(root),
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
