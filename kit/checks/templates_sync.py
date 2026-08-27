"""The committed guide templates stay in sync with the build. Each templates/<file> must equal
the templates_build output (per-tool head plus the shared core); a hand-edit to a built file, or
an edit to a source without a rebuild, is drift. Run `python tools/build.py templates` to
regenerate.
"""
from __future__ import annotations

import pathlib

from . import compare_generated
from ..templates_build import build_templates


def run(root: pathlib.Path) -> tuple[bool, str]:
    try:
        generated = build_templates(root)
    except ValueError as e:
        return False, str(e)

    missing, drifted = compare_generated(root, generated)
    errors = [f"built template missing: {rel}" for rel in missing]
    errors += [f"template drift: {rel} does not match the build (run python tools/build.py templates)"
               for rel in drifted]
    if errors:
        return False, "; ".join(errors[:10])
    return True, f"{len(generated)} guide templates in sync with the shared core"
