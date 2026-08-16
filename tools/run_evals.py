#!/usr/bin/env python3
"""Run a lightweight behavioral eval per pilot prompt: copy its fixture, install the one prompt
under test, run a real `claude -p` call against the seeded task, diff the filesystem, and check
the transcript against tools/eval_assertions.py's mechanical assertions.

  python tools/run_evals.py                          # run every eval under evals/
  python tools/run_evals.py --only interrogate,debt-log
  python tools/run_evals.py --timeout 180
  python tools/run_evals.py --keep-temp              # do not delete temp dirs (debugging)

Opt-in only: never wired into validate.py or CI. Requires the `claude` CLI installed and
authenticated. Exit codes: 0 all evals passed, 1 at least one eval failed or no evals found,
2 the `claude` CLI is not on PATH (checked once, up front, before any eval runs).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from eval_assertions import evaluate_all  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVALS_DIR = ROOT / "evals"
_SKIP_DIRS = {".git"}


def hash_tree(root: pathlib.Path) -> dict[str, str]:
    """{relative posix path: sha256 hex digest} for every file under root. Skips .git."""
    hashes: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if _SKIP_DIRS & set(path.relative_to(root).parts):
            continue
        rel = path.relative_to(root).as_posix()
        hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def parse_stream_json(stdout: str) -> dict:
    """Reconstruct the {"result": str, "tool_calls": [{"name": str}, ...]} shape
    tools/eval_assertions.py expects, from claude -p --output-format stream-json --verbose's
    JSONL stdout. Ignores lines that aren't valid JSON or aren't a recognized event type. If no
    "result"-type line is found, "result" is "" (the caller treats an empty transcript with no
    tool_calls as a real, if uninformative, result — the JSON-parse-failure path is for when
    stdout doesn't parse as JSONL at all, not for this case)."""
    tool_calls = []
    result_text = ""
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "assistant":
            for block in (obj.get("message", {}) or {}).get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_calls.append({"name": block.get("name")})
        elif obj.get("type") == "result":
            result_text = obj.get("result") or ""
    return {"result": result_text, "tool_calls": tool_calls}


def discover_evals(evals_dir: pathlib.Path) -> list[str]:
    """Sorted names of every immediate subdirectory of evals_dir containing a task.txt."""
    if not evals_dir.is_dir():
        return []
    return sorted(
        p.name for p in evals_dir.iterdir() if p.is_dir() and (p / "task.txt").is_file()
    )


def run_one_eval(name: str, evals_dir: pathlib.Path, repo_root: pathlib.Path, timeout: int) -> dict:
    """Returns a dict carrying "tmp_dir" (str) once the temp dir has been created, so the caller
    can clean it up or, with --keep-temp, leave it for inspection regardless of how this eval
    turned out. A failure reading task.txt/assertions.json happens before the temp dir exists, so
    that one error dict omits "tmp_dir" — there is nothing to clean up."""
    eval_dir = evals_dir / name
    try:
        task_text = (eval_dir / "task.txt").read_text(encoding="utf-8")
        assertions = json.loads((eval_dir / "assertions.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return {"name": name, "status": "error", "results": None,
                "detail": f"could not read task.txt/assertions.json: {exc}"}
    fixture_dir = eval_dir / "fixture"

    tmp = pathlib.Path(tempfile.mkdtemp(prefix=f"outpost-eval-{name}-"))

    try:
        shutil.copytree(fixture_dir, tmp, dirs_exist_ok=True)
    except (FileNotFoundError, OSError) as exc:
        return {"name": name, "status": "error", "results": None,
                "detail": f"could not copy fixture: {exc}", "tmp_dir": str(tmp)}

    try:
        install = subprocess.run(
            [sys.executable, str(repo_root / "install.py"), "--tool", "claude",
             "--project", str(tmp), "--only", name],
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return {"name": name, "status": "error", "results": None,
                "detail": "install.py timed out after 60s", "tmp_dir": str(tmp)}

    if install.returncode != 0:
        return {"name": name, "status": "error", "results": None,
                "detail": f"install.py failed: {install.stderr.strip()}", "tmp_dir": str(tmp)}

    before = hash_tree(tmp)

    try:
        proc = subprocess.run(
            ["claude", "-p", task_text, "--output-format", "stream-json", "--verbose",
             "--permission-mode", "acceptEdits"],
            cwd=str(tmp), capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"name": name, "status": "error", "results": None,
                "detail": f"claude -p timed out after {timeout}s", "tmp_dir": str(tmp)}

    after = hash_tree(tmp)

    if proc.returncode != 0:
        detail = (f"claude -p failed (exit {proc.returncode}). "
                  f"stdout: {proc.stdout[:500]!r} stderr: {proc.stderr[:500]!r}")
        return {"name": name, "status": "error", "results": None, "detail": detail,
                "tmp_dir": str(tmp)}

    transcript = parse_stream_json(proc.stdout)

    try:
        results = evaluate_all(assertions, transcript, before, after)
    except Exception as exc:
        return {"name": name, "status": "error", "results": None,
                "detail": f"evaluate_all raised: {exc}", "tmp_dir": str(tmp)}
    status = "pass" if all(passed for _, passed, _ in results) else "fail"
    return {"name": name, "status": status, "results": results, "detail": None,
            "tmp_dir": str(tmp)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--only", help="comma-separated eval names to run (default: all)")
    parser.add_argument("--timeout", type=int, default=120,
                        help="per-eval claude -p timeout in seconds (default: 120)")
    parser.add_argument("--keep-temp", action="store_true",
                        help="do not delete the temp directory for each eval")
    args = parser.parse_args(argv)

    if shutil.which("claude") is None:
        print("error: the `claude` CLI is not on PATH. Install and authenticate Claude Code, "
              "then re-run.", file=sys.stderr)
        return 2

    names = discover_evals(EVALS_DIR)
    if args.only:
        wanted = [n.strip() for n in args.only.split(",")]
        available = names
        unknown = [n for n in wanted if n not in available]
        if unknown:
            print(
                f"error: --only named unknown eval(s): {', '.join(unknown)} "
                f"(available: {', '.join(available)})",
                file=sys.stderr,
            )
            return 1
        names = [n for n in available if n in wanted]

    if not names:
        print("no evals found under evals/", file=sys.stderr)
        return 1

    evals_passed = 0
    for name in names:
        print(f"running {name} ...")
        outcome = run_one_eval(name, EVALS_DIR, ROOT, args.timeout)
        try:
            if outcome["status"] == "error":
                print(f"  ERROR {name}: {outcome['detail']}")
                continue
            for assertion, passed, reason in outcome["results"]:
                mark = "ok  " if passed else "FAIL"
                print(f"  {mark} {assertion['type']}: {reason}")
            n_pass = sum(1 for _, passed, _ in outcome["results"] if passed)
            n_total = len(outcome["results"])
            print(f"{outcome['status'].upper()} {name} ({n_pass}/{n_total} assertions passed)")
            if outcome["status"] == "pass":
                evals_passed += 1
        finally:
            tmp_dir = outcome.get("tmp_dir")
            if tmp_dir:
                if args.keep_temp:
                    print(f"  kept: {tmp_dir}")
                else:
                    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n{evals_passed}/{len(names)} evals passed")
    return 0 if evals_passed == len(names) else 1


if __name__ == "__main__":
    sys.exit(main())
