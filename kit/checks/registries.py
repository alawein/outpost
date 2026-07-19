"""The adapter and check registries match the code on disk. The `catalog` check covers the prompt
and template files; this widens that to the two code registries, both ways. A check module on disk
but not in the catalog would silently never run (the runner only runs catalog-listed checks); an
adapter package not registered would never install; and a catalog entry with no module would fail
late. This catches all three at the gate.
"""
from __future__ import annotations

import pathlib

from ..catalog import load_catalog

# kit/checks modules that are machinery, not checks: the package init and the runner.
NON_CHECK_MODULES = {"__init__", "run"}


def run(root: pathlib.Path) -> tuple[bool, str]:
    try:
        cat = load_catalog(root / "kit" / "catalog" / "catalog.json")
    except ValueError as e:
        return False, str(e)

    errors: list[str] = []

    # Adapters: a *.py module in kit/adapters, excluding the package init and base.py machinery.
    on_disk = {p.stem for p in (root / "kit" / "adapters").glob("*.py")
               if p.stem not in {"__init__", "base"}}
    listed = {a["tool"] for a in cat.adapters}
    errors += [f"adapter {t!r} is in the catalog but kit/adapters/{t}/ has no package"
               for t in sorted(listed - on_disk)]
    errors += [f"adapter package kit/adapters/{n}/ is on disk but not in the catalog"
               for n in sorted(on_disk - listed)]

    # Checks: every kit/checks/*.py that is not machinery must be registered, and vice versa.
    on_disk = {p.stem for p in (root / "kit" / "checks").glob("*.py") if p.stem not in NON_CHECK_MODULES}
    listed = {entry["module"].rsplit(".", 1)[-1] for entry in cat.checks}
    errors += [f"check {n!r} is in the catalog but kit/checks/{n}.py is missing"
               for n in sorted(listed - on_disk)]
    errors += [f"check module kit/checks/{n}.py is on disk but not in the catalog"
               for n in sorted(on_disk - listed)]

    if errors:
        return False, "; ".join(errors[:10])
    return True, f"{len(cat.adapters)} adapters and {len(cat.checks)} checks match the code on disk"
