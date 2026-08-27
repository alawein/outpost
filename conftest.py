"""Put the repo root on sys.path so the tests can import the top-level `install` and `validate`
modules and the `kit` package without an editable install, and keep every test's git activity
away from the developer's real config files."""
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _isolate_git_config(tmp_path_factory, monkeypatch):
    """A test that runs `git config user.email` in a temp repo must write that repo's
    .git/config, never ~/.gitconfig. GIT_CONFIG (when a shell sets it) redirects every
    `git config` write to one file, so drop it; GIT_CONFIG_GLOBAL points global reads and
    writes at a throwaway file."""
    monkeypatch.delenv("GIT_CONFIG", raising=False)
    scratch = tmp_path_factory.mktemp("gitconfig") / "gitconfig"
    scratch.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(scratch))
