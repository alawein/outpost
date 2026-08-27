"""Run the checks in catalog order and report. The catalog's check list drives this, so adding a
check means adding it to the catalog and shipping the module. A check that cannot import is a
failure, not a silent skip.
"""
from __future__ import annotations

import importlib
import pathlib

from ..catalog import load_catalog

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def run_all(root: pathlib.Path) -> list[tuple[str, bool, str]]:
    try:
        cat = load_catalog(root / "kit" / "catalog" / "catalog.json")
    except ValueError as e:
        return [("catalog", False, str(e))]
    results: list[tuple[str, bool, str]] = []
    for entry in cat.checks:
        name = entry.get("name", "<unnamed>")
        try:
            module = importlib.import_module(entry["module"])
            ok, detail = module.run(root)
        except Exception as e:  # a check that errors (or a malformed entry) is a reported failure
            ok, detail = False, f"check raised {type(e).__name__}: {e}"
        results.append((name, ok, detail))
    return results


def main(root: pathlib.Path | None = None) -> int:
    root = root or REPO_ROOT
    results = run_all(root)
    print("outpost validate")
    print("-" * 48)
    failed = 0
    for name, ok, detail in results:
        failed += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    print("-" * 48)
    print(f"{len(results) - failed}/{len(results)} ok; {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
