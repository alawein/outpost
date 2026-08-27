"""The adapters coexist: every tool's planned paths are disjoint from the others', and installing
all of them leaves each tool's files intact with the settings only from Claude."""
import json
import pathlib
import re
import sys

import pytest

import install
from kit.adapters import TOOLS, plan_for
from kit.adapters.base import load_prompts
from kit.adapters.windsurf import WINDSURF_LIMIT
from kit.checks import frontmatter_field, split_frontmatter

ROOT = pathlib.Path(__file__).resolve().parents[1]
# every tool but the primary one, so a new adapter joins the host-limit tests without an edit here
OTHER_TOOLS = tuple(t for t in TOOLS if t != "claude")


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
    assert (tmp_path / ".windsurf" / "rules" / "outpost.md").is_file()
    assert (tmp_path / "GEMINI.md").is_file()
    assert (tmp_path / ".claude" / "skills" / "code-review" / "SKILL.md").is_file()
    assert (tmp_path / ".agents" / "prompts" / "code-review.md").is_file()
    assert (tmp_path / ".cursor" / "rules" / "outpost" / "code-review.md").is_file()
    assert (tmp_path / ".github" / "prompts" / "code-review.prompt.md").is_file()
    assert (tmp_path / ".windsurf" / "workflows" / "outpost-code-review.md").is_file()
    assert (tmp_path / ".gemini" / "commands" / "outpost" / "code-review.toml").is_file()


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
    for tool in OTHER_TOOLS:
        install.main(["--tool", tool, "--project", str(tmp_path)])
        assert not (tmp_path / ".claude").exists(), tool
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
    assert (tmp_path / ".windsurf" / "workflows" / "outpost-grill.md").is_file()
    assert (tmp_path / ".gemini" / "commands" / "outpost" / "grill.toml").is_file()


def test_load_prompts_none_returns_all():
    names = {n for n, _ in load_prompts(ROOT, "claude", select=None)}
    assert "plan-change" in names and len(names) == 28


def test_converge_ships_to_claude_only(tmp_path):
    # the catalog hosts field limits converge to Claude; the other
    # tools plan and install every core prompt except it, even when selected
    assert "converge" in {n for n, _ in load_prompts(ROOT, "claude")}
    for tool in OTHER_TOOLS:
        names = {n for n, _ in load_prompts(ROOT, tool)}
        assert "converge" not in names, tool
        assert len(names) == 27, tool
        selected = {n for n, _ in load_prompts(ROOT, tool, select={"converge", "grill"})}
        assert selected == {"grill"}, tool
    install.main(["--tool", "all", "--project", str(tmp_path)])
    assert (tmp_path / ".claude" / "skills" / "converge" / "SKILL.md").is_file()
    assert not (tmp_path / ".agents" / "prompts" / "converge.md").exists()
    assert not (tmp_path / ".cursor" / "rules" / "outpost" / "converge.md").exists()
    assert not (tmp_path / ".github" / "prompts" / "converge.prompt.md").exists()
    assert not (tmp_path / ".windsurf" / "workflows" / "outpost-converge.md").exists()
    assert not (tmp_path / ".gemini" / "commands" / "outpost" / "converge.toml").exists()


def test_manifest_omits_a_claude_only_prompt_for_other_tools(tmp_path):
    # the manifest's per-tool prompt list drives --verify, so a host-limited prompt must
    # not be recorded for a tool that never installs it (it would verify as MISSING)
    install.main(["--tool", "all", "--project", str(tmp_path)])
    manifest = json.loads((tmp_path / ".outpost" / "manifest.json").read_text(encoding="utf-8"))
    assert "converge" in manifest["tools"]["claude"]["prompts"]
    for tool in OTHER_TOOLS:
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
    # with terse off, every write-mode action is a prompt file, so one per tool proves each
    # adapter honored select (a tool that ignored it would add more; one that dropped it, fewer)
    prompt_actions = [a for a in actions if a.mode == "write"]
    assert len(prompt_actions) == len(TOOLS), [a.path for a in prompt_actions]
    assert all("plan-change" in a.path for a in prompt_actions)


# Windsurf: an always-on rule plus one workflow per prompt, each under the 12,000-character cap
# (WINDSURF_LIMIT, imported from the adapter so the test and the install agree)


def test_windsurf_rule_has_always_on_frontmatter(tmp_path):
    rules = [a for a in plan_for("windsurf", ROOT, tmp_path) if a.path == ".windsurf/rules/outpost.md"]
    assert len(rules) == 1 and rules[0].mode == "create"
    fm, _ = split_frontmatter(rules[0].content)
    assert frontmatter_field(fm, "trigger") == "always_on"
    assert frontmatter_field(fm, "description")
    assert len(rules[0].content) < WINDSURF_LIMIT


def test_windsurf_workflows_are_prefixed_and_under_limit(tmp_path):
    # the outpost- prefix keeps every workflow at the top level and clear of a user's own
    workflows = [a for a in plan_for("windsurf", ROOT, tmp_path) if a.mode == "write"]
    names = {n for n, _ in load_prompts(ROOT, "windsurf")}
    assert {a.path for a in workflows} == {f".windsurf/workflows/outpost-{n}.md" for n in names}
    for a in workflows:
        assert len(a.content) < WINDSURF_LIMIT, a.path
        # a workflow shows its description in the picker; the prompt frontmatter supplies it
        assert frontmatter_field(split_frontmatter(a.content)[0], "description"), a.path


def test_windsurf_refuses_a_prompt_over_the_cap(tmp_path):
    # the cap is enforced at plan time, so an overlay prompt over it fails loudly instead of
    # installing a workflow Windsurf would reject
    kit = tmp_path / "kit"
    (kit / "prompts" / "core").mkdir(parents=True)
    (kit / "templates").mkdir()
    (kit / "templates" / "windsurf-rules.md").write_text("rule", encoding="utf-8")
    (kit / "prompts" / "core" / "big.md").write_text("x" * (WINDSURF_LIMIT + 1), encoding="utf-8")
    with pytest.raises(ValueError, match="big"):
        plan_for("windsurf", kit, tmp_path)


def test_windsurf_refuses_a_rule_over_the_cap(tmp_path):
    # the always-on rule has the same per-file cap as a workflow
    kit = tmp_path / "kit"
    (kit / "prompts" / "core").mkdir(parents=True)
    (kit / "templates").mkdir()
    (kit / "templates" / "windsurf-rules.md").write_text("r" * (WINDSURF_LIMIT + 1), encoding="utf-8")
    with pytest.raises(ValueError, match="outpost.md"):
        plan_for("windsurf", kit, tmp_path)


def test_windsurf_leaves_existing_rule_alone(tmp_path):
    rules = tmp_path / ".windsurf" / "rules"
    rules.mkdir(parents=True)
    (rules / "outpost.md").write_text("my own rule", encoding="utf-8")
    install.main(["--tool", "windsurf", "--project", str(tmp_path)])
    assert (rules / "outpost.md").read_text(encoding="utf-8") == "my own rule"
    assert (tmp_path / ".windsurf" / "workflows" / "outpost-code-review.md").is_file()


# Gemini CLI: GEMINI.md plus one TOML command per prompt under .gemini/commands/outpost/

def _parse_toml(text):
    if sys.version_info >= (3, 11):
        import tomllib
        return tomllib.loads(text)
    # older interpreters: pull the two keys by shape (a basic string and a multi-line literal)
    desc = re.search(r'(?m)^description = "((?:[^"\\]|\\.)*)"$', text)
    # anchored to the end of the text, so trailing junk after the closing delimiter fails here
    # the way tomllib fails it on 3.11+
    prompt = re.search(r"(?ms)^prompt = '''\n(.*?)'''\n?\Z", text)
    assert desc and prompt, text[:200]
    return {"description": desc.group(1).replace('\\"', '"').replace("\\\\", "\\"),
            "prompt": prompt.group(1)}


def test_gemini_commands_are_valid_toml(tmp_path):
    prompts = dict(load_prompts(ROOT, "gemini"))
    commands = [a for a in plan_for("gemini", ROOT, tmp_path) if a.mode == "write"]
    assert {a.path for a in commands} == {f".gemini/commands/outpost/{n}.toml" for n in prompts}
    for a in commands:
        name = a.path.rsplit("/", 1)[1][:-len(".toml")]
        fm, body = split_frontmatter(prompts[name])
        data = _parse_toml(a.content)
        assert data["description"] == frontmatter_field(fm, "description"), a.path
        assert data["prompt"].strip() == body.strip(), a.path
        assert not data["prompt"].lstrip().startswith("---"), a.path
        assert "'''" not in data["prompt"], a.path


def test_gemini_leaves_existing_guide_alone(tmp_path):
    (tmp_path / "GEMINI.md").write_text("my own guide", encoding="utf-8")
    install.main(["--tool", "gemini", "--project", str(tmp_path)])
    assert (tmp_path / "GEMINI.md").read_text(encoding="utf-8") == "my own guide"
    assert (tmp_path / ".gemini" / "commands" / "outpost" / "code-review.toml").is_file()


def test_to_command_toml_rejects_triple_quote():
    # a TOML literal string has no escapes, so a body holding the delimiter cannot be encoded
    from kit.adapters.gemini import to_command_toml
    with pytest.raises(ValueError):
        to_command_toml("x", "---\nname: x\ndescription: d\n---\n\nbody with ''' inside\n")


def test_to_command_toml_rejects_gemini_injection():
    # Gemini CLI runs !{...} as a shell command and @{...} as a file injection inside a command
    # prompt, so a body carrying either must never install as text
    from kit.adapters.gemini import to_command_toml
    for body in ("run !{ls} first\n", "read @{secrets.txt} first\n"):
        with pytest.raises(ValueError, match="Gemini CLI runs"):
            to_command_toml("x", "---\nname: x\ndescription: d\n---\n\n" + body)


def test_to_command_toml_rejects_a_control_character():
    # a TOML literal string cannot hold a form feed; tomllib rejects the file, so the adapter must
    from kit.adapters.gemini import to_command_toml
    with pytest.raises(ValueError, match="control character"):
        to_command_toml("x", "---\nname: x\ndescription: d\n---\n\nbody\x0cwith a form feed\n")


def test_to_command_toml_rejects_a_control_character_in_the_description():
    # a TOML basic string cannot hold a raw control character either
    from kit.adapters.gemini import to_command_toml
    with pytest.raises(ValueError, match="control character"):
        to_command_toml("x", "---
name: x
description: dd
---

body
")


def test_to_command_toml_escapes_the_description():
    from kit.adapters.gemini import to_command_toml
    text = to_command_toml("x", '---\nname: x\ndescription: say "hi" a\\b\n---\n\nbody\n')
    data = _parse_toml(text)
    assert data["description"] == 'say "hi" a\\b'
    assert data["prompt"].strip() == "body"
