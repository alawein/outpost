"""The test session must never write the developer's real git config. Some tests run
`git config user.email` inside a temp repo; with GIT_CONFIG pointing at ~/.gitconfig (some
shells set it), that write lands in the real global file."""
import os
import pathlib
import subprocess


def test_git_config_env_is_isolated(tmp_path_factory):
    assert "GIT_CONFIG" not in os.environ
    g = os.environ.get("GIT_CONFIG_GLOBAL")
    assert g, "GIT_CONFIG_GLOBAL must point at a throwaway file"
    scratch = pathlib.Path(g).resolve()
    assert tmp_path_factory.getbasetemp().resolve() in scratch.parents
    home = pathlib.Path.home().resolve()
    assert scratch not in {home / ".gitconfig", home / ".config" / "git" / "config"}


def test_global_git_config_write_lands_in_the_scratch_file():
    scratch = pathlib.Path(os.environ["GIT_CONFIG_GLOBAL"])
    subprocess.run(["git", "config", "--global", "outpost.probe", "yes"], check=True)
    assert "outpost" in scratch.read_text(encoding="utf-8")
    real = pathlib.Path.home() / ".gitconfig"
    if real.is_file():
        assert "outpost.probe" not in real.read_text(encoding="utf-8", errors="replace")
