#!/usr/bin/env python3
"""Sync GitHub labels from kit/labels/registry.json.

  python tools/sync_labels.py            # dry-run: print the plan, write nothing
  python tools/sync_labels.py --apply    # create and update labels via gh
  python tools/sync_labels.py --repo owner/name [--apply]

Never deletes or renames a label, on either path. A live label with no registry match (a
retained default, or anything else) is reported, not touched. Requires the `gh` CLI,
authenticated, for --apply and for the live-label read dry-run uses to show an accurate plan.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from kit.labels import load_labels

_REMOTE_RE = re.compile(r"github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$")


def infer_repo(root: pathlib.Path) -> str | None:
    try:
        proc = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"],
                              capture_output=True, text=True)
    except (OSError, FileNotFoundError):
        return None
    if proc.returncode != 0:
        return None
    m = _REMOTE_RE.search(proc.stdout.strip())
    return f"{m.group(1)}/{m.group(2)}" if m else None


def fetch_live_labels(repo: str) -> dict[str, dict]:
    """{name: {"color": ..., "description": ...}} for every label currently on `repo`."""
    proc = subprocess.run(
        ["gh", "label", "list", "--repo", repo, "--json", "name,color,description",
         "--limit", "300"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"gh label list failed: {proc.stderr.strip()}")
    rows = json.loads(proc.stdout)
    return {row["name"]: {"color": row["color"], "description": row.get("description") or ""}
            for row in rows}


def plan_sync(registry_labels: list[dict], live_labels: dict[str, dict]) -> dict:
    """Compute the sync plan. Never proposes a delete or a rename: a live label with no registry
    match lands in `untouched_existing` only."""
    to_create: list[dict] = []
    to_update: list[dict] = []
    unchanged: list[str] = []
    registry_names = {label["name"] for label in registry_labels}
    for label in registry_labels:
        live = live_labels.get(label["name"])
        if live is None:
            to_create.append(label)
        elif live["color"] != label["color"] or live["description"] != label["description"]:
            to_update.append(label)
        else:
            unchanged.append(label["name"])
    untouched_existing = sorted(set(live_labels) - registry_names)
    return {
        "to_create": to_create,
        "to_update": to_update,
        "unchanged": unchanged,
        "untouched_existing": untouched_existing,
    }


def _run_gh(args: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    return proc.returncode == 0, (proc.stderr or proc.stdout).strip()


def apply_plan(repo: str, plan: dict) -> list[tuple[str, bool, str]]:
    """Create and update labels via gh. Returns one (label, ok, detail) row per action; never
    calls `gh label delete` or renames anything."""
    results: list[tuple[str, bool, str]] = []
    for label in plan["to_create"]:
        ok, detail = _run_gh(["label", "create", label["name"], "--repo", repo,
                              "--color", label["color"], "--description", label["description"],
                              "--force"])
        results.append((label["name"], ok, detail or "created"))
    for label in plan["to_update"]:
        ok, detail = _run_gh(["label", "edit", label["name"], "--repo", repo,
                              "--color", label["color"], "--description", label["description"]])
        results.append((label["name"], ok, detail or "updated"))
    return results


def _print_plan(plan: dict) -> None:
    print(f"create ({len(plan['to_create'])}): "
          f"{', '.join(l['name'] for l in plan['to_create']) or 'none'}")
    print(f"update ({len(plan['to_update'])}): "
          f"{', '.join(l['name'] for l in plan['to_update']) or 'none'}")
    print(f"unchanged ({len(plan['unchanged'])}): {', '.join(plan['unchanged']) or 'none'}")
    print(f"untouched existing, no registry match, never deleted or renamed "
          f"({len(plan['untouched_existing'])}): "
          f"{', '.join(plan['untouched_existing']) or 'none'}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="owner/name; inferred from the origin remote by default")
    parser.add_argument("--apply", action="store_true", help="write to GitHub; default is dry-run")
    args = parser.parse_args(argv)

    root = pathlib.Path(__file__).resolve().parents[1]
    registry = load_labels(root / "kit" / "labels" / "registry.json")

    repo = args.repo or infer_repo(root)
    if not repo:
        print("cannot infer owner/name from the origin remote; pass --repo owner/name")
        return 2

    try:
        live = fetch_live_labels(repo)
    except RuntimeError as e:
        print(str(e))
        return 2

    plan = plan_sync(registry.labels, live)
    _print_plan(plan)

    if not args.apply:
        print("dry-run: nothing written. Re-run with --apply to create and update labels.")
        return 0

    results = apply_plan(repo, plan)
    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"[{'OK' if ok else 'FAIL'}] {name}: {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
