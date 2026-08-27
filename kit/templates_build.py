"""Build the per-tool guide templates from one shared core plus a per-tool head.

`build_templates(root)` returns a dict mapping each committed template path to its content. The
caller writes the files; this function is pure, mirroring `kit.plugin.build_plugin`. The
`templates_sync` gate check proves the committed files match this output; run
`tools/build.py templates` after editing a source under `templates/_src/`.

One home for the shared core (`templates/_src/core.md`). The catalog is the home for the
tool-to-filename map, so adding a guide for a new tool is one catalog `templates` entry plus one
head file.
"""
from __future__ import annotations

import pathlib

from .catalog import load_catalog

_SRC = "templates/_src"


def _join(head: str, core: str) -> str:
    """The one definition of how a head and the core combine. The builder writes this and the
    check compares against it, so they cannot disagree."""
    return head.strip() + "\n\n" + core.strip() + "\n"


def build_templates(root: pathlib.Path) -> dict[str, str]:
    """Return {committed template path: content} for every catalog template. Reads the sources,
    writes nothing. Raises ValueError on a missing or unreadable source, so a broken build fails
    loudly with the file named."""
    cat = load_catalog(root / "kit" / "catalog" / "catalog.json")
    try:
        core = (root / _SRC / "core.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise ValueError(f"template core cannot be read: {e}") from e
    out: dict[str, str] = {}
    for entry in cat.templates:
        name = entry["name"]
        try:
            head = (root / _SRC / "head" / f"{name}.md").read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            raise ValueError(f"template head {name!r} cannot be read: {e}") from e
        out[entry["path"]] = _join(head, core)
    return out
