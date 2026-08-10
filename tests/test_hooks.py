"""Tests for the plugin hooks: the context nudge and the hooks.json wiring."""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOOKS = ROOT / "plugins" / "outpost" / "hooks"
NUDGE = HOOKS / "nudge_context.py"


def _run(hook: pathlib.Path, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(hook)], input=json.dumps(payload),
                          capture_output=True, text=True)


def _run_env(hook: pathlib.Path, payload: dict, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(hook)], input=json.dumps(payload),
                          capture_output=True, text=True, env={**os.environ, **env})


# nudge_context


def test_nudge_silent_when_bounded_by_offset(tmp_path: pathlib.Path):
    f = tmp_path / "file.md"
    f.write_bytes(b"x" * 200)
    proc = _run_env(NUDGE, {"tool_input": {"file_path": str(f), "offset": 10}},
                    {"OUTPOST_NUDGE_BYTES": "100"})
    assert proc.returncode == 0
    assert proc.stderr == ""


def test_nudge_silent_when_bounded_by_limit(tmp_path: pathlib.Path):
    f = tmp_path / "file.md"
    f.write_bytes(b"x" * 200)
    proc = _run_env(NUDGE, {"tool_input": {"file_path": str(f), "limit": 50}},
                    {"OUTPOST_NUDGE_BYTES": "100"})
    assert proc.returncode == 0
    assert proc.stderr == ""


def test_nudge_fires_on_large_unbounded_read(tmp_path: pathlib.Path):
    f = tmp_path / "big.md"
    f.write_bytes(b"x" * 110_000)  # > 100 KB default threshold
    proc = _run(NUDGE, {"tool_input": {"file_path": str(f)}})
    assert proc.returncode == 0  # advisory: never blocks
    assert "nudge" in proc.stderr


def test_nudge_message_is_self_contained(tmp_path: pathlib.Path):
    # the hook ships inside the installed Claude plugin, into a consumer project that never
    # receives Outpost's own docs/, so the guidance must not point somewhere the reader has no
    # way to follow (a prior version pointed at docs/token-budget.md, which a consumer never gets)
    f = tmp_path / "big.md"
    f.write_bytes(b"x" * 110_000)
    proc = _run(NUDGE, {"tool_input": {"file_path": str(f)}})
    assert proc.returncode == 0
    assert "Prefer a targeted range or a subagent to keep it out of your own context." in proc.stderr
    assert "docs/token-budget.md" not in proc.stderr
    assert "docs/" not in proc.stderr


def test_nudge_threshold_via_new_env_name(tmp_path: pathlib.Path):
    f = tmp_path / "file.md"
    f.write_bytes(b"x" * 200)
    proc = _run_env(NUDGE, {"tool_input": {"file_path": str(f)}},
                    {"OUTPOST_NUDGE_BYTES": "100"})
    assert proc.returncode == 0
    assert "nudge" in proc.stderr


def test_nudge_malformed_threshold_fails_open_to_the_default(tmp_path: pathlib.Path):
    f = tmp_path / "file.md"
    f.write_bytes(b"x" * 200)
    proc = _run_env(NUDGE, {"tool_input": {"file_path": str(f)}},
                    {"OUTPOST_NUDGE_BYTES": "banana"})
    assert proc.returncode == 0
    assert proc.stderr == ""


def test_nudge_negative_threshold_falls_back_to_the_default(tmp_path: pathlib.Path):
    f = tmp_path / "file.md"
    f.write_bytes(b"x" * 200)
    proc = _run_env(NUDGE, {"tool_input": {"file_path": str(f)}},
                    {"OUTPOST_NUDGE_BYTES": "-5"})
    assert proc.returncode == 0
    assert proc.stderr == ""


def test_nudge_new_env_name_wins_over_old(tmp_path: pathlib.Path):
    f = tmp_path / "file.md"
    f.write_bytes(b"x" * 200)
    proc = _run_env(NUDGE, {"tool_input": {"file_path": str(f)}},
                    {"OUTPOST_NUDGE_BYTES": "1000"})
    assert proc.returncode == 0
    assert proc.stderr == ""


def test_nudge_malformed_stdin_fails_open():
    proc = subprocess.run([sys.executable, str(NUDGE)], input="not json",
                          capture_output=True, text=True)
    assert proc.returncode == 0


# hooks.json wiring


def test_hooks_json_is_valid_and_wired_correctly():
    spec = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))
    assert "PostToolUse" in spec["hooks"]
    referenced: set[str] = set()
    for event in spec.get("hooks", {}).values():
        for group in event:
            re.compile(group["matcher"])  # must be a valid regex
            for h in group["hooks"]:
                m = re.search(r"hooks/(\w+\.py)", h["command"])
                assert m, f"hook command references no hooks/*.py: {h['command']}"
                assert (HOOKS / m.group(1)).exists(), f"hooks.json references missing {m.group(1)}"
                referenced.add(m.group(1))
    on_disk = {p.name for p in HOOKS.glob("*.py")}
    assert on_disk == referenced, (
        f"hook scripts on disk not wired in hooks.json: {on_disk - referenced}"
    )
