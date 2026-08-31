"""The ledgers check holds the three append-only records to their contract: decision records
indexed, numbered, and well-formed; debt entries dated with paths that still resolve; the roadmap
carrying its required sections. Pass on the real tree, fail on each seeded violation."""
import pathlib
import shutil

import pytest

from kit.checks import ledgers

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Same ignore set as test_check_negatives.py: untracked local content must not leak into the
# copied tree and trip the check's walk-fallback, which the real git-tracked scan never sees.
IGNORE = shutil.ignore_patterns(".git", ".claude", ".superpowers", "superpowers", "__pycache__",
                                ".pytest_cache", ".benchmarks", ".venv", "venv", "*.egg-info")


@pytest.fixture
def repo_copy(tmp_path):
    dst = tmp_path / "kit"
    shutil.copytree(ROOT, dst, ignore=IGNORE)
    return dst


def test_ledgers_passes_on_the_real_tree():
    ok, detail = ledgers.run(ROOT)
    assert ok, detail


def test_ledgers_passes_on_the_copy(repo_copy):
    # the copy has no .git, so this exercises the working-tree fallback for path resolution
    ok, detail = ledgers.run(repo_copy)
    assert ok, detail


def test_ledgers_catches_an_unindexed_record(repo_copy):
    # a record file on disk but absent from the README index list must fail, naming the number
    (repo_copy / "docs" / "decisions" / "0003-a-stray-choice.md").write_text(
        "# 0003: A stray choice\n\nStatus: Accepted\nDate: 2026-08-30\n\n## Context\n\nx\n",
        encoding="utf-8")
    ok, detail = ledgers.run(repo_copy)
    assert not ok and "0003" in detail and "index" in detail


def test_ledgers_catches_a_numbering_gap(repo_copy):
    # 0004 exists and is indexed, but 0003 does not: the sequence must stay contiguous from 0001
    (repo_copy / "docs" / "decisions" / "0004-a-skipped-number.md").write_text(
        "# 0004: A skipped number\n\nStatus: Accepted\nDate: 2026-08-30\n\n## Context\n\nx\n",
        encoding="utf-8")
    readme = repo_copy / "docs" / "decisions" / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "- 0004: a skipped number\n",
                      encoding="utf-8")
    ok, detail = ledgers.run(repo_copy)
    assert not ok and "0003" in detail


def test_ledgers_catches_a_bad_status_value(repo_copy):
    p = repo_copy / "docs" / "decisions" / "0002-installer-path-safety.md"
    text = p.read_text(encoding="utf-8").replace("Status: Accepted", "Status: Maybe")
    assert "Status: Maybe" in text  # guard: the substitution landed
    p.write_text(text, encoding="utf-8")
    ok, detail = ledgers.run(repo_copy)
    assert not ok and "Maybe" in detail


def test_ledgers_catches_a_dangling_supersede(repo_copy):
    # "Superseded by NNNN" must point at a record that exists
    p = repo_copy / "docs" / "decisions" / "0002-installer-path-safety.md"
    text = p.read_text(encoding="utf-8").replace("Status: Accepted", "Status: Superseded by 0009")
    assert "Superseded by 0009" in text  # guard: the substitution landed
    p.write_text(text, encoding="utf-8")
    ok, detail = ledgers.run(repo_copy)
    assert not ok and "0009" in detail


def test_ledgers_catches_an_open_entry_naming_a_deleted_file(repo_copy):
    # a closed or renamed file must not leave a stale Open entry silently
    p = repo_copy / "docs" / "DEBT.md"
    text = p.read_text(encoding="utf-8").replace(
        "## Open\n",
        "## Open\n\n- 2026-08-30: a shortcut in `kit/checks/ghost.py`. Close by removing it.\n",
        1)
    assert "ghost.py" in text  # guard: the seeded entry landed
    p.write_text(text, encoding="utf-8")
    ok, detail = ledgers.run(repo_copy)
    assert not ok and "ghost.py" in detail


def test_ledgers_tracked_mode_skips_an_untracked_decision_draft(repo_copy, monkeypatch):
    # a local draft on disk but absent from git's tracked set is scratch, not a record under
    # contract; the tracked-mode scan must not read it into the index checks
    tracked = [p.relative_to(repo_copy).as_posix()
               for p in repo_copy.rglob("*") if p.is_file()]
    monkeypatch.setattr(ledgers, "tracked_files", lambda root: tracked)
    (repo_copy / "docs" / "decisions" / "0003-wip-draft.md").write_text(
        "# 0003: A work-in-progress draft\n\nnot a record yet\n", encoding="utf-8")
    ok, detail = ledgers.run(repo_copy)
    assert ok, detail


def test_ledgers_tracked_mode_catches_an_open_entry_naming_an_untracked_path(
        repo_copy, monkeypatch):
    # tracked mode must test membership in the tracked set, not existence on disk: the file
    # is present in the working tree but git does not track it
    stray = repo_copy / "kit" / "checks" / "stray_local.py"
    stray.write_text("# local scratch\n", encoding="utf-8")
    tracked = [p.relative_to(repo_copy).as_posix()
               for p in repo_copy.rglob("*") if p.is_file() and p != stray]
    monkeypatch.setattr(ledgers, "tracked_files", lambda root: tracked)
    p = repo_copy / "docs" / "DEBT.md"
    text = p.read_text(encoding="utf-8").replace(
        "## Open\n",
        "## Open\n\n- 2026-08-30: a shortcut in `kit/checks/stray_local.py`. Close by removing it.\n",
        1)
    assert "stray_local.py" in text  # guard: the seeded entry landed
    p.write_text(text, encoding="utf-8")
    ok, detail = ledgers.run(repo_copy)
    assert not ok and "stray_local.py" in detail


def test_ledgers_catches_a_missing_closed_heading(repo_copy):
    p = repo_copy / "docs" / "DEBT.md"
    text = p.read_text(encoding="utf-8").replace("## Closed", "## Done")
    assert "## Closed" not in text  # guard: the heading is genuinely gone
    p.write_text(text, encoding="utf-8")
    ok, detail = ledgers.run(repo_copy)
    assert not ok and "Closed" in detail


def test_ledgers_catches_a_missing_roadmap_heading(repo_copy):
    p = repo_copy / "docs" / "ROADMAP.md"
    text = p.read_text(encoding="utf-8").replace("## Idea backlog", "## Ideas")
    assert "## Idea backlog" not in text  # guard: the heading is genuinely gone
    p.write_text(text, encoding="utf-8")
    ok, detail = ledgers.run(repo_copy)
    assert not ok and "Idea backlog" in detail
