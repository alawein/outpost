"""A source is a skill library the kit does not own, cloned by the user and passed with --source.
Discovery validates it, every adapter installs it beside the core pack, and the manifest records
it so --verify, --prune, and --remove cover its files without the flag."""
import json
import pathlib
import re
import shutil
import sys

import pytest

import install
from kit.adapters import TOOLS, plan_for
from kit.adapters.base import Skip, source_actions
from kit.adapters.windsurf import WINDSURF_LIMIT
from kit.sources import Skill, Source, discover

ROOT = pathlib.Path(__file__).resolve().parents[1]

ALPHA = "---\nname: alpha\ndescription: Alpha, a skill with supporting files\n---\n\n# Alpha\n\nRead notes.md and run scripts/run.sh.\n"
BETA = "---\nname: beta\ndescription: Beta, a plain skill\n---\n\n# Beta\n\nNothing else here.\n"
BIG_HEAD = "---\nname: big\ndescription: Big, over the Windsurf cap\n---\n\n"


def make_source(root: pathlib.Path, name: str = "lib", layout: str = "skills") -> pathlib.Path:
    """A fixture source at root/name: alpha (with notes.md and scripts/run.sh), beta (plain), and
    big (12,001 characters). `layout` is 'skills' for <source>/skills/<name>/SKILL.md or 'flat'
    for <source>/<name>/SKILL.md."""
    src = root / name
    base = src / "skills" if layout == "skills" else src
    (base / "alpha" / "scripts").mkdir(parents=True)
    (base / "alpha" / "SKILL.md").write_text(ALPHA, encoding="utf-8")
    # bytes, so the fixture holds LF on every platform (write_text would give CRLF on Windows)
    (base / "alpha" / "notes.md").write_bytes(b"alpha notes\n")
    (base / "alpha" / "scripts" / "run.sh").write_bytes(b"#!/bin/sh\necho alpha\n")
    (base / "beta").mkdir()
    (base / "beta" / "SKILL.md").write_text(BETA, encoding="utf-8")
    (base / "big").mkdir()
    (base / "big" / "SKILL.md").write_text(BIG_HEAD + "x" * (WINDSURF_LIMIT + 1 - len(BIG_HEAD)),
                                           encoding="utf-8")
    return src


def _tree(root: pathlib.Path) -> dict:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}


def _main(*argv):
    return install.main([str(a) for a in argv])


def _manifest(project: pathlib.Path) -> dict:
    return json.loads((project / ".outpost" / "manifest.json").read_text(encoding="utf-8"))


def _write_manifest(project: pathlib.Path, manifest: dict) -> None:
    (project / ".outpost").mkdir(exist_ok=True)
    (project / ".outpost" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                                          encoding="utf-8")


def _link_dir(target: pathlib.Path, link: pathlib.Path) -> None:
    """A directory link the OS offers without privilege: an NTFS junction on Windows (which
    Path.is_symlink() does not report on Python 3.12+), a symlink elsewhere. Skips the test when
    neither can be made."""
    try:
        if sys.platform == "win32":
            import _winapi
            _winapi.CreateJunction(str(target), str(link))
        else:
            link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError, ImportError, AttributeError):
        pytest.skip("directory links not available in this environment")


# discovery


def test_discover_reads_both_layouts(tmp_path):
    for layout in ("skills", "flat"):
        src = discover(make_source(tmp_path / layout, layout=layout))
        assert isinstance(src, Source) and src.name == "lib"
        assert src.path == (tmp_path / layout / "lib").resolve()
        assert [s.name for s in src.skills] == ["alpha", "beta", "big"]


def test_discover_reads_body_description_files_and_chars(tmp_path):
    src = discover(make_source(tmp_path))
    alpha, beta, big = src.skills
    assert isinstance(alpha, Skill)
    assert alpha.body == ALPHA and alpha.chars == len(ALPHA)
    assert alpha.description == "Alpha, a skill with supporting files"
    assert alpha.files == {"notes.md": b"alpha notes\n", "scripts/run.sh": b"#!/bin/sh\necho alpha\n"}
    assert beta.files == {}
    assert big.chars == WINDSURF_LIMIT + 1


def test_discover_lowercases_the_source_name(tmp_path):
    src = discover(make_source(tmp_path, name="MyLib"))
    assert src.name == "mylib"


def test_discover_rejects_a_source_name_off_the_rule(tmp_path):
    with pytest.raises(ValueError, match=r"my_lib.*\[a-z0-9-\]"):
        discover(make_source(tmp_path, name="my_lib"))


def test_source_name_rejects_a_trailing_newline():
    # re.match with a trailing $ accepts "abc\n"; the rule is [a-z0-9-] and nothing else
    from kit.sources import source_name
    with pytest.raises(ValueError, match="rename the clone"):
        source_name(pathlib.Path("abc\n"))
    assert source_name(pathlib.Path("Abc-1")) == "abc-1"


def test_discover_rejects_a_missing_directory(tmp_path):
    with pytest.raises(ValueError, match="not a directory"):
        discover(tmp_path / "nope")


def test_discover_rejects_an_empty_source(tmp_path):
    (tmp_path / "lib").mkdir()
    with pytest.raises(ValueError, match="no skills"):
        discover(tmp_path / "lib")


def test_discover_rejects_a_skill_name_off_the_rule(tmp_path):
    src = tmp_path / "lib" / "skills"
    (src / "Bad_Name").mkdir(parents=True)
    (src / "Bad_Name" / "SKILL.md").write_text(
        "---\nname: Bad_Name\ndescription: d\n---\n\nbody\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Bad_Name"):
        discover(tmp_path / "lib")


def test_discover_rejects_a_name_that_does_not_match_its_directory(tmp_path):
    src = tmp_path / "lib" / "skills"
    (src / "gamma").mkdir(parents=True)
    (src / "gamma" / "SKILL.md").write_text(
        "---\nname: delta\ndescription: d\n---\n\nbody\n", encoding="utf-8")
    with pytest.raises(ValueError, match="gamma"):
        discover(tmp_path / "lib")


def test_discover_rejects_a_skill_without_a_description(tmp_path):
    src = tmp_path / "lib" / "skills"
    (src / "gamma").mkdir(parents=True)
    (src / "gamma" / "SKILL.md").write_text("---\nname: gamma\n---\n\nbody\n", encoding="utf-8")
    with pytest.raises(ValueError, match="gamma.*description"):
        discover(tmp_path / "lib")


@pytest.mark.parametrize("indicator", [">", "|", ">-", "|-"])
def test_discover_rejects_a_multi_line_description(tmp_path, indicator):
    # a YAML block scalar would otherwise pass validation as ">" and become Gemini's description
    src = tmp_path / "lib" / "skills"
    (src / "gamma").mkdir(parents=True)
    (src / "gamma" / "SKILL.md").write_text(
        f"---\nname: gamma\ndescription: {indicator}\n  spread over\n  two lines\n---\n\nbody\n",
        encoding="utf-8")
    with pytest.raises(ValueError, match="gamma.*multi-line description"):
        discover(tmp_path / "lib")


def test_discover_ignores_a_directory_without_a_skill_file(tmp_path):
    src = make_source(tmp_path)
    (src / "skills" / "docs").mkdir()
    (src / "skills" / "docs" / "guide.md").write_text("not a skill\n", encoding="utf-8")
    assert [s.name for s in discover(src).skills] == ["alpha", "beta", "big"]


def test_discover_skips_a_symlink_inside_a_skill_and_reports_it(tmp_path):
    src = make_source(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("secret\n", encoding="utf-8")
    try:
        (src / "skills" / "alpha" / "link.md").symlink_to(outside)
        (src / "skills" / "alpha" / "linkdir").symlink_to(tmp_path, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not permitted in this environment")
    alpha = discover(src).skills[0]
    assert set(alpha.files) == {"notes.md", "scripts/run.sh"}  # neither link was followed
    assert {rel for rel, _ in alpha.skipped} == {"link.md", "linkdir"}
    assert all(reason == "symlink" for _, reason in alpha.skipped)


def test_discover_skips_a_symlinked_skill_directory(tmp_path):
    src = make_source(tmp_path)
    try:
        (src / "skills" / "linked").symlink_to(src / "skills" / "beta", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not permitted in this environment")
    found = discover(src)
    assert [s.name for s in found.skills] == ["alpha", "beta", "big"]
    assert found.skipped == (("skills/linked", "symlink"),)


# Directory links the symlink check misses: an NTFS junction is not a symlink to Python 3.12+,
# and os.walk(followlinks=False) descends into it. Each shape below must be skipped and
# reported, never read through.


def test_discover_skips_a_linked_directory_inside_a_skill_and_never_reads_through_it(tmp_path):
    src = make_source(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "leak.txt").write_bytes(b"secret\n")
    _link_dir(outside, src / "skills" / "alpha" / "linkdir")
    alpha = discover(src).skills[0]
    assert set(alpha.files) == {"notes.md", "scripts/run.sh"}
    assert alpha.skipped == (("linkdir", "symlink"),)


def test_discover_skips_a_link_loop_inside_a_skill(tmp_path):
    src = make_source(tmp_path)
    _link_dir(src / "skills" / "alpha", src / "skills" / "alpha" / "loop")
    alpha = discover(src).skills[0]
    assert set(alpha.files) == {"notes.md", "scripts/run.sh"}  # no loop/loop/... nesting
    assert alpha.skipped == (("loop", "symlink"),)


def test_discover_skips_a_linked_skill_directory(tmp_path):
    src = make_source(tmp_path)
    outside = tmp_path / "outside" / "jskill"
    outside.mkdir(parents=True)
    (outside / "SKILL.md").write_text("---\nname: jskill\ndescription: d\n---\n\nbody\n",
                                      encoding="utf-8")
    _link_dir(outside, src / "skills" / "jskill")
    found = discover(src)
    assert [s.name for s in found.skills] == ["alpha", "beta", "big"]
    assert found.skipped == (("skills/jskill", "symlink"),)


def test_discover_refuses_a_linked_skills_directory(tmp_path):
    outside = tmp_path / "outside" / "skills" / "leaky"
    outside.mkdir(parents=True)
    (outside / "SKILL.md").write_text("---\nname: leaky\ndescription: d\n---\n\nbody\n",
                                      encoding="utf-8")
    src = tmp_path / "lib"
    src.mkdir()
    _link_dir(tmp_path / "outside" / "skills", src / "skills")
    with pytest.raises(ValueError, match="skills/ is a symlink or junction"):
        discover(src)


# per-tool actions


def _actions(tool, src, select=None, skipped=None):
    return source_actions(tool, src, select, skipped)


def test_claude_and_codex_install_skill_and_supporting_files(tmp_path):
    src = discover(make_source(tmp_path))
    for tool, base in (("claude", ".claude/skills"), ("codex", ".agents/skills")):
        by_path = {a.path: a for a in _actions(tool, src)}
        assert set(by_path) == {
            f"{base}/alpha/SKILL.md", f"{base}/alpha/notes.md", f"{base}/alpha/scripts/run.sh",
            f"{base}/beta/SKILL.md", f"{base}/big/SKILL.md"}, tool
        assert by_path[f"{base}/alpha/SKILL.md"].content == ALPHA
        assert by_path[f"{base}/alpha/notes.md"].content == "alpha notes\n"
        assert all(a.mode == "write" for a in by_path.values())


def test_cursor_copilot_windsurf_install_skill_file_only(tmp_path):
    src = discover(make_source(tmp_path))
    expected = {
        "cursor": {".cursor/rules/lib/alpha.md", ".cursor/rules/lib/beta.md",
                   ".cursor/rules/lib/big.md"},
        "copilot": {".github/prompts/lib-alpha.prompt.md", ".github/prompts/lib-beta.prompt.md",
                    ".github/prompts/lib-big.prompt.md"},
        "windsurf": {".windsurf/workflows/lib-alpha.md", ".windsurf/workflows/lib-beta.md"},
    }
    for tool, paths in expected.items():
        actions = _actions(tool, src)
        assert {a.path for a in actions} == paths, tool
        assert all(a.mode == "write" for a in actions)
        assert all("notes" not in a.path and "run.sh" not in a.path for a in actions), tool
        assert next(a.content for a in actions if "alpha" in a.path) == ALPHA


def test_windsurf_skips_an_over_cap_skill_with_a_note(tmp_path):
    src = discover(make_source(tmp_path))
    skipped = []
    actions = _actions("windsurf", src, skipped=skipped)
    assert not any("big" in a.path for a in actions)
    assert len(skipped) == 1 and isinstance(skipped[0], Skip)
    assert skipped[0].path == ".windsurf/workflows/lib-big.md"
    assert skipped[0].label == "skip (over cap)"
    assert str(WINDSURF_LIMIT) in skipped[0].reason and "truncat" in skipped[0].reason


def _parse_toml(text):
    if sys.version_info >= (3, 11):
        import tomllib
        return tomllib.loads(text)
    desc = re.search(r'(?m)^description = "((?:[^"\\]|\\.)*)"$', text)
    prompt = re.search(r"(?ms)^prompt = '''\n(.*?)'''\n?\Z", text)
    assert desc and prompt, text[:200]
    return {"description": desc.group(1), "prompt": prompt.group(1)}


def test_gemini_renders_valid_toml_commands(tmp_path):
    src = discover(make_source(tmp_path))
    actions = _actions("gemini", src)
    assert {a.path for a in actions} == {".gemini/commands/lib/alpha.toml",
                                         ".gemini/commands/lib/beta.toml",
                                         ".gemini/commands/lib/big.toml"}
    alpha = next(a for a in actions if a.path.endswith("alpha.toml"))
    data = _parse_toml(alpha.content)
    assert data["description"] == "Alpha, a skill with supporting files"
    assert data["prompt"].strip() == "# Alpha\n\nRead notes.md and run scripts/run.sh."
    assert "/lib:alpha" in alpha.note


def test_gemini_skips_a_skill_it_cannot_render(tmp_path):
    src = make_source(tmp_path)
    (src / "skills" / "beta" / "SKILL.md").write_text(
        "---\nname: beta\ndescription: d\n---\n\nrun !{ls} now\n", encoding="utf-8")
    skipped = []
    actions = _actions("gemini", discover(src), skipped=skipped)
    assert not any("beta" in a.path for a in actions)
    assert [s.path for s in skipped] == [".gemini/commands/lib/beta.toml"]
    assert "Gemini CLI runs" in skipped[0].reason


def test_a_non_text_supporting_file_is_skipped_for_claude_and_codex(tmp_path):
    src = make_source(tmp_path)
    (src / "skills" / "alpha" / "logo.bin").write_bytes(b"\xff\xfe\x00binary")
    found = discover(src)
    assert found.skills[0].files["logo.bin"] == b"\xff\xfe\x00binary"
    for tool, base in (("claude", ".claude/skills"), ("codex", ".agents/skills")):
        skipped = []
        actions = _actions(tool, found, skipped=skipped)
        assert not any(a.path.endswith("logo.bin") for a in actions)
        assert [(s.path, s.label) for s in skipped] == [(f"{base}/alpha/logo.bin", "skip (not text)")]
    for tool in ("cursor", "copilot", "windsurf", "gemini"):
        skipped = []
        _actions(tool, found, skipped=skipped)
        assert not any("logo" in s.path for s in skipped), tool


def test_select_applies_to_source_skills(tmp_path):
    src = discover(make_source(tmp_path))
    assert {a.path for a in _actions("claude", src, select={"beta"})} == {".claude/skills/beta/SKILL.md"}
    assert _actions("cursor", src, select=set()) == []


def test_plan_for_appends_source_actions_after_the_core(tmp_path):
    src = discover(make_source(tmp_path))
    actions = plan_for("claude", ROOT, tmp_path, sources=[src])
    core = plan_for("claude", ROOT, tmp_path)
    assert actions[:len(core)] == core
    assert {a.path for a in actions[len(core):]} == {a.path for a in _actions("claude", src)}
    everything = plan_for("all", ROOT, tmp_path, sources=[src])
    for tool in TOOLS:
        assert all(a in everything for a in _actions(tool, src)), tool


def test_plan_for_rejects_a_source_skill_that_collides_with_a_core_prompt(tmp_path):
    src = tmp_path / "lib" / "skills"
    (src / "plan-change").mkdir(parents=True)
    (src / "plan-change" / "SKILL.md").write_text(
        "---\nname: plan-change\ndescription: d\n---\n\nbody\n", encoding="utf-8")
    with pytest.raises(ValueError, match="plan-change"):
        plan_for("claude", ROOT, tmp_path, sources=[discover(tmp_path / "lib")])


# the installer


def test_install_writes_every_tool_and_verify_is_in_sync(tmp_path, capsys):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    assert _main("--tool", "all", "--project", project, "--source", src) == 0
    assert (project / ".claude" / "skills" / "alpha" / "SKILL.md").read_text(encoding="utf-8") == ALPHA
    assert (project / ".claude" / "skills" / "alpha" / "scripts" / "run.sh").is_file()
    assert (project / ".agents" / "skills" / "alpha" / "notes.md").is_file()
    assert (project / ".cursor" / "rules" / "lib" / "beta.md").is_file()
    assert (project / ".github" / "prompts" / "lib-beta.prompt.md").is_file()
    assert (project / ".windsurf" / "workflows" / "lib-beta.md").is_file()
    assert not (project / ".windsurf" / "workflows" / "lib-big.md").exists()
    assert (project / ".gemini" / "commands" / "lib" / "big.toml").is_file()
    out = capsys.readouterr().out
    assert "skip" in out and ".windsurf/workflows/lib-big.md" in out and "over cap" in out
    assert _main("--tool", "all", "--project", project, "--source", src, "--verify") == 0
    assert "in sync" in capsys.readouterr().out


def test_install_is_idempotent_with_a_source(tmp_path):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _main("--tool", "all", "--project", project, "--source", src)
    first = _tree(project)
    _main("--tool", "all", "--project", project, "--source", src)
    assert _tree(project) == first


def test_dry_run_writes_nothing_and_lists_skips(tmp_path, capsys):
    src = make_source(tmp_path)
    (src / "skills" / "alpha" / "logo.bin").write_bytes(b"\xff\xfe\x00")
    project = tmp_path / "project"
    project.mkdir()
    assert _main("--tool", "all", "--project", project, "--source", src, "--dry-run") == 0
    assert _tree(project) == {}
    out = capsys.readouterr().out
    assert ".claude/skills/alpha/SKILL.md" in out
    assert "[skip (over cap)" in out and ".windsurf/workflows/lib-big.md" in out
    assert "[skip (not text)" in out and ".claude/skills/alpha/logo.bin" in out


def test_manifest_records_the_source(tmp_path):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _main("--tool", "claude", "--project", project, "--source", src)
    manifest = _manifest(project)
    # the path lives at the top level (one clone, re-discovered by any later run); the skills
    # kept live with the tool, since installs are per tool
    assert manifest["sources"] == {"lib": {"path": src.resolve().as_posix()}}
    assert manifest["tools"]["claude"]["sources"] == {"lib": ["alpha", "beta", "big"]}
    files = manifest["tools"]["claude"]["files"]
    assert files[".claude/skills/alpha/notes.md"]["existed"] is False
    assert ".claude/skills/alpha/scripts/run.sh" in files
    assert "alpha" not in manifest["tools"]["claude"]["prompts"]


def test_only_and_exclude_apply_to_source_skills(tmp_path):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    assert _main("--tool", "claude", "--project", project, "--source", src, "--only", "beta,grill") == 0
    skills = project / ".claude" / "skills"
    assert (skills / "beta" / "SKILL.md").is_file() and (skills / "grill" / "SKILL.md").is_file()
    assert not (skills / "alpha").exists()
    assert _manifest(project)["tools"]["claude"]["sources"]["lib"] == ["beta"]
    assert _main("--tool", "claude", "--project", project, "--source", src, "--verify") == 0
    other = tmp_path / "other"
    other.mkdir()
    assert _main("--tool", "claude", "--project", other, "--source", src, "--exclude", "alpha") == 0
    assert (other / ".claude" / "skills" / "beta" / "SKILL.md").is_file()
    assert not (other / ".claude" / "skills" / "alpha").exists()


def test_install_leaves_a_users_own_skill_alone(tmp_path, capsys):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    mine = project / ".claude" / "skills" / "alpha"
    mine.mkdir(parents=True)
    (mine / "SKILL.md").write_text("my own alpha\n", encoding="utf-8")
    assert _main("--tool", "claude", "--project", project, "--source", src) == 0
    out = capsys.readouterr().out
    assert (mine / "SKILL.md").read_text(encoding="utf-8") == "my own alpha\n"
    assert "skip" in out and ".claude/skills/alpha/SKILL.md" in out
    # the user's skill directory stays whole: no supporting file lands beside their SKILL.md
    assert not (mine / "notes.md").exists() and not (mine / "scripts").exists()
    assert (project / ".claude" / "skills" / "beta" / "SKILL.md").is_file()
    manifest = json.loads((project / ".outpost" / "manifest.json").read_text(encoding="utf-8"))
    files = manifest["tools"]["claude"]["files"]
    assert files[".claude/skills/alpha/SKILL.md"]["existed"] is True
    assert ".claude/skills/alpha/notes.md" not in files
    assert _main("--tool", "claude", "--project", project, "--source", src, "--verify") == 0
    _main("--tool", "claude", "--project", project, "--remove")
    assert (mine / "SKILL.md").read_text(encoding="utf-8") == "my own alpha\n"
    assert not (project / ".claude" / "skills" / "beta").exists()


@pytest.mark.parametrize("tool,path", [
    ("codex", ".agents/skills/alpha/SKILL.md"),
    ("cursor", ".cursor/rules/lib/alpha.md"),
    ("copilot", ".github/prompts/lib-alpha.prompt.md"),
    ("windsurf", ".windsurf/workflows/lib-alpha.md"),
    ("gemini", ".gemini/commands/lib/alpha.toml"),
])
def test_install_leaves_a_users_own_file_alone_for_every_tool(tmp_path, capsys, tool, path):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    mine = project / path
    mine.parent.mkdir(parents=True)
    mine.write_text("mine\n", encoding="utf-8")
    assert _main("--tool", tool, "--project", project, "--source", src, "--dry-run") == 0
    assert f"[skip (exists) ] write  {path}" in capsys.readouterr().out
    assert _main("--tool", tool, "--project", project, "--source", src) == 0
    assert mine.read_text(encoding="utf-8") == "mine\n"
    assert _manifest(project)["tools"][tool]["files"][path]["existed"] is True
    assert _main("--tool", tool, "--project", project, "--verify") == 0
    assert _main("--tool", tool, "--project", project, "--remove") == 0
    assert mine.read_text(encoding="utf-8") == "mine\n"


def test_verify_per_tool_after_a_source_installed_for_another_tool(tmp_path, capsys):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    assert _main("--tool", "all", "--project", project) == 0
    assert _main("--tool", "codex", "--project", project, "--source", src) == 0
    manifest = _manifest(project)
    assert "sources" not in manifest["tools"]["claude"]
    assert manifest["tools"]["codex"]["sources"] == {"lib": ["alpha", "beta", "big"]}
    capsys.readouterr()
    # claude never installed the source, so its copies are not demanded of claude
    assert _main("--tool", "claude", "--project", project, "--verify") == 0
    assert "MISSING" not in capsys.readouterr().out
    assert _main("--tool", "all", "--project", project, "--verify") == 0
    assert _main("--tool", "all", "--project", project, "--prune") == 0
    # removing the one tool that installed the source forgets the source with it
    assert _main("--tool", "codex", "--project", project, "--remove") == 0
    assert "sources" not in _manifest(project)
    shutil.rmtree(src)
    assert _main("--tool", "claude", "--project", project, "--verify") == 0


def test_verify_keeps_a_narrower_per_tool_source_selection(tmp_path, capsys):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    assert _main("--tool", "claude", "--project", project, "--source", src, "--only", "beta") == 0
    assert _main("--tool", "codex", "--project", project, "--source", src) == 0
    manifest = _manifest(project)
    assert manifest["tools"]["claude"]["sources"] == {"lib": ["beta"]}
    assert manifest["tools"]["codex"]["sources"] == {"lib": ["alpha", "beta", "big"]}
    capsys.readouterr()
    assert _main("--tool", "claude", "--project", project, "--verify") == 0
    assert "MISSING" not in capsys.readouterr().out
    assert _main("--tool", "codex", "--project", project, "--verify") == 0


@pytest.mark.parametrize("mode", ["--remove", "--prune"])
@pytest.mark.parametrize("how", ["cli", "recorded"])
def test_a_legacy_manifest_never_deletes_a_hand_placed_source_copy(tmp_path, capsys, mode, how):
    # a pre-records manifest (no files map) came from a kit that could not install a source, so
    # a byte match against a library the user copied in by hand is no proof the kit wrote it
    src = make_source(tmp_path)
    project = tmp_path / "project"
    for name in ("alpha", "beta"):
        shutil.copytree(src / "skills" / name, project / ".claude" / "skills" / name)
    entry = {"prompts": ["grill"], "selection": "only", "terse": False}
    manifest = {"kit_version": "0.0.1", "tools": {"claude": entry}}
    if how == "recorded":
        entry["sources"] = {"lib": ["alpha", "beta"]}
        manifest["sources"] = {"lib": {"path": src.resolve().as_posix()}}
    _write_manifest(project, manifest)
    before = {k: v for k, v in _tree(project).items() if k.startswith(".claude/")}
    argv = ["--tool", "claude", "--project", project, mode]
    if how == "cli":
        argv += ["--source", src]
    assert _main(*argv) == 0
    assert "remove .claude/skills" not in capsys.readouterr().out
    assert {k: v for k, v in _tree(project).items() if k.startswith(".claude/")} == before


def test_install_refuses_a_source_skill_that_collides_with_a_recorded_source(tmp_path, capsys):
    one = make_source(tmp_path / "x", name="lib-one")
    two = make_source(tmp_path / "y", name="lib-two")
    project = tmp_path / "project"
    project.mkdir()
    assert _main("--tool", "claude", "--project", project, "--source", one) == 0
    before = _tree(project)
    # both hold alpha: the second install would write lib-one's path with lib-two's body and
    # then block every later mode, so it is refused before any write
    assert _main("--tool", "claude", "--project", project, "--source", two) == 1
    assert "planned twice" in capsys.readouterr().err
    assert _tree(project) == before
    assert _main("--tool", "claude", "--project", project, "--verify") == 0


def test_install_refuses_a_source_path_that_collides_with_a_core_prompt_under_only(tmp_path,
                                                                                  capsys):
    # source `plan` with skill `change` plans copilot's .github/prompts/plan-change.prompt.md,
    # the core plan-change path; --only change leaves the core prompt out of the selected plan,
    # so the guard must run over the full plan
    src = tmp_path / "plan" / "skills" / "change"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("---\nname: change\ndescription: d\n---\n\nbody\n",
                                  encoding="utf-8")
    project = tmp_path / "project"
    project.mkdir()
    assert _main("--tool", "copilot", "--project", project, "--only", "change",
                 "--source", tmp_path / "plan") == 1
    assert "planned twice" in capsys.readouterr().err
    assert _tree(project) == {}


def test_remove_reports_a_recorded_collision_cleanly(tmp_path, capsys):
    one = make_source(tmp_path / "x", name="lib-one")
    two = make_source(tmp_path / "y", name="lib-two")
    project = tmp_path / "project"
    project.mkdir()
    assert _main("--tool", "claude", "--project", project, "--source", one) == 0
    manifest = _manifest(project)  # a hand edit records a second source with the same skill
    manifest["tools"]["claude"]["sources"]["lib-two"] = ["alpha"]
    manifest["sources"]["lib-two"] = {"path": two.resolve().as_posix()}
    _write_manifest(project, manifest)
    capsys.readouterr()
    assert _main("--tool", "claude", "--project", project, "--remove") == 1
    err = capsys.readouterr().err
    assert err.startswith("error:") and "planned twice" in err


def test_a_relative_recorded_source_path_is_taken_from_the_project(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    src = make_source(project)  # the clone lives inside the project, at project/lib
    assert _main("--tool", "claude", "--project", project, "--source", src) == 0
    manifest = _manifest(project)
    manifest["sources"]["lib"]["path"] = "lib"
    _write_manifest(project, manifest)
    monkeypatch.chdir(tmp_path)  # the working directory holds no lib/
    assert _main("--tool", "claude", "--project", project, "--verify") == 0


def test_verify_detects_an_edited_installed_copy(tmp_path, capsys):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _main("--tool", "all", "--project", project, "--source", src)
    (project / ".cursor" / "rules" / "lib" / "alpha.md").write_text("edited\n", encoding="utf-8")
    capsys.readouterr()
    assert _main("--tool", "all", "--project", project, "--source", src, "--verify") == 1
    out = capsys.readouterr().out
    assert "DRIFTED .cursor/rules/lib/alpha.md" in out
    assert out.count("DRIFTED") == 1


def test_verify_detects_an_upstream_edit_for_every_tool(tmp_path, capsys):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _main("--tool", "all", "--project", project, "--source", src)
    (src / "skills" / "alpha" / "SKILL.md").write_text(
        ALPHA.replace("# Alpha", "# Alpha, revised upstream"), encoding="utf-8")
    capsys.readouterr()
    assert _main("--tool", "all", "--project", project, "--source", src, "--verify") == 1
    out = capsys.readouterr().out
    for path in (".claude/skills/alpha/SKILL.md", ".agents/skills/alpha/SKILL.md",
                 ".cursor/rules/lib/alpha.md", ".github/prompts/lib-alpha.prompt.md",
                 ".windsurf/workflows/lib-alpha.md", ".gemini/commands/lib/alpha.toml"):
        assert f"DRIFTED {path}" in out, path
    assert "DRIFTED .claude/skills/alpha/notes.md" not in out
    # a re-install restores every copy
    assert _main("--tool", "all", "--project", project, "--source", src) == 0
    assert _main("--tool", "all", "--project", project, "--source", src, "--verify") == 0


def test_verify_without_the_flag_checks_the_recorded_source(tmp_path, capsys):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _main("--tool", "all", "--project", project, "--source", src)
    capsys.readouterr()
    assert _main("--tool", "all", "--project", project, "--verify") == 0
    assert "in sync" in capsys.readouterr().out
    (project / ".claude" / "skills" / "alpha" / "notes.md").unlink()
    assert _main("--tool", "all", "--project", project, "--verify") == 1
    assert "MISSING .claude/skills/alpha/notes.md" in capsys.readouterr().out


def test_verify_reports_a_missing_recorded_source(tmp_path, capsys):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _main("--tool", "claude", "--project", project, "--source", src)
    shutil.rmtree(src)
    capsys.readouterr()
    assert _main("--tool", "claude", "--project", project, "--verify") == 1
    out = capsys.readouterr().out
    assert f"SOURCE MISSING lib {src.resolve().as_posix()}" in out
    assert _main("--tool", "claude", "--project", project, "--prune") == 1


def test_install_without_the_flag_keeps_the_recorded_source(tmp_path):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _main("--tool", "claude", "--project", project, "--source", src)
    before = _tree(project)
    assert _main("--tool", "claude", "--project", project) == 0
    assert _tree(project) == before
    assert _main("--tool", "claude", "--project", project, "--verify") == 0


def test_remove_deletes_source_files_and_the_record(tmp_path):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _main("--tool", "all", "--project", project, "--source", src)
    (project / "notes-of-mine.md").write_text("keep me\n", encoding="utf-8")
    assert _main("--tool", "all", "--project", project, "--remove") == 0
    left = _tree(project)
    assert set(left) == {"notes-of-mine.md"}


@pytest.mark.parametrize("break_clone", ["delete", "empty"])
def test_remove_covers_a_source_whose_clone_is_gone_or_broken(tmp_path, capsys, break_clone):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _main("--tool", "claude", "--project", project, "--source", src)
    # gone, or still there but holding no skills: either way the recorded files are removed
    shutil.rmtree(src if break_clone == "delete" else src / "skills")
    capsys.readouterr()
    assert _main("--tool", "claude", "--project", project, "--remove") == 0
    assert "note   source lib" in capsys.readouterr().out
    assert not (project / ".claude" / "skills" / "alpha").exists()
    assert not (project / ".outpost").exists()


def test_prune_removes_a_source_skill_dropped_by_a_narrower_reinstall(tmp_path, capsys):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _main("--tool", "claude", "--project", project, "--source", src)
    _main("--tool", "claude", "--project", project, "--source", src, "--exclude", "alpha")
    capsys.readouterr()
    assert _main("--tool", "claude", "--project", project, "--verify") == 1
    assert "EXTRA   .claude/skills/alpha/SKILL.md" in capsys.readouterr().out
    assert _main("--tool", "claude", "--project", project, "--prune") == 0
    assert not (project / ".claude" / "skills" / "alpha").exists()
    assert (project / ".claude" / "skills" / "beta" / "SKILL.md").is_file()
    assert _main("--tool", "claude", "--project", project, "--verify") == 0


def test_prune_retires_a_skill_the_source_dropped_upstream(tmp_path, capsys):
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _main("--tool", "claude", "--project", project, "--source", src)
    shutil.rmtree(src / "skills" / "beta")
    capsys.readouterr()
    assert _main("--tool", "claude", "--project", project, "--verify") == 1
    assert "LEFTOVER .claude/skills/beta/SKILL.md" in capsys.readouterr().out
    assert _main("--tool", "claude", "--project", project, "--prune") == 0
    assert not (project / ".claude" / "skills" / "beta").exists()
    assert _main("--tool", "claude", "--project", project, "--verify") == 0


def test_two_sources_with_one_name_are_rejected(tmp_path, capsys):
    a = make_source(tmp_path / "one")
    b = make_source(tmp_path / "two")
    project = tmp_path / "project"
    project.mkdir()
    assert _main("--tool", "claude", "--project", project, "--source", a, "--source", b) == 1
    assert "lib" in capsys.readouterr().err
    assert _tree(project) == {}


def test_a_bad_source_fails_before_any_write(tmp_path, capsys):
    project = tmp_path / "project"
    project.mkdir()
    assert _main("--tool", "claude", "--project", project, "--source", tmp_path / "nope") == 1
    assert "not a directory" in capsys.readouterr().err
    assert _tree(project) == {}


def test_manifest_with_a_source_round_trips_through_parse(tmp_path):
    from kit.installers.manifest import parse_manifest
    src = make_source(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _main("--tool", "claude", "--project", project, "--source", src)
    text = (project / ".outpost" / "manifest.json").read_text(encoding="utf-8")
    assert "lib" in parse_manifest(text)["sources"]
    with pytest.raises(ValueError, match="source"):
        parse_manifest(json.dumps({"tools": {}, "sources": {"lib": {"skills": ["a"]}}}))
    with pytest.raises(ValueError, match="source"):
        parse_manifest(json.dumps({"tools": {}, "sources": ["lib"]}))
    with pytest.raises(ValueError, match="'sources' for 'claude'"):
        parse_manifest(json.dumps({"tools": {"claude": {"prompts": [], "sources": ["lib"]}}}))
    with pytest.raises(ValueError, match="'sources' for 'claude'"):
        parse_manifest(json.dumps({"tools": {"claude": {"prompts": [], "sources": {"lib": "a"}}}}))
