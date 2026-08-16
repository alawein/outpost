"""tools/run_evals.py's filesystem-hashing, eval-discovery, and stream-json-parsing helpers are
pure and testable without a live claude call. run_one_eval's real subprocess.run call for the
claude -p step is exercised too, via a monkeypatched stdlib substitute for the `claude` command
(a real subprocess, not a live claude call) -- see test_run_one_eval_decodes_claude_stdout_as_utf8.
Only a genuine `claude -p` invocation stays out of pytest -q: that path is run by hand via
python tools/run_evals.py, or in the dogfood record, which keeps this suite fast, free, and
deterministic."""
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


def test_discover_evals_finds_every_subdir_with_a_task_txt():
    with tempfile.TemporaryDirectory() as tmp:
        evals_dir = pathlib.Path(tmp)
        (evals_dir / "alpha").mkdir()
        (evals_dir / "alpha" / "task.txt").write_text("do alpha")
        (evals_dir / "beta").mkdir()
        (evals_dir / "beta" / "task.txt").write_text("do beta")
        (evals_dir / "not_an_eval").mkdir()  # no task.txt, must be excluded
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

        # Set up an eval with task.txt and assertions.json but no fixture/ directory
        eval_dir = evals_dir / "broken_eval"
        eval_dir.mkdir()
        (eval_dir / "task.txt").write_text("some task")
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


def test_run_one_eval_decodes_claude_stdout_as_utf8(tmp_path, monkeypatch):
    """Regression test for af79812 (the encoding="utf-8" fix on run_one_eval's claude -p
    subprocess.run call). Redirects only the "claude"-prefixed command to a small stdlib Python
    substitute -- a real .py file, invoked via sys.executable as a list arg, never through a
    shell or a -c string, so there is no argv-encoding ambiguity -- that emits a stream-json
    result line containing a right double curly quote (U+201D) as raw UTF-8 bytes. Every other
    kwarg (cwd, capture_output, text, timeout) passes through unchanged to the real
    subprocess.run, and install.py runs for real against a real catalog prompt, so this exercises
    run_one_eval's actual code path end to end, not a disconnected substitute with its own kwargs.

    U+201D is not an arbitrary "curly quote": its UTF-8 encoding is b"\\xe2\\x80\\x9d", and 0x9d
    is one of only five bytes cp1252 (this platform's locale.getencoding(), what subprocess.run
    falls back to when no encoding= is given) leaves undefined, so decoding it under cp1252
    raises UnicodeDecodeError while decoding it as UTF-8 does not. Confirmed live before writing
    this test: the more obvious choice, U+2019 (the apostrophe-style curly quote), does NOT
    reproduce the crash -- its UTF-8 bytes are all defined in cp1252, so it silently mis-decodes
    instead of raising, which would make a test built on it pass whether or not the fix is
    present.

    Two independent checks, for two different reasons:
      1. The decode-behavior check (outcome["status"] == "pass" and the curly quote round-trips)
         proves the fix actually works, but it can only go RED without the fix on a host whose
         locale-preferred encoding is not already UTF-8 (cp1252 on Windows). CI also runs Ubuntu
         legs, which default to a UTF-8 locale, so removing encoding="utf-8" would NOT make this
         half fail there -- decoding would coincidentally still succeed.
      2. The captured-kwargs check (below) is a call-signature pin, immune to host locale: it
         asserts the literal source line still passes encoding="utf-8" to subprocess.run,
         regardless of whether this host's locale would happen to paper over its absence. This is
         what gives every CI leg (not just Windows) real protection against the kwarg being
         quietly dropped.
    """
    # The curly quote is a real U+201D character in this source file (not a \uXXXX escape), read
    # by Python's own source decoder (UTF-8 by default, independent of locale/console codepage --
    # unlike argv or console I/O, this is not the ambiguous layer). It is written here with an
    # explicit encoding="utf-8" and read back the same way, so the only encoding this test leaves
    # to chance is the one line under test: run_one_eval's claude -p subprocess.run call.
    fake_claude = tmp_path / "fake_claude.py"
    fake_claude.write_text(
        'import sys\n'
        'line = \'{"type": "result", "result": "value”"}\\n\'\n'
        'sys.stdout.buffer.write(line.encode("utf-8"))\n'
        'sys.stdout.buffer.flush()\n',
        encoding="utf-8",
    )

    real_subprocess_run = run_evals.subprocess.run
    captured = {}

    def fake_subprocess_run(cmd, *args, **kwargs):
        if cmd[0] == "claude":
            captured.update(kwargs)  # pin the exact kwargs run_one_eval passed, before rewriting cmd
            cmd = [sys.executable, str(fake_claude)]
        return real_subprocess_run(cmd, *args, **kwargs)

    monkeypatch.setattr(run_evals.subprocess, "run", fake_subprocess_run)

    evals_dir = tmp_path / "evals"
    eval_dir = evals_dir / "debt-log"
    eval_dir.mkdir(parents=True)
    (eval_dir / "task.txt").write_text(
        "unused: fake_claude.py ignores this and always emits a fixed result line",
        encoding="utf-8",
    )
    (eval_dir / "assertions.json").write_text(
        json.dumps([{"type": "text_contains", "value": "value”"}]), encoding="utf-8",
    )
    (eval_dir / "fixture").mkdir()

    # Windows-specific proof: on a non-UTF-8-locale host this line itself raises AttributeError
    # (proc.stdout ends up None; see parse_stream_json) when encoding="utf-8" is missing -- that
    # is the real, observed crash mechanism, not a generic "subprocess raises" assumption.
    outcome = run_evals.run_one_eval("debt-log", evals_dir, ROOT, timeout=30)

    assert outcome["status"] == "pass", outcome
    assert outcome["results"][0][1] is True, outcome["results"]

    # Locale-independent proof: the real call site must still name encoding="utf-8" explicitly,
    # regardless of whether this host's own locale would happen to decode the bytes correctly
    # anyway. Catches the kwarg being dropped on every platform, not just a non-UTF-8-locale one.
    assert captured.get("encoding") == "utf-8", captured


def test_run_one_eval_survives_invalid_utf8_byte_in_claude_stdout(tmp_path, monkeypatch):
    """Regression test: encoding="utf-8" (af79812) only narrows WHICH byte sequences crash
    run_one_eval, it does not close the crash class. The curly quote in the test above is valid
    UTF-8 that only cp1252 chokes on; a byte that is invalid UTF-8 under any codec state -- 0xFF,
    which is never a legal lead or continuation byte -- reproduces the identical batch-halting
    crash encoding="utf-8" alone was meant to fix, because subprocess.run's decode step still
    raises on it. errors="replace" closes the crash class outright: any invalid byte becomes a
    U+FFFD replacement character instead of raising, so proc.stdout is always a real string and
    the eval can proceed to its own pass/fail decision instead of aborting the whole batch (see
    run_evals.main's loop, which does not wrap this call in its own try/except).

    Same monkeypatch pattern as test_run_one_eval_decodes_claude_stdout_as_utf8 above: redirect
    only the "claude"-prefixed command to a stdlib substitute -- a real .py file invoked via
    sys.executable as a list arg, never a shell or a -c string, so there is no argv-encoding
    ambiguity -- while install.py runs for real against a real catalog prompt, so this exercises
    run_one_eval's actual code path end to end. The invalid byte sits on its own line so it fails
    parse_stream_json's per-line json.loads and is silently skipped there (already-tested
    behavior); what this test proves is that the byte reaches that point at all, i.e. the decode
    itself did not raise.
    """
    fake_claude = tmp_path / "fake_claude_invalid_utf8.py"
    fake_claude.write_text(
        'import sys\n'
        'sys.stdout.buffer.write(b"\\xff\\n")\n'
        'sys.stdout.buffer.write(b\'{"type": "result", "result": "eval completed"}\\n\')\n'
        'sys.stdout.buffer.flush()\n',
        encoding="utf-8",
    )

    real_subprocess_run = run_evals.subprocess.run

    def fake_subprocess_run(cmd, *args, **kwargs):
        if cmd[0] == "claude":
            cmd = [sys.executable, str(fake_claude)]
        return real_subprocess_run(cmd, *args, **kwargs)

    monkeypatch.setattr(run_evals.subprocess, "run", fake_subprocess_run)

    evals_dir = tmp_path / "evals"
    eval_dir = evals_dir / "debt-log"
    eval_dir.mkdir(parents=True)
    (eval_dir / "task.txt").write_text(
        "unused: fake_claude_invalid_utf8.py ignores this and always emits a fixed result line",
        encoding="utf-8",
    )
    (eval_dir / "assertions.json").write_text(
        json.dumps([{"type": "text_contains", "value": "eval completed"}]), encoding="utf-8",
    )
    (eval_dir / "fixture").mkdir()

    # Must not raise: an invalid UTF-8 byte anywhere in claude's stdout must not crash
    # run_one_eval or escape it uncaught. Before errors="replace", this call raises out of
    # run_one_eval entirely (the try/except around it only catches subprocess.TimeoutExpired).
    outcome = run_evals.run_one_eval("debt-log", evals_dir, ROOT, timeout=30)

    assert outcome["status"] == "pass", outcome
    assert outcome["results"][0][1] is True, outcome["results"]


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
