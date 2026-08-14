"""tools/build.py's own CLI wrapper (argv handling, the unknown-target error path, and the
LF-forcing _write helper) has no test elsewhere: only the three builder functions it dispatches to
are covered, via test_docs_build.py/test_plugin.py/test_templates_build.py."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build  # noqa: E402


def test_main_unknown_target_returns_2_and_calls_no_builder(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(build, "BUILDERS", {"docs": lambda root: calls.append("docs") or {}})

    rc = build.main(["bogus"])

    assert rc == 2
    assert calls == []
    out = capsys.readouterr().out
    assert "unknown target(s): bogus" in out


def test_main_no_args_defaults_to_every_builder(monkeypatch):
    calls = []
    monkeypatch.setattr(build, "BUILDERS", {
        "docs": lambda root: calls.append("docs") or {},
        "plugin": lambda root: calls.append("plugin") or {},
        "templates": lambda root: calls.append("templates") or {},
    })
    monkeypatch.setattr(build, "__file__", "/fake/tools/build.py")

    rc = build.main([])

    assert rc == 0
    assert set(calls) == {"docs", "plugin", "templates"}


def test_main_dispatches_only_the_named_target(monkeypatch):
    calls = []
    monkeypatch.setattr(build, "BUILDERS", {
        "docs": lambda root: calls.append("docs") or {},
        "plugin": lambda root: calls.append("plugin") or {},
    })
    monkeypatch.setattr(build, "__file__", "/fake/tools/build.py")

    rc = build.main(["docs"])

    assert rc == 0
    assert calls == ["docs"]


def test_write_never_produces_crlf(tmp_path):
    build._write(tmp_path, lambda root: {"out/generated.txt": "line one\nline two\n"})

    raw = (tmp_path / "out" / "generated.txt").read_bytes()

    assert raw == b"line one\nline two\n"
    assert b"\r\n" not in raw
