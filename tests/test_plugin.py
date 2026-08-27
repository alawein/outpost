"""Plugin packaging falsifiers: the plugin mirrors the catalog and loads cleanly."""
import json
import pathlib

from kit.plugin import build_plugin

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_build_plugin_emits_a_skill_per_catalog_prompt():
    files = build_plugin(ROOT)
    catalog = json.loads((ROOT / "kit" / "catalog" / "catalog.json").read_text(encoding="utf-8"))
    names = {p["name"] for p in catalog["prompts"]}
    skills = {k for k in files if k.startswith("plugins/outpost/skills/")}
    assert len(skills) == len(names)
    for name in names:
        assert f"plugins/outpost/skills/{name}/SKILL.md" in files


def test_build_plugin_manifest_version_matches_catalog():
    files = build_plugin(ROOT)
    catalog = json.loads((ROOT / "kit" / "catalog" / "catalog.json").read_text(encoding="utf-8"))
    manifest = json.loads(files["plugins/outpost/.claude-plugin/plugin.json"])
    assert manifest["version"] == catalog["version"]


def test_plugin_skill_matches_the_source_prompt():
    # The generated skill body comes from prompts/core, not a hand-edited copy: the generator
    # output for a known prompt must contain that prompt's body text.
    files = build_plugin(ROOT)
    src = (ROOT / "prompts" / "core" / "plan-change.md").read_text(encoding="utf-8")
    skill = files["plugins/outpost/skills/plan-change/SKILL.md"]
    # A distinctive line from plan-change.md that must appear in the rendered skill.
    assert "Most wasted work comes from editing before understanding." in src
    assert "Most wasted work comes from editing before understanding." in skill
    # No non-stdlib import crept into the generator.
    import kit.plugin  # noqa: F401
    import sys
    assert "yaml" not in sys.modules  # generator stays stdlib-only


def test_stress_command_routes_to_all_four_scrutiny_prompts():
    cmd = (ROOT / "plugins" / "outpost" / "commands" / "stress.md").read_text(
        encoding="utf-8"
    )
    for stance in ("interrogate", "self-refute", "grill", "premortem"):
        assert f"`{stance}`" in cmd
