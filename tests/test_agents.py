"""Each plugin agent is well-formed: YAML frontmatter has a name matching the file stem, a
description of at least 40 chars, and a tools field; the body is not empty."""
import pathlib

from kit.checks import frontmatter_field, split_frontmatter

AGENTS = pathlib.Path(__file__).resolve().parents[1] / "plugins" / "outpost" / "agents"


def test_each_agent_is_well_formed():
    files = sorted(AGENTS.glob("*.md"))
    assert files, "no agent files found under plugins/outpost/agents/"
    for p in files:
        text = p.read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        name = frontmatter_field(fm, "name")
        desc = frontmatter_field(fm, "description")
        tools = frontmatter_field(fm, "tools")
        assert name == p.stem, f"{p.stem}: frontmatter name {name!r} must match file stem"
        assert desc and len(desc) >= 40, (
            f"{p.stem}: description missing or too short "
            f"({len(desc) if desc else 0} chars)"
        )
        assert tools, f"{p.stem}: missing tools field"
        assert body.strip(), f"{p.stem}: body is empty"
