#!/usr/bin/env python3
"""Write generated files to disk from the catalog and sources. One target per builder:

  python tools/build.py plugin      # the Claude plugin tree (plugin_sync guards it)
  python tools/build.py docs        # the catalog-derived doc spans (docs_sync guards it)
  python tools/build.py templates   # the guide templates (templates_sync guards it)
  python tools/build.py all         # all three (the default)

Run the matching target whenever a catalog, prompt, or template source changes; the *_sync gate
check proves the committed tree matches the builder output.
"""
from __future__ import annotations
import pathlib
import sys

# Allow `python tools/build.py` from the repo root: put the repo root on sys.path, since running a
# script adds its own directory, not the repo root.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from kit.docs_build import build_docs
from kit.plugin import build_plugin
from kit.templates_build import build_templates

BUILDERS = {"plugin": build_plugin, "docs": build_docs, "templates": build_templates}


def _write(root: pathlib.Path, builder) -> None:
    for rel, content in builder(root).items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        # write bytes with the in-memory LF, so the build is byte-identical on every platform
        # (write_text would translate to CRLF on Windows; the newline= param is 3.10+, floor is 3.9)
        p.write_bytes(content.encode("utf-8"))


def main(argv: list[str]) -> int:
    targets = argv or ["all"]
    if targets == ["all"]:
        targets = list(BUILDERS)
    unknown = [t for t in targets if t not in BUILDERS]
    if unknown:
        print(f"unknown target(s): {', '.join(unknown)}; choose from {', '.join(BUILDERS)}, all")
        return 2
    root = pathlib.Path(__file__).resolve().parents[1]
    for name in targets:
        _write(root, BUILDERS[name])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
