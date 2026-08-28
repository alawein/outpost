"""The drift benchmark's pieces, on a two-tool subset (claude and gemini) so pytest stays fast:
the pristine project verifies in sync, every seed changes exactly what it reports, the detectors
read the real installer and git output, the table matches the row count, and the --check diff
names a flipped row."""
import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUN_PY = ROOT / "benchmarks" / "drift" / "run.py"
SUBSET = ("claude", "gemini")


def _load_runner():
    spec = importlib.util.spec_from_file_location("drift_run", RUN_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


run = _load_runner()


def _tree(root: pathlib.Path) -> dict:
    """Every file under root as {posix relative path: bytes}, minus the git store."""
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*"))
            if p.is_file() and ".git" not in p.relative_to(root).parts}


def _changed(before: dict, after: dict) -> set:
    return {k for k in set(before) | set(after) if before.get(k) != after.get(k)}


@pytest.fixture(scope="module")
def pristine(tmp_path_factory):
    return run.build_pristine(ROOT, tmp_path_factory.mktemp("drift"))


@pytest.fixture(scope="module")
def subset_results(tmp_path_factory):
    return run.run_all(ROOT, tmp_path_factory.mktemp("drift-all"), tools=SUBSET)


def _copy(pristine: pathlib.Path, tmp_path: pathlib.Path, name: str) -> pathlib.Path:
    dest = tmp_path / name
    run.copy_project(pristine, dest)
    return dest


def test_build_pristine_is_in_sync_and_committed(pristine):
    run.assert_pristine(ROOT, pristine)  # raises on verify drift or a dirty git status
    assert (pristine / ".git").is_dir()
    assert (pristine / ".outpost" / "manifest.json").is_file()


def test_prompt_and_guide_paths_come_from_the_plan(pristine):
    assert run.prompt_path("claude", ROOT, pristine, "plan-change") == \
        ".claude/skills/plan-change/SKILL.md"
    assert run.prompt_path("gemini", ROOT, pristine, "plan-change") == \
        ".gemini/commands/outpost/plan-change.toml"
    assert run.guide_path("claude", ROOT, pristine) == "CLAUDE.md"
    assert run.guide_path("gemini", ROOT, pristine) == "GEMINI.md"


@pytest.mark.parametrize("tool", SUBSET)
@pytest.mark.parametrize("scenario", list(run.SEEDS))
def test_each_seed_changes_only_what_it_reports(pristine, tmp_path, scenario, tool):
    before = _tree(pristine)
    copy = _copy(pristine, tmp_path, f"{scenario}-{tool}")
    paths = run.SEEDS[scenario](copy, tool, ROOT)
    assert _tree(pristine) == before, "the seed touched the pristine project"
    assert paths and len(set(paths)) == len(paths)
    changed = _changed(before, _tree(copy))
    if scenario == "orphan":
        # the narrowed re-install rewrites only the manifest; the orphans stay byte-identical
        assert changed == {".outpost/manifest.json"}
        assert all(_tree(copy)[p] == before[p] for p in paths)
        assert not any("plan-change" in p for p in paths)
        assert len(paths) > 1
    elif scenario == "source-ahead":
        # the change lives in a copy of the kit, never in the project
        assert changed == set()
        ahead = run.ahead_kit_dir(copy)
        edited = ahead / "prompts" / "core" / "plan-change.md"
        assert edited.read_bytes() != (ROOT / "prompts" / "core" / "plan-change.md").read_bytes()
        assert paths == [run.prompt_path(tool, ROOT, copy, "plan-change")]
    else:
        assert changed == set(paths)


@pytest.mark.parametrize("tool", SUBSET)
def test_detect_verify_catches_an_edited_copy(pristine, tmp_path, tool):
    copy = _copy(pristine, tmp_path, "edited")
    paths = run.SEEDS["edited-copy"](copy, tool, ROOT)
    caught, line = run.detect_verify(ROOT, copy, paths)
    assert caught
    assert line.split()[:2] == ["DRIFTED", paths[0]]


@pytest.mark.parametrize("tool", SUBSET)
def test_detect_verify_catches_an_edited_guide(pristine, tmp_path, tool):
    copy = _copy(pristine, tmp_path, "guide")
    paths = run.SEEDS["guide-edited"](copy, tool, ROOT)
    caught, line = run.detect_verify(ROOT, copy, paths)
    assert caught
    assert line.split()[:2] == ["EDITED", paths[0]]


@pytest.mark.parametrize("tool", SUBSET)
def test_detect_git_catches_an_edited_guide(pristine, tmp_path, tool):
    copy = _copy(pristine, tmp_path, "guide")
    paths = run.SEEDS["guide-edited"](copy, tool, ROOT)
    assert run.detect_git(copy, paths)


@pytest.mark.parametrize("tool", SUBSET)
def test_detect_git_misses_an_orphan(pristine, tmp_path, tool):
    copy = _copy(pristine, tmp_path, "orphan")
    paths = run.SEEDS["orphan"](copy, tool, ROOT)
    assert not run.detect_git(copy, paths)


def test_run_all_rows_are_in_plan_order(subset_results):
    rows = subset_results["rows"]
    assert len(rows) == len(run.SEEDS) * len(SUBSET)
    assert [(r["scenario"], r["tool"]) for r in rows] == \
        [(s, t) for s in run.SEEDS for t in SUBSET]
    assert all(r["none"] is False for r in rows)
    assert subset_results["totals"]["none"] == [0, len(rows)]
    assert subset_results["totals"]["verify"][1] == len(rows)


def test_render_table_has_one_line_per_row_plus_header_and_total(subset_results):
    lines = run.render_table(subset_results).splitlines()
    assert len(lines) == 2 + len(subset_results["rows"]) + 1
    assert lines[0].startswith("| scenario | tool | verify | git | none |")
    assert lines[-1].startswith("| total |")


def test_check_diff_names_a_flipped_row(subset_results):
    # the pure diff behind --check; the CI --check step covers main's exit code
    flipped = json.loads(json.dumps(subset_results))
    row = flipped["rows"][0]
    row["verify"] = not row["verify"]
    problems = run._diff_rows(flipped, subset_results)
    assert any(f"{row['scenario']} {row['tool']}" in p for p in problems)
    assert run._diff_rows(subset_results, subset_results) == []


def test_check_problems_treat_a_missing_file_as_a_failure(subset_results, tmp_path):
    # a check that points at a path with no file must not pass by skipping the comparison
    table = run.render_table(subset_results)
    results_path = tmp_path / "results.json"
    readme_path = tmp_path / "README.md"
    missing = run.check_problems(subset_results, table, results_path, readme_path)
    assert any("results.json is missing" in p for p in missing)
    assert any("README.md is missing" in p for p in missing)
    results_path.write_text(run._dumps(subset_results), encoding="utf-8")
    readme_path.write_text(f"intro\n{run.MARK_START}\nstale\n{run.MARK_END}\n", encoding="utf-8")
    stale = run.check_problems(subset_results, table, results_path, readme_path)
    assert stale == ["the table in README.md is stale; run with --write"]
    readme_path.write_text(f"intro\n{run.MARK_START}\n{table}\n{run.MARK_END}\n", encoding="utf-8")
    assert run.check_problems(subset_results, table, results_path, readme_path) == []


def test_rmtree_clears_a_read_only_git_store(pristine, tmp_path):
    copy = _copy(pristine, tmp_path, "gone")
    assert (copy / ".git").is_dir()
    run.rmtree(copy)
    assert not copy.exists()
