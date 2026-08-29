"""The catalog-derived spans inside README.md, docs/workflow.md, and docs/plugin.md stay in
sync with the catalog. `docs_build.build_docs` is the generator; this check proves every marked
span on disk equals what it would generate. Run `python tools/build.py docs` to regenerate after
a catalog change (a new core prompt, a stage rename, a domain-prompt count change) or a benchmark
rerun (the README headline is rendered from benchmarks/drift/results.json).
"""
from __future__ import annotations

import pathlib

from ..docs_build import build_docs


def run(root: pathlib.Path) -> tuple[bool, str]:
    try:
        drifted = build_docs(root)
    except ValueError as e:
        return False, str(e)

    if drifted:
        names = ", ".join(sorted(drifted))
        return False, f"generated spans drifted in: {names} (run python tools/build.py docs)"

    return True, "generated doc spans match the catalog"
