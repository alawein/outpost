"""The catalog matches what is on disk, both ways. A prompt or template added to disk but not the
catalog, or listed but missing, is drift. The catalog version agrees with the package
(`KIT_VERSION`), `pyproject.toml`, and the latest released CHANGELOG entry.
"""
from __future__ import annotations

import pathlib
import re

from .. import KIT_VERSION
from ..catalog import load_catalog


def _on_disk(root: pathlib.Path, subdir: str) -> set[str]:
    d = root / subdir
    if not d.is_dir():
        return set()
    return {p.relative_to(root).as_posix() for p in d.glob("*.md") if p.name != "README.md"}


def run(root: pathlib.Path) -> tuple[bool, str]:
    try:
        cat = load_catalog(root / "kit" / "catalog" / "catalog.json")
    except ValueError as e:
        return False, str(e)

    errors: list[str] = []

    listed = cat.prompt_paths
    # Scan prompts/core. Scanning the on-disk dir (not just catalog-declared names)
    # catches a stray file the catalog has not yet registered.
    disk = _on_disk(root, "prompts/core")
    for missing in sorted(listed - disk):
        errors.append(f"catalog lists prompt {missing!r} but it is not on disk")
    for unlisted in sorted(disk - listed):
        errors.append(f"prompt {unlisted!r} is on disk but not in the catalog")

    t_listed = cat.template_paths
    t_dir = root / "templates"
    t_disk = {p.relative_to(root).as_posix()
              for p in t_dir.glob("*") if p.is_file() and p.name != "README.md"} if t_dir.is_dir() else set()
    for missing in sorted(t_listed - t_disk):
        errors.append(f"catalog lists template {missing!r} but it is not on disk")
    for unlisted in sorted(t_disk - t_listed):
        errors.append(f"template {unlisted!r} is on disk but not in the catalog")

    if not cat.adapters:
        errors.append("catalog lists no adapters")
    if not cat.checks:
        errors.append("catalog lists no checks")

    if cat.version != KIT_VERSION:
        errors.append(f"version drift: catalog {cat.version!r} != package KIT_VERSION {KIT_VERSION!r}")

    pj = root / "pyproject.toml"
    if pj.is_file():
        m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pj.read_text(encoding="utf-8"))
        if not m:
            errors.append("pyproject.toml has no version field")
        elif m.group(1) != cat.version:
            errors.append(f"version drift: catalog {cat.version!r} != pyproject {m.group(1)!r}")

    cl = root / "CHANGELOG.md"
    if cl.is_file():
        released = re.findall(r"(?m)^##\s*\[(\d+\.\d+\.\d+[^\]]*)\]", cl.read_text(encoding="utf-8"))
        if released and released[0] != cat.version:
            errors.append(f"version drift: catalog {cat.version!r} != latest CHANGELOG [{released[0]}]")

    if errors:
        return False, "; ".join(errors[:10])
    return True, f"catalog v{cat.version}: {len(cat.prompts)} prompts, {len(cat.templates)} templates, in sync"
