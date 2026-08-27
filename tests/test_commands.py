"""Every shipped plugin command is complete: it lints clean against the command contract."""
import pathlib

from kit.checks.commands import lint_command

COMMANDS = pathlib.Path(__file__).resolve().parents[1] / "plugins" / "outpost" / "commands"


def test_every_command_lints_clean():
    files = sorted(COMMANDS.glob("*.md"))
    assert files, "no command files found under plugins/outpost/commands/"
    for p in files:
        errors = lint_command(p.read_text(encoding="utf-8"), p.stem)
        assert errors == [], (p.stem, errors)
