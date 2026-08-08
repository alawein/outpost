"""tools/run_evals.py's filesystem-hashing, eval-discovery, and stream-json-parsing helpers are
pure and testable without a live claude call. The actual subprocess orchestration (run_one_eval's
claude -p call) is exercised only by python tools/run_evals.py itself, run by hand or in the
dogfood record, not by pytest -q, which stays fast, free, and deterministic."""
import hashlib
import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_evals  # noqa: E402
from run_evals import discover_evals, hash_tree, parse_stream_json  # noqa: E402


def test_hash_tree_hashes_every_file_under_root():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / "a.txt").write_text("hello")
        (root / "sub").mkdir()
        (root / "sub" / "b.txt").write_text("world")
        hashes = hash_tree(root)
        assert set(hashes) == {"a.txt", "sub/b.txt"}
        assert hashes["a.txt"] == hashlib.sha256(b"hello").hexdigest()
        assert hashes["sub/b.txt"] == hashlib.sha256(b"world").hexdigest()


def test_hash_tree_returns_empty_dict_for_empty_dir():
    with tempfile.TemporaryDirectory() as tmp:
        assert hash_tree(pathlib.Path(tmp)) == {}


def test_hash_tree_skips_dot_git_directory():
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / ".git").mkdir()
        (root / ".git" / "HEAD").write_text("ref: refs/heads/main")
        (root / "app.py").write_text("code")
        hashes = hash_tree(root)
        assert set(hashes) == {"app.py"}


def test_discover_evals_finds_every_subdir_with_a_task_md():
    with tempfile.TemporaryDirectory() as tmp:
        evals_dir = pathlib.Path(tmp)
        (evals_dir / "alpha").mkdir()
        (evals_dir / "alpha" / "task.md").write_text("do alpha")
        (evals_dir / "beta").mkdir()
        (evals_dir / "beta" / "task.md").write_text("do beta")
        (evals_dir / "not_an_eval").mkdir()  # no task.md, must be excluded
        assert discover_evals(evals_dir) == ["alpha", "beta"]


def test_discover_evals_returns_empty_list_for_empty_dir():
    with tempfile.TemporaryDirectory() as tmp:
        assert discover_evals(pathlib.Path(tmp)) == []


def test_run_one_eval_handles_missing_fixture():
    """run_one_eval catches FileNotFoundError from missing fixture/ and returns error dict."""
    with tempfile.TemporaryDirectory() as evals_tmp, \
         tempfile.TemporaryDirectory() as repo_tmp:
        evals_dir = pathlib.Path(evals_tmp)
        repo_root = pathlib.Path(repo_tmp)

        # Set up an eval with task.md and assertions.json but no fixture/ directory
        eval_dir = evals_dir / "broken_eval"
        eval_dir.mkdir()
        (eval_dir / "task.md").write_text("some task")
        (eval_dir / "assertions.json").write_text("[]")
        # Note: no fixture/ directory created

        # run_one_eval should catch the missing fixture and return an error dict
        # (it won't actually run install.py or claude -p)
        from run_evals import run_one_eval
        outcome = run_one_eval("broken_eval", evals_dir, repo_root, timeout=120)

        # Verify it's an error return with tmp_dir present
        assert outcome["status"] == "error"
        assert outcome["results"] is None
        assert "could not copy fixture" in outcome["detail"]
        assert outcome["tmp_dir"]  # Must be present for cleanup

        # Verify the temp directory exists (was created before the error)
        assert pathlib.Path(outcome["tmp_dir"]).exists()


def test_parse_stream_json_single_tool_use():
    stdout = "\n".join([
        json.dumps({"type": "system", "subtype": "init"}),
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "text", "text": "Reading the file."},
            {"type": "tool_use", "name": "Read", "input": {"file_path": "a.py"}},
        ]}}),
        json.dumps({"type": "result", "result": "Done reading."}),
    ])
    assert parse_stream_json(stdout) == {
        "result": "Done reading.", "tool_calls": [{"name": "Read"}],
    }


def test_parse_stream_json_no_tool_use():
    stdout = "\n".join([
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "text", "text": "No tools needed."},
        ]}}),
        json.dumps({"type": "result", "result": "All good, no edits made."}),
    ])
    assert parse_stream_json(stdout) == {
        "result": "All good, no edits made.", "tool_calls": [],
    }


def test_parse_stream_json_multiple_assistant_lines_each_contribute_tool_use():
    stdout = "\n".join([
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {}},
        ]}}),
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Edit", "input": {}},
            {"type": "tool_use", "name": "Grep", "input": {}},
        ]}}),
        json.dumps({"type": "result", "result": "Made the edit."}),
    ])
    parsed = parse_stream_json(stdout)
    assert parsed["tool_calls"] == [{"name": "Read"}, {"name": "Edit"}, {"name": "Grep"}]
    assert parsed["result"] == "Made the edit."


def test_parse_stream_json_skips_unparseable_and_blank_lines():
    stdout = "\n".join([
        "",
        "not valid json {{{",
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Write", "input": {}},
        ]}}),
        "   ",
        json.dumps({"type": "result", "result": "Wrote the file."}),
        "trailing garbage",
    ])
    assert parse_stream_json(stdout) == {
        "result": "Wrote the file.", "tool_calls": [{"name": "Write"}],
    }


def test_main_reports_unknown_only_names(monkeypatch, capsys):
    """--only naming a name that matches no discovered eval names them explicitly rather than
    falling into the generic "no evals found" message."""
    monkeypatch.setattr(run_evals.shutil, "which", lambda name: "/usr/bin/claude")
    exit_code = run_evals.main(["--only", "nosuchname"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "nosuchname" in captured.err
    assert "unknown eval" in captured.err.lower()
