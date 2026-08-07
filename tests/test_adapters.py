"""The adapters coexist: every tool's planned paths are disjoint from the others', and installing
all of them leaves each tool's files intact with the settings only from Claude."""
import json
import pathlib

import install
from kit.adapters import TOOLS, plan_for
from kit.adapters.base import load_prompts

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _paths(tool, tmp):
    return {a.path for a in plan_for(tool, ROOT, tmp)}


def test_planned_paths_are_disjoint(tmp_path):
    # every pair of adapters, so a newly added one is covered without editing this test
    paths = {t: _paths(t, tmp_path) for t in TOOLS}
    tools = sorted(paths)
    for i, a in enumerate(tools):
        for b in tools[i + 1:]:
            assert not (paths[a] & paths[b]), (a, b, paths[a] & paths[b])


def test_all_adapters_coexist_on_disk(tmp_path):
    install.main(["--tool", "all", "--project", str(tmp_path)])
    assert (tmp_path / "CLAUDE.md").is_file()
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / ".cursor" / "rules" / "outpost.mdc").is_file()
    assert (tmp_path / ".github" / "copilot-instructions.md").is_file()
    assert (tmp_path / ".claude" / "skills" / "code-review" / "SKILL.md").is_file()
    assert (tmp_path / ".agents" / "prompts" / "code-review.md").is_file()
    assert (tmp_path / ".cursor" / "rules" / "outpost" / "code-review.md").is_file()
    assert (tmp_path / ".github" / "prompts" / "code-review.prompt.md").is_file()


def test_copilot_leaves_existing_instructions_alone(tmp_path):
    # a user's own repo instructions must survive an install (the prompt files still land)
    gh = tmp_path / ".github"
    gh.mkdir()
    (gh / "copilot-instructions.md").write_text("my own instructions", encoding="utf-8")
    install.main(["--tool", "copilot", "--project", str(tmp_path)])
    assert (gh / "copilot-instructions.md").read_text(encoding="utf-8") == "my own instructions"
    assert (gh / "prompts" / "code-review.prompt.md").is_file()


def test_cursor_prompts_do_not_clobber_a_user_rule(tmp_path):
    # a user's own rule of the same name must survive an install (prompts go in a kit subdir)
    rules = tmp_path / ".cursor" / "rules"
    rules.mkdir(parents=True)
    (rules / "code-review.md").write_text("my own cursor rule", encoding="utf-8")
    install.main(["--tool", "cursor", "--project", str(tmp_path)])
    assert (rules / "code-review.md").read_text(encoding="utf-8") == "my own cursor rule"
    assert (rules / "outpost" / "code-review.md").is_file()


def test_settings_only_from_claude(tmp_path):
    install.main(["--tool", "codex", "--project", str(tmp_path)])
    assert not (tmp_path / ".claude").exists()
    install.main(["--tool", "cursor", "--project", str(tmp_path)])
    assert not (tmp_path / ".claude").exists()
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    assert json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))


def test_every_core_prompt_renders_as_a_skill(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    skills = {p.parent.name for p in (tmp_path / ".claude" / "skills").rglob("SKILL.md")}
    core = {p.stem for p in (ROOT / "prompts" / "core").glob("*.md")}
    assert skills == core


def test_overlay_prompt_overrides_core(tmp_path):
    # a same-stem file under prompts/<tool>/ wins over the core prompt; a README overlay is skipped
    kit = tmp_path / "kit"
    (kit / "prompts" / "core").mkdir(parents=True)
    (kit / "prompts" / "claude").mkdir(parents=True)
    (kit / "prompts" / "core" / "foo.md").write_text("core foo", encoding="utf-8")
    (kit / "prompts" / "claude" / "foo.md").write_text("overlay foo", encoding="utf-8")
    (kit / "prompts" / "claude" / "README.md").write_text("ignore me", encoding="utf-8")
    prompts = dict(load_prompts(kit, "claude"))
    assert prompts == {"foo": "overlay foo"}


def test_scrutiny_prompt_installs_under_every_tool(tmp_path):
    install.main(["--tool", "all", "--project", str(tmp_path)])
    assert (tmp_path / ".claude" / "skills" / "grill" / "SKILL.md").is_file()
    assert (tmp_path / ".agents" / "prompts" / "grill.md").is_file()
    assert (tmp_path / ".cursor" / "rules" / "outpost" / "grill.md").is_file()
    assert (tmp_path / ".github" / "prompts" / "grill.prompt.md").is_file()


def test_load_prompts_none_returns_all():
    names = {n for n, _ in load_prompts(ROOT, "claude", select=None)}
    assert "plan-change" in names and len(names) == 25


def test_converge_ships_to_claude_only(tmp_path):
    # decision 0014: the catalog hosts field limits converge to Claude; the other
    # tools plan and install every core prompt except it, even when selected
    assert "converge" in {n for n, _ in load_prompts(ROOT, "claude")}
    for tool in ("codex", "cursor", "copilot"):
        names = {n for n, _ in load_prompts(ROOT, tool)}
        assert "converge" not in names, tool
        assert len(names) == 24, tool
        selected = {n for n, _ in load_prompts(ROOT, tool, select={"converge", "grill"})}
        assert selected == {"grill"}, tool
    install.main(["--tool", "all", "--project", str(tmp_path)])
    assert (tmp_path / ".claude" / "skills" / "converge" / "SKILL.md").is_file()
    assert not (tmp_path / ".agents" / "prompts" / "converge.md").exists()
    assert not (tmp_path / ".cursor" / "rules" / "outpost" / "converge.md").exists()
    assert not (tmp_path / ".github" / "prompts" / "converge.prompt.md").exists()


def test_manifest_omits_a_claude_only_prompt_for_other_tools(tmp_path):
    # the manifest's per-tool prompt list drives --verify, so a host-limited prompt must
    # not be recorded for a tool that never installs it (it would verify as MISSING)
    install.main(["--tool", "all", "--project", str(tmp_path)])
    manifest = json.loads((tmp_path / ".outpost" / "manifest.json").read_text(encoding="utf-8"))
    assert "converge" in manifest["tools"]["claude"]["prompts"]
    for tool in ("codex", "cursor", "copilot"):
        assert "converge" not in manifest["tools"][tool]["prompts"], tool
    assert install.main(["--tool", "all", "--project", str(tmp_path), "--verify"]) == 0


def test_load_prompts_select_filters_to_subset():
    subset = load_prompts(ROOT, "claude", select={"plan-change", "write-tests"})
    assert [n for n, _ in subset] == ["plan-change", "write-tests"]


def test_load_prompts_select_empty_returns_nothing():
    assert load_prompts(ROOT, "claude", select=set()) == []


def _skill_names(actions):
    return [a.path.split("/")[-2] for a in actions if a.path.startswith(".claude/skills/")]


def test_plan_for_select_limits_claude_skills(tmp_path):
    actions = plan_for("claude", ROOT, tmp_path, select={"plan-change", "grill"})
    assert sorted(_skill_names(actions)) == ["grill", "plan-change"]
    assert any(a.path == "CLAUDE.md" for a in actions)
    assert any(a.path == ".claude/settings.json" for a in actions)


def test_plan_for_all_applies_select_to_every_tool(tmp_path):
    actions = plan_for("all", ROOT, tmp_path, select={"plan-change"})
    prompt_actions = [a for a in actions if a.mode == "write"
                      and any(seg in a.path for seg in ("/skills/", "/prompts/", "/rules/outpost/"))]
    assert prompt_actions, "no prompt actions planned"
    assert all("plan-change" in a.path for a in prompt_actions)
