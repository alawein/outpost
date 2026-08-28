#!/usr/bin/env python3
"""The drift benchmark: seed one kind of drift into an installed project, then ask three
detectors whether they noticed. See README.md beside this file for what each row means.

    python benchmarks/drift/run.py            # run everything, print the table
    python benchmarks/drift/run.py --write    # also rewrite results.json and the README table
    python benchmarks/drift/run.py --check    # exit 1 if a fresh run differs from results.json

Honesty rule: before every seed the copy must verify in sync and have a clean git status, and
every seed proves it changed something, or the run aborts. A miss is a published row.

Stdlib only. Writes only under a temp dir (and, with --write, the two files beside this one).
Results carry no timestamps or machine paths, so they match across operating systems.
"""
from __future__ import annotations

import argparse
import atexit
import concurrent.futures
import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
KIT_ROOT = HERE.parents[1]
RESULTS_PATH = HERE / "results.json"
README_PATH = HERE / "README.md"
MARK_START = "<!-- RESULTS -->"
MARK_END = "<!-- /RESULTS -->"

if str(KIT_ROOT) not in sys.path:
    sys.path.insert(0, str(KIT_ROOT))

from kit import KIT_VERSION  # noqa: E402
from kit.adapters import TOOLS, plan_for  # noqa: E402

DETECTORS = ("verify", "git", "none")
EDIT_LINE = b"\nbenchmark seed: one appended line\n"
# the source-ahead seed copies only what the installer reads (install.py, kit/, prompts/,
# templates/); the one thing those four can hold that is not source is a bytecode cache
KIT_IGNORE = shutil.ignore_patterns("__pycache__")
KIT_SOURCE_DIRS = ("kit", "prompts", "templates")
GIT_CONFIG = (
    ("user.name", "outpost benchmark"),
    ("user.email", "benchmark@example.invalid"),
    ("core.autocrlf", "false"),
    ("commit.gpgsign", "false"),
)


class SeedError(RuntimeError):
    """A precondition of the honesty rule did not hold. The run aborts rather than publish."""


# ---- subprocess helpers ----------------------------------------------------------------------

_EMPTY_GITCONFIG: pathlib.Path | None = None


def _git_env() -> dict:
    """Run git against an empty global config, so a developer's autocrlf, hooks, or identity
    never shape a result. The empty config file lives for the process and is removed at exit."""
    global _EMPTY_GITCONFIG
    if _EMPTY_GITCONFIG is None:
        fd, name = tempfile.mkstemp(prefix="outpost-drift-", suffix=".gitconfig")
        os.close(fd)
        _EMPTY_GITCONFIG = pathlib.Path(name)
        atexit.register(lambda: _EMPTY_GITCONFIG.unlink(missing_ok=True))
    env = dict(os.environ)
    for key in ("GIT_CONFIG", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(key, None)
    env["GIT_CONFIG_GLOBAL"] = str(_EMPTY_GITCONFIG)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    return env


def _run(cmd: list, cwd: pathlib.Path, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                          errors="replace")


def git(project: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    out = _run(["git", "-C", str(project), *args], cwd=project, env=_git_env())
    if out.returncode != 0:
        raise SeedError(f"git {' '.join(args)} failed in {project.name}:\n{out.stdout}")
    return out


def install(kit_root: pathlib.Path, project: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    """Run `install.py` from `kit_root` against `project` with the given extra flags."""
    cmd = [sys.executable, str(kit_root / "install.py"), "--project", str(project), *args]
    return _run(cmd, cwd=kit_root)


def verify_output(kit_root: pathlib.Path, project: pathlib.Path) -> tuple[int, str]:
    out = install(kit_root, project, "--tool", "all", "--verify")
    return out.returncode, out.stdout


def rmtree(path: pathlib.Path) -> None:
    """Remove a tree that may hold a read-only git store (Windows refuses to delete those)."""
    path = pathlib.Path(path)
    if not path.exists():
        return
    for root, dirs, files in os.walk(path):
        for name in dirs:
            os.chmod(os.path.join(root, name), stat.S_IRWXU)
        for name in files:
            os.chmod(os.path.join(root, name), stat.S_IRUSR | stat.S_IWUSR)
    shutil.rmtree(path, ignore_errors=True)
    if path.exists():
        print(f"warning: could not remove {path}", file=sys.stderr)


# ---- the pristine project ---------------------------------------------------------------------

def build_pristine(kit_root: pathlib.Path, workdir: pathlib.Path) -> pathlib.Path:
    """Install every tool into a fresh scratch project and commit it. The commit is the git
    detector's baseline; the in-sync verify is the installer's."""
    project = pathlib.Path(workdir) / "pristine"
    project.mkdir(parents=True)
    out = install(kit_root, project, "--tool", "all")
    if out.returncode != 0:
        raise SeedError(f"install --tool all failed:\n{out.stdout}")
    git(project, "-c", "init.defaultBranch=main", "init", "-q")
    for key, value in GIT_CONFIG:
        git(project, "config", key, value)
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "baseline")
    assert_pristine(kit_root, project)
    return project


def assert_pristine(kit_root: pathlib.Path, project: pathlib.Path) -> None:
    """The honesty gate: verify exits 0 and git status is empty, or the run aborts."""
    rc, text = verify_output(kit_root, project)
    if rc != 0:
        raise SeedError(f"{project.name} is not in sync before the seed (verify exit {rc}):\n{text}")
    status = git(project, "status", "--porcelain", "--untracked-files=all").stdout
    if status.strip():
        raise SeedError(f"{project.name} has a dirty git status before the seed:\n{status}")


def copy_project(pristine: pathlib.Path, dest: pathlib.Path) -> pathlib.Path:
    shutil.copytree(pristine, dest)  # the .git store comes along, so git status works
    return dest


def ahead_kit_dir(project: pathlib.Path) -> pathlib.Path:
    """Where the source-ahead seed puts its edited copy of the kit: beside the project copy."""
    return project.parent / f"{project.name}-kit"


# ---- paths derived from the adapters ----------------------------------------------------------

def _stem(component: str) -> str:
    """A path component reduced to a prompt name: drop an `outpost-` prefix and any extension."""
    if component.startswith("outpost-"):
        component = component[len("outpost-"):]
    return component.split(".", 1)[0]


def prompt_path(tool: str, kit_root: pathlib.Path, project: pathlib.Path, name: str) -> str:
    """The tool's installed copy of prompt `name`: the write-mode action whose file stem, or
    whose parent directory (a Claude skill lives at `<name>/SKILL.md`), is the prompt name."""
    hits = []
    for a in plan_for(tool, kit_root, project):
        if a.mode != "write":
            continue
        parts = a.path.split("/")
        if _stem(parts[-1]) == name or (len(parts) > 1 and _stem(parts[-2]) == name):
            hits.append(a.path)
    if len(hits) != 1:
        raise SeedError(f"{tool}: expected one installed path for {name!r}, found {hits}")
    return hits[0]


def guide_path(tool: str, kit_root: pathlib.Path, project: pathlib.Path) -> str:
    """The tool's guide: its one create-mode action."""
    hits = [a.path for a in plan_for(tool, kit_root, project) if a.mode == "create"]
    if len(hits) != 1:
        raise SeedError(f"{tool}: expected one create-mode guide, found {hits}")
    return hits[0]


# ---- seeds ------------------------------------------------------------------------------------
# Each takes (project, tool, kit_root), changes the project (or a copy of the kit), proves the
# change took, and returns the paths a detector should name.

def _append(path: pathlib.Path) -> None:
    before = path.read_bytes()
    with path.open("ab") as fh:
        fh.write(EDIT_LINE)
    if path.read_bytes() == before:
        raise SeedError(f"appending to {path} changed nothing")


def seed_edited_copy(project: pathlib.Path, tool: str, kit_root: pathlib.Path) -> list:
    rel = prompt_path(tool, kit_root, project, "plan-change")
    _append(project / rel)
    return [rel]


def seed_deleted_copy(project: pathlib.Path, tool: str, kit_root: pathlib.Path) -> list:
    rel = prompt_path(tool, kit_root, project, "write-tests")
    target = project / rel
    target.unlink()
    if target.exists():
        raise SeedError(f"could not delete {rel}")
    return [rel]


def seed_source_ahead(project: pathlib.Path, tool: str, kit_root: pathlib.Path) -> list:
    """The kit moved on and the project did not: a copy of the kit gets one more line in the
    core `plan-change`, and verify later runs from that copy. The project itself is untouched."""
    ahead = ahead_kit_dir(project)
    if not ahead.is_dir():
        ahead.mkdir()
        shutil.copy2(kit_root / "install.py", ahead / "install.py")
        for d in KIT_SOURCE_DIRS:
            shutil.copytree(kit_root / d, ahead / d, ignore=KIT_IGNORE)
        _append(ahead / "prompts" / "core" / "plan-change.md")
    source = (kit_root / "prompts" / "core" / "plan-change.md").read_bytes()
    if (ahead / "prompts" / "core" / "plan-change.md").read_bytes() == source:
        raise SeedError("the ahead kit's plan-change matches the real kit")
    return [prompt_path(tool, kit_root, project, "plan-change")]


def seed_orphan(project: pathlib.Path, tool: str, kit_root: pathlib.Path) -> list:
    """Narrow the tool to one prompt without pruning. The de-selected prompt files stay on disk,
    byte-identical, and only the manifest changes. That manifest change is committed as the
    user's own action, so the git detector faces a clean tree and its miss is genuine."""
    full = [a.path for a in plan_for(tool, kit_root, project) if a.mode == "write"]
    keep = {a.path for a in plan_for(tool, kit_root, project, select={"plan-change"})
            if a.mode == "write"}
    orphans = [p for p in full if p not in keep]
    manifest = project / ".outpost" / "manifest.json"
    before = manifest.read_bytes()
    out = install(kit_root, project, "--tool", tool, "--only", "plan-change")
    if out.returncode != 0:
        raise SeedError(f"narrowed install failed for {tool}:\n{out.stdout}")
    if manifest.read_bytes() == before:
        raise SeedError(f"narrowed install left the manifest unchanged for {tool}")
    missing = [p for p in orphans if not (project / p).is_file()]
    if missing or not orphans:
        raise SeedError(f"orphan seed for {tool}: expected leftovers on disk, missing {missing}")
    git(project, "commit", "-q", "-am", "narrow to plan-change")
    return orphans


def seed_guide_edited(project: pathlib.Path, tool: str, kit_root: pathlib.Path) -> list:
    rel = guide_path(tool, kit_root, project)
    _append(project / rel)
    return [rel]


SEEDS = {
    "edited-copy": seed_edited_copy,
    "deleted-copy": seed_deleted_copy,
    "source-ahead": seed_source_ahead,
    "orphan": seed_orphan,
    "guide-edited": seed_guide_edited,
}


# ---- detectors --------------------------------------------------------------------------------

def detect_verify(kit_root: pathlib.Path, project: pathlib.Path, paths: list) -> tuple[bool, str]:
    """Run `--verify` from `kit_root` and read its report. Caught when a line names one of
    `paths` with a status token other than `ok`. Returns that line (whitespace collapsed), or
    the first `ok` line naming a seeded path on a miss. A healthy report names every seeded
    path (ok, MISSING, DRIFTED, EXTRA, or EDITED), so a report naming none means verify did not run
    (a corrupt manifest, a plan error) and the run aborts rather than publish a miss."""
    wanted = set(paths)
    seen = ""
    _, text = verify_output(kit_root, project)
    for raw in text.splitlines():
        tokens = raw.split()
        if len(tokens) < 2 or tokens[1] not in wanted:
            continue
        line = " ".join(tokens)
        if tokens[0] != "ok":
            return True, line
        if not seen:
            seen = line
    if not seen:
        raise SeedError(f"verify never named any of {sorted(wanted)}:\n{text}")
    return False, seen


def detect_git(project: pathlib.Path, paths: list) -> bool:
    """Caught when `git status --porcelain` names one of `paths`."""
    wanted = set(paths)
    out = git(project, "status", "--porcelain", "--untracked-files=all").stdout
    for raw in out.splitlines():
        if len(raw) < 4:
            continue
        entry = raw[3:]
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        if entry.strip('"') in wanted:
            return True
    return False


# ---- the run ----------------------------------------------------------------------------------

def run_row(kit_root: pathlib.Path, pristine: pathlib.Path, workdir: pathlib.Path,
            scenario: str, tool: str) -> dict:
    """One (scenario, tool) pair: copy the pristine project, gate it, seed it, ask each detector.
    Everything lives under its own directory, so rows can run side by side."""
    copy = copy_project(pristine, workdir / f"{scenario}-{tool}")
    assert_pristine(kit_root, copy)
    paths = SEEDS[scenario](copy, tool, kit_root)
    ahead = ahead_kit_dir(copy)
    verify_root = ahead if ahead.is_dir() else kit_root
    verify_caught, line = detect_verify(verify_root, copy, paths)
    return {
        "scenario": scenario,
        "tool": tool,
        "paths": paths,
        "verify": verify_caught,
        "verify_line": line,
        "git": detect_git(copy, paths),
        "none": False,
    }


def run_all(kit_root: pathlib.Path, workdir: pathlib.Path, tools=TOOLS, jobs: int = 4) -> dict:
    """Every scenario for every tool, rows in plan order (scenarios, then tools). Rows are
    independent and mostly wait on subprocesses and file copies, so a few run at once; the
    result order does not depend on which finished first."""
    kit_root = pathlib.Path(kit_root)
    workdir = pathlib.Path(workdir)
    pristine = build_pristine(kit_root, workdir)
    pairs = [(scenario, tool) for scenario in SEEDS for tool in tools]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        futures = [pool.submit(run_row, kit_root, pristine, workdir, *st) for st in pairs]
        try:
            rows = [f.result() for f in futures]
        except BaseException:
            # abort now: drop the queued rows instead of running them all before the error shows
            pool.shutdown(cancel_futures=True)
            raise
    totals = {d: [sum(1 for r in rows if r[d]), len(rows)] for d in DETECTORS}
    return {
        "kit_version": KIT_VERSION,
        "tools": list(tools),
        "scenarios": list(SEEDS),
        "rows": rows,
        "totals": totals,
    }


def totals_line(results: dict) -> str:
    t = results["totals"]
    return "totals: " + ", ".join(f"{d} {t[d][0]}/{t[d][1]}" for d in DETECTORS)


def render_table(results: dict) -> str:
    lines = ["| scenario | tool | verify | git | none |", "|---|---|---|---|---|"]
    for r in results["rows"]:
        cells = ["caught" if r[d] else "miss" for d in DETECTORS]
        lines.append(f"| {r['scenario']} | {r['tool']} | " + " | ".join(cells) + " |")
    t = results["totals"]
    lines.append("| total | | " + " | ".join(f"{t[d][0]}/{t[d][1]}" for d in DETECTORS) + " |")
    return "\n".join(lines)


def _dumps(results: dict) -> str:
    return json.dumps(results, indent=2, sort_keys=False) + "\n"


def _replace_block(text: str, table: str) -> str:
    start = text.index(MARK_START) + len(MARK_START)
    end = text.index(MARK_END)
    return text[:start] + "\n" + table + "\n" + text[end:]


def _readme_block(text: str) -> str:
    start = text.index(MARK_START) + len(MARK_START)
    end = text.index(MARK_END)
    return text[start:end].strip()


def _diff_rows(stored: dict, fresh: dict) -> list:
    """Human lines for every difference between a stored result and a fresh one."""
    out = []
    for key in ("kit_version", "tools", "scenarios"):
        if stored.get(key) != fresh[key]:
            out.append(f"{key}: stored {stored.get(key)!r}, fresh {fresh[key]!r}")
    by_key = {(r["scenario"], r["tool"]): r for r in stored.get("rows", [])}
    for r in fresh["rows"]:
        old = by_key.pop((r["scenario"], r["tool"]), None)
        if old is None:
            out.append(f"{r['scenario']} {r['tool']}: not in results.json")
        elif old != r:
            fields = sorted(k for k in set(old) | set(r) if old.get(k) != r.get(k))
            out.append(f"{r['scenario']} {r['tool']}: differs in {', '.join(fields)} "
                       f"(stored {[old.get(k) for k in fields]!r}, "
                       f"fresh {[r.get(k) for k in fields]!r})")
    for scenario, tool in by_key:
        out.append(f"{scenario} {tool}: in results.json but not in the fresh run")
    if stored.get("totals") != fresh["totals"]:
        out.append(f"totals: stored {stored.get('totals')!r}, fresh {fresh['totals']!r}")
    return out


def check_problems(results: dict, table: str, results_path: pathlib.Path,
                   readme_path: pathlib.Path) -> list:
    """Everything --check would complain about: a missing or differing results file, and a
    missing or stale README table. A missing file is a problem, never a pass, so a check can
    not go green by pointing at a path that does not exist."""
    problems = []
    if not results_path.is_file():
        problems.append(f"{results_path.name} is missing; run with --write")
    else:
        stored = json.loads(results_path.read_text(encoding="utf-8"))
        problems.extend(_diff_rows(stored, results))
    if not readme_path.is_file():
        problems.append(f"{readme_path.name} is missing; run with --write")
    elif _readme_block(readme_path.read_text(encoding="utf-8")) != table:
        problems.append(f"the table in {readme_path.name} is stale; run with --write")
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the drift benchmark.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true",
                      help="rewrite results.json and the README table from this run")
    mode.add_argument("--check", action="store_true",
                      help="exit 1 if this run differs from results.json or the README table")
    parser.add_argument("--tools", default=",".join(TOOLS),
                        help="comma-separated tool subset (default: every adapter)")
    parser.add_argument("--jobs", type=int, default=4,
                        help="rows to run side by side (default: 4)")
    parser.add_argument("--results", default=str(RESULTS_PATH), help=argparse.SUPPRESS)
    parser.add_argument("--readme", default=str(README_PATH), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    tools = tuple(t.strip() for t in args.tools.split(",") if t.strip())
    unknown = [t for t in tools if t not in TOOLS]
    if unknown:
        print(f"error: unknown tool(s) {unknown}; choose from {list(TOOLS)}", file=sys.stderr)
        return 2
    if args.write and tools != TOOLS:
        parser.error("--write publishes every adapter; drop --tools")
    workdir = pathlib.Path(tempfile.mkdtemp(prefix="outpost-drift-"))
    try:
        results = run_all(KIT_ROOT, workdir, tools=tools, jobs=args.jobs)
    except SeedError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    finally:
        rmtree(workdir)

    table = render_table(results)
    print(table)
    print(totals_line(results))
    results_path = pathlib.Path(args.results)
    readme_path = pathlib.Path(args.readme)

    if args.write:
        results_path.write_bytes(_dumps(results).encode("utf-8"))
        readme = readme_path.read_text(encoding="utf-8")
        readme_path.write_bytes(_replace_block(readme, table).encode("utf-8"))
        print(f"wrote {results_path.name} and the table in {readme_path.name}")
        return 0

    if args.check:
        problems = check_problems(results, table, results_path, readme_path)
        if problems:
            print("check failed:")
            for p in problems:
                print(f"  {p}")
            return 1
        print("check passed: results match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
