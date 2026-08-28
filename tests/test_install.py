"""The installer is safe and idempotent: dry-run writes nothing, a real install is repeatable, and
a user-owned file is never overwritten."""
import dataclasses
import json
import pathlib

import pytest

import install
from kit.catalog import load_catalog

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _tree(root: pathlib.Path) -> dict:
    return {p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_dry_run_writes_nothing(tmp_path, capsys):
    rc = install.main(["--tool", "all", "--project", str(tmp_path), "--dry-run"])
    assert rc == 0
    assert _tree(tmp_path) == {}
    assert "dry-run" in capsys.readouterr().out


def test_install_is_idempotent(tmp_path):
    install.main(["--tool", "all", "--project", str(tmp_path)])
    first = _tree(tmp_path)
    # guard against a vacuous pass: an installer that writes nothing would make
    # first == {} == second and still satisfy the equality below.
    assert first, "install wrote no files"
    assert "CLAUDE.md" in first
    assert ".claude/skills/plan-change/SKILL.md" in first
    install.main(["--tool", "all", "--project", str(tmp_path)])
    assert _tree(tmp_path) == first


def test_install_does_not_overwrite_user_owned_files(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("my own guide", encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "my own guide"
    # but the kit-owned skills are still installed
    assert (tmp_path / ".claude" / "skills" / "plan-change" / "SKILL.md").is_file()


def test_claude_install_writes_secret_deny_rules(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    deny = settings["permissions"]["deny"]
    assert "Read(./.env)" in deny and "Read(./secrets/**)" in deny


def test_terse_installs_output_style(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--terse"])
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert settings["outputStyle"] == "terse"
    assert (tmp_path / ".claude" / "output-styles" / "terse.md").is_file()


def test_reinstall_restores_a_drifted_kit_file(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    skill = tmp_path / ".claude" / "skills" / "plan-change" / "SKILL.md"
    original = skill.read_text(encoding="utf-8")
    skill.write_text("junk that drifted", encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    assert skill.read_text(encoding="utf-8") == original


def test_malformed_existing_settings_aborts_cleanly(tmp_path):
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "settings.json").write_text("{ not json", encoding="utf-8")
    rc = install.main(["--tool", "claude", "--project", str(tmp_path)])
    assert rc == 1
    # fail-closed at plan time: the malformed file is untouched and no skills were written
    assert (claude / "settings.json").read_text(encoding="utf-8") == "{ not json"
    assert not (claude / "skills").exists()


def test_installed_files_use_lf_not_crlf(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    raw = (tmp_path / ".claude" / "skills" / "plan-change" / "SKILL.md").read_bytes()
    assert b"\r\n" not in raw


def test_unknown_tool_is_rejected(tmp_path):
    # argparse rejects an out-of-choices value by exiting non-zero
    with pytest.raises(SystemExit) as e:
        install.main(["--tool", "emacs", "--project", str(tmp_path)])
    assert e.value.code != 0


def test_list_writes_nothing_and_shows_prompts(tmp_path, capsys):
    rc = install.main(["--list", "--project", str(tmp_path)])
    assert rc == 0
    assert _tree(tmp_path) == {}
    out = capsys.readouterr().out
    assert "plan-change" in out and "claude" in out


def test_no_tool_and_no_list_is_an_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        install.main(["--project", str(tmp_path)])
    assert e.value.code != 0
    # bind to the new parser.error path, not the old required=True behavior
    assert "--tool is required" in capsys.readouterr().err


def test_nonexistent_project_is_rejected(tmp_path):
    rc = install.main(["--tool", "claude", "--project", str(tmp_path / "nope")])
    assert rc == 1


def test_overwrite_of_edited_kit_file_warns(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    capsys.readouterr()  # drop the first-install output
    skill = tmp_path / ".claude" / "skills" / "plan-change" / "SKILL.md"
    original = skill.read_text(encoding="utf-8")
    skill.write_text("I hand-edited this skill", encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    out = capsys.readouterr().out
    assert "WARN" in out and "plan-change" in out
    # still restored to the kit version (idempotent restore preserved)
    assert skill.read_text(encoding="utf-8") == original


def test_apply_prints_a_summary_line(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    out = capsys.readouterr().out
    assert "created" in out
    # a second run writes nothing new, so the summary reports unchanged
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    out2 = capsys.readouterr().out
    assert "unchanged" in out2


def test_verify_passes_after_a_clean_install(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 0
    assert "in sync" in capsys.readouterr().out


def test_verify_fails_when_nothing_is_installed(tmp_path):
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 1


def test_verify_detects_a_drifted_kit_file(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    capsys.readouterr()
    (tmp_path / ".claude" / "skills" / "plan-change" / "SKILL.md").write_text(
        "drifted", encoding="utf-8")
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 1
    assert "DRIFTED" in capsys.readouterr().out


def test_verify_writes_nothing(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    # a user-owned CLAUDE.md absent and unwritten; verify must not create the kit tree
    assert not (tmp_path / ".claude").exists()


# Fix 1 (I1): semantic settings compare


def test_verify_passes_after_settings_reformatted(tmp_path, capsys):
    import json as _json
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    settings = tmp_path / ".claude" / "settings.json"
    data = _json.loads(settings.read_text(encoding="utf-8"))
    data["env"] = {"FOO": "bar"}  # unrelated user key
    settings.write_text(_json.dumps(data, indent=4), encoding="utf-8")  # 4-space, not canonical
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 0
    assert "in sync" in capsys.readouterr().out


def test_reinstall_is_noop_after_settings_reformatted(tmp_path):
    import json as _json
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    settings = tmp_path / ".claude" / "settings.json"
    data = _json.loads(settings.read_text(encoding="utf-8"))
    settings.write_text(_json.dumps(data, indent=4), encoding="utf-8")
    before = settings.read_text(encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    # semantically equal, so the installer leaves the user's formatting untouched
    assert settings.read_text(encoding="utf-8") == before


def test_verify_detects_a_removed_deny_rule(tmp_path):
    import json as _json
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    settings = tmp_path / ".claude" / "settings.json"
    data = _json.loads(settings.read_text(encoding="utf-8"))
    data["permissions"]["deny"] = []  # real semantic drift: security rules gone
    settings.write_text(_json.dumps(data, indent=2) + "\n", encoding="utf-8")
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 1


# Fix 2 (I2): precise --verify wording


def test_verify_passes_when_user_owned_guide_is_absent(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    (tmp_path / "CLAUDE.md").unlink()  # user-owned guide removed
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 0  # kit-owned files intact; the guide is optional
    out = capsys.readouterr().out
    assert "CLAUDE.md" in out and "optional" in out


# Fix 3 (M4): mutually exclusive mode flags


def test_verify_and_dry_run_together_are_rejected(tmp_path):
    with pytest.raises(SystemExit) as e:
        install.main(["--tool", "claude", "--project", str(tmp_path), "--verify", "--dry-run"])
    assert e.value.code != 0


# Fix 5 (M3): CRLF-normalized verify is intentional


def test_verify_treats_crlf_kit_file_as_in_sync(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    skill = tmp_path / ".claude" / "skills" / "plan-change" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    skill.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))  # same text, CRLF
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 0  # newline-normalized comparison treats same-text as in sync


def test_verify_treats_crlf_guide_as_not_edited(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    guide = tmp_path / "CLAUDE.md"
    guide.write_bytes(guide.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
    capsys.readouterr()
    assert install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"]) == 0
    assert "EDITED" not in capsys.readouterr().out


def test_verify_reports_a_guide_that_no_longer_decodes_as_edited(tmp_path, capsys):
    # the kit writes UTF-8; a guide holding bytes that do not decode was changed by someone else
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    (tmp_path / "CLAUDE.md").write_bytes(b"\xff\xfe not utf-8\n")
    capsys.readouterr()
    assert install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"]) == 0
    out = capsys.readouterr().out
    assert "EDITED CLAUDE.md" in " ".join(out.split())
    assert "NOTE: 1 guide(s) edited" in out


# Team tailoring: prompt subset selection (Task 4)

CATALOG_NAMES = {p["name"] for p in
                 load_catalog(ROOT / "kit" / "catalog" / "catalog.json").prompts}


def test_resolve_full_when_no_flags():
    assert install.resolve_selection(None, None, CATALOG_NAMES) == ("full", None)


def test_resolve_only_returns_the_named_set():
    label, sel = install.resolve_selection("plan-change,write-tests", None, CATALOG_NAMES)
    assert label == "only" and sel == {"plan-change", "write-tests"}


def test_resolve_exclude_is_the_complement():
    label, sel = install.resolve_selection(None, "plan-change", CATALOG_NAMES)
    assert label == "exclude" and "plan-change" not in sel and "grill" in sel


def test_resolve_unknown_name_raises():
    with pytest.raises(ValueError):
        install.resolve_selection("not-a-prompt", None, CATALOG_NAMES)


def test_resolve_empty_value_raises():
    with pytest.raises(ValueError):
        install.resolve_selection("", None, CATALOG_NAMES)


def test_only_install_writes_just_the_selected_skills(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--only", "plan-change,write-tests"])
    skills = tmp_path / ".claude" / "skills"
    assert sorted(p.name for p in skills.iterdir()) == ["plan-change", "write-tests"]


def test_only_and_exclude_together_are_rejected(tmp_path):
    with pytest.raises(SystemExit) as e:
        install.main(["--tool", "claude", "--project", str(tmp_path),
                      "--only", "plan-change", "--exclude", "grill"])
    assert e.value.code != 0


def test_unknown_prompt_name_fails_loudly(tmp_path, capsys):
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--only", "nope"])
    assert rc == 1
    assert "nope" in capsys.readouterr().err


# Team tailoring: the install manifest (Task 5)

def _manifest(tmp_path):
    return json.loads((tmp_path / ".outpost" / "manifest.json").read_text(encoding="utf-8"))


def test_full_install_writes_a_manifest(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    man = _manifest(tmp_path)
    assert man["tools"]["claude"]["selection"] == "full"
    assert "plan-change" in man["tools"]["claude"]["prompts"]


def test_full_install_manifest_matches_installed_skills_only(tmp_path):
    # a full install must record only the prompts actually written to disk, not some larger set
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    man = _manifest(tmp_path)
    on_disk = {p.parent.name for p in (tmp_path / ".claude" / "skills").glob("*/SKILL.md")}
    assert set(man["tools"]["claude"]["prompts"]) == on_disk


def test_only_install_records_the_subset(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--only", "plan-change,write-tests"])
    entry = _manifest(tmp_path)["tools"]["claude"]
    assert entry["selection"] == "only"
    assert entry["prompts"] == ["plan-change", "write-tests"]
    assert entry["terse"] is False
    # every path this install wrote is recorded as kit-created, with a hash of what it wrote
    rec = entry["files"][".claude/skills/plan-change/SKILL.md"]
    assert rec["existed"] is False
    assert rec["kit_hash"].startswith("sha256:")


def test_prune_of_a_deselected_orphan_ends_the_kit_ownership_claim(tmp_path):
    # a de-selected orphan that prune deletes must also drop its manifest record, the same way a
    # retired file does: otherwise a file the user creates at that path later is claimed by the
    # stale record and overwritten by the next full reinstall
    install.main(["--tool", "codex", "--project", str(tmp_path)])  # full: grill written + recorded
    orphan = tmp_path / ".agents" / "prompts" / "grill.md"
    assert orphan.exists()
    install.main(["--tool", "codex", "--project", str(tmp_path), "--only", "plan-change"])  # narrow
    install.main(["--tool", "codex", "--project", str(tmp_path), "--prune"])  # grill now orphaned
    assert not orphan.exists()  # pruned
    files = _manifest(tmp_path)["tools"]["codex"]["files"]
    assert ".agents/prompts/grill.md" not in files  # record dropped, no lingering claim

    orphan.write_text("my own grill notes", encoding="utf-8")
    install.main(["--tool", "codex", "--project", str(tmp_path)])  # full reinstall
    assert orphan.read_text(encoding="utf-8") == "my own grill notes"


def test_verify_with_corrupt_settings_fails_clean_not_traceback(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    (tmp_path / ".claude" / "settings.json").write_text("{ not json", encoding="utf-8")
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    out = capsys.readouterr()
    assert rc == 1
    assert "error:" in (out.out + out.err)


def test_remove_with_corrupt_settings_still_deletes_prompts(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    skill = tmp_path / ".claude" / "skills" / "grill" / "SKILL.md"
    assert skill.exists()
    (tmp_path / ".claude" / "settings.json").write_text("{ not json", encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    assert not skill.exists()  # prompt cleanup is not blocked by the corrupt settings file


def test_installing_a_second_tool_accumulates_in_the_manifest(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--only", "plan-change"])
    install.main(["--tool", "codex", "--project", str(tmp_path), "--only", "grill"])
    man = _manifest(tmp_path)
    assert set(man["tools"]) == {"claude", "codex"}


def test_tool_all_records_every_tool(tmp_path):
    install.main(["--tool", "all", "--project", str(tmp_path), "--only", "plan-change"])
    man = _manifest(tmp_path)
    assert set(man["tools"]) == {"claude", "codex", "cursor", "copilot", "windsurf", "gemini"}


def test_manifest_install_is_idempotent(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    first = _tree(tmp_path)
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    assert _tree(tmp_path) == first


def test_dry_run_shows_manifest_and_writes_nothing(tmp_path, capsys):
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--dry-run"])
    assert rc == 0
    assert _tree(tmp_path) == {}
    assert ".outpost/manifest.json" in capsys.readouterr().out


# Team tailoring: manifest-aware verify (Task 6)

def test_verify_passes_after_a_subset_install(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--only", "plan-change,write-tests"])
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "in sync" in out
    assert "MISSING" not in out  # excluded prompts are not flagged missing


def test_verify_full_pack_when_no_manifest(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    (tmp_path / ".outpost" / "manifest.json").unlink()
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 0  # full pack present, so the fallback still verifies clean


def test_exclude_install_end_to_end(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--exclude", "plan-change"])
    skills = {p.name for p in (tmp_path / ".claude" / "skills").iterdir()}
    assert "plan-change" not in skills and "write-tests" in skills
    assert _manifest(tmp_path)["tools"]["claude"]["selection"] == "exclude"


def test_exclude_every_prompt_installs_no_skills(tmp_path):
    all_names = ",".join(CATALOG_NAMES)
    install.main(["--tool", "claude", "--project", str(tmp_path), "--exclude", all_names])
    assert not (tmp_path / ".claude" / "skills").exists()
    assert _manifest(tmp_path)["tools"]["claude"]["prompts"] == []


def test_tool_all_then_single_tool_verify(tmp_path, capsys):
    install.main(["--tool", "all", "--project", str(tmp_path), "--only", "plan-change"])
    capsys.readouterr()
    rc = install.main(["--tool", "codex", "--project", str(tmp_path), "--verify"])
    assert rc == 0
    assert "MISSING" not in capsys.readouterr().out


def test_verify_detects_drift_within_a_subset(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--only", "plan-change,write-tests"])
    (tmp_path / ".claude" / "skills" / "plan-change" / "SKILL.md").unlink()
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 1
    assert "MISSING" in capsys.readouterr().out


def test_manifest_file_uses_lf_not_crlf(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    raw = (tmp_path / ".outpost" / "manifest.json").read_bytes()
    assert b"\r\n" not in raw


def test_install_aborts_cleanly_on_malformed_manifest(tmp_path, capsys):
    mdir = tmp_path / ".outpost"
    mdir.mkdir()
    (mdir / "manifest.json").write_text("{ not json", encoding="utf-8")
    rc = install.main(["--tool", "claude", "--project", str(tmp_path)])
    assert rc == 1
    assert "error" in capsys.readouterr().err
    # fail-closed: the malformed file is untouched and no skills were written
    assert (mdir / "manifest.json").read_text(encoding="utf-8") == "{ not json"
    assert not (tmp_path / ".claude" / "skills").exists()


def test_verify_fails_loudly_on_malformed_manifest(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    (tmp_path / ".outpost" / "manifest.json").write_text("{ not json", encoding="utf-8")
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 1
    assert "error" in capsys.readouterr().err  # not a phantom DRIFT report


def test_verify_fails_on_wrong_shaped_manifest(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    (tmp_path / ".outpost" / "manifest.json").write_text('{"tools": ["nope"]}', encoding="utf-8")
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 1  # a hand-edited bad shape fails loudly, not an AttributeError crash


# Verify flags orphan prompt files left by narrowing an install (v0.11.1)

def test_verify_flags_orphans_after_narrowing(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])  # full pack: all 15 skills
    install.main(["--tool", "claude", "--project", str(tmp_path), "--exclude", "grill,premortem"])
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    out = capsys.readouterr().out
    assert rc == 1  # orphans are drift: verify is a gate and fails on extras
    assert "EXTRA" in out and "grill" in out and "premortem" in out
    assert "in sync" not in out  # do not claim a clean sync when extras exist
    # the de-selected skill files are indeed still on disk
    assert (tmp_path / ".claude" / "skills" / "grill" / "SKILL.md").is_file()


def test_verify_note_does_not_claim_pass_when_drift_and_orphans_coexist(tmp_path, capsys):
    # grill catch: a missing selected prompt AND orphans must not print a contradictory "passes"
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    install.main(["--tool", "claude", "--project", str(tmp_path), "--exclude", "grill,premortem"])
    (tmp_path / ".claude" / "skills" / "plan-change" / "SKILL.md").unlink()  # break a selected one
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "MISSING" in out and "EXTRA" in out
    assert "passes" not in out and "in sync" not in out


def test_verify_no_orphans_on_clean_subset_install(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--only", "plan-change,write-tests"])
    capsys.readouterr()
    install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert "EXTRA" not in capsys.readouterr().out  # nothing was narrowed away


def test_verify_no_orphans_on_full_install(tmp_path, capsys):
    install.main(["--tool", "all", "--project", str(tmp_path)])
    capsys.readouterr()
    install.main(["--tool", "all", "--project", str(tmp_path), "--verify"])
    assert "EXTRA" not in capsys.readouterr().out


# Prune removes orphan prompt files left by narrowing an install (v0.12.0)

def test_prune_removes_orphans_and_makes_verify_pass(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])  # full pack
    install.main(["--tool", "claude", "--project", str(tmp_path), "--exclude", "grill,premortem"])
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--prune"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "remove" in out.lower() and "grill" in out and "premortem" in out
    # the orphan skill dirs are gone, the selected ones remain
    assert not (tmp_path / ".claude" / "skills" / "grill").exists()
    assert not (tmp_path / ".claude" / "skills" / "premortem").exists()
    assert (tmp_path / ".claude" / "skills" / "plan-change" / "SKILL.md").is_file()
    # disk now matches the manifest, so verify passes
    assert install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"]) == 0


def test_prune_keeps_user_owned_and_merge_files(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    install.main(["--tool", "claude", "--project", str(tmp_path), "--exclude", "grill"])
    install.main(["--tool", "claude", "--project", str(tmp_path), "--prune"])
    assert (tmp_path / "CLAUDE.md").is_file()
    assert (tmp_path / ".claude" / "settings.json").is_file()
    assert (tmp_path / ".outpost" / "manifest.json").is_file()


def test_prune_skips_a_modified_orphan(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    install.main(["--tool", "claude", "--project", str(tmp_path), "--exclude", "grill"])
    skill = tmp_path / ".claude" / "skills" / "grill" / "SKILL.md"
    skill.write_text("my own customized grill", encoding="utf-8")  # hand-edited orphan
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--prune"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "skip" in out.lower() and "grill" in out
    # the user's edit is preserved, not silently deleted
    assert skill.read_text(encoding="utf-8") == "my own customized grill"
    # and its ownership record must survive: the pop fires only on a real delete, so a skipped
    # edited orphan keeps its record (locking the asymmetry against a regression that pops on skip)
    assert ".claude/skills/grill/SKILL.md" in _manifest(tmp_path)["tools"]["claude"]["files"]


def test_prune_keeps_a_byte_identical_file_at_a_never_recorded_path(tmp_path):
    # the file was never part of any install this project ran (excluded from the very first
    # install), so it has no manifest record at all: not existed=True, no record whatsoever.
    # A byte match alone must never authorize deletion (matching bytes never prove
    # kit ownership); "no record" is not the same as "the kit created it".
    skill = tmp_path / ".claude" / "skills" / "grill" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    kit_content = (ROOT / "prompts" / "core" / "grill.md").read_text(encoding="utf-8")
    skill.write_text(kit_content, encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path), "--exclude", "grill"])
    assert ".claude/skills/grill/SKILL.md" not in _manifest(tmp_path)["tools"]["claude"]["files"]
    before = _tree(tmp_path)
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--prune"])
    assert rc == 0
    assert skill.read_text(encoding="utf-8") == kit_content  # never deleted
    assert _tree(tmp_path) == before  # nothing else in the tree touched either


def test_remove_leaves_a_corrupt_settings_file_untouched(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    settings = tmp_path / ".claude" / "settings.json"
    settings.write_text("{ not json", encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    # remove deletes the prompt files but must never rewrite or delete a settings file it cannot
    # parse: a corrupt file is the user's to fix, left exactly as found
    assert settings.read_text(encoding="utf-8") == "{ not json"


def test_prune_removes_nothing_on_a_full_install(tmp_path, capsys):
    install.main(["--tool", "all", "--project", str(tmp_path)])
    capsys.readouterr()
    rc = install.main(["--tool", "all", "--project", str(tmp_path), "--prune"])
    assert rc == 0
    assert "nothing to prune" in capsys.readouterr().out.lower()
    assert (tmp_path / ".claude" / "skills" / "grill" / "SKILL.md").is_file()


def test_prune_writes_nothing_else_and_is_safe_without_manifest(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    (tmp_path / ".outpost" / "manifest.json").unlink()  # no record -> full-pack assumption
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--prune"])
    assert rc == 0
    assert (tmp_path / ".claude" / "skills" / "grill" / "SKILL.md").is_file()  # nothing removed


def test_prune_and_verify_together_are_rejected(tmp_path):
    with pytest.raises(SystemExit) as e:
        install.main(["--tool", "claude", "--project", str(tmp_path), "--prune", "--verify"])
    assert e.value.code != 0


# Manifest prompt-name validation: a hand-edited manifest naming an unknown prompt is rejected,
# so a typo can never drive a wrong verify or a destructive prune (v0.12.1)

def _write_manifest(tmp_path, tools):
    (tmp_path / ".outpost").mkdir(exist_ok=True)
    (tmp_path / ".outpost" / "manifest.json").write_text(
        json.dumps({"kit_version": "0.0.0", "tools": tools}), encoding="utf-8")


def test_verify_rejects_a_manifest_naming_an_unknown_prompt(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    _write_manifest(tmp_path, {"claude": {"selection": "only", "prompts": ["plan-change", "Bogus-Name"]}})
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 1
    assert "Bogus-Name" in capsys.readouterr().err


def test_prune_refuses_and_preserves_files_on_a_typoed_manifest(tmp_path, capsys):
    # the grill edge: a typo'd name (Plan-Change) would make prune delete the real plan-change.
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    _write_manifest(tmp_path, {"claude": {"selection": "only", "prompts": ["Plan-Change", "write-tests"]}})
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--prune"])
    assert rc == 1
    assert "Plan-Change" in capsys.readouterr().err
    # the real prompt is untouched: validation runs before any deletion
    assert (tmp_path / ".claude" / "skills" / "plan-change" / "SKILL.md").is_file()


def test_verify_accepts_a_manifest_with_only_real_prompt_names(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--only", "plan-change,write-tests"])
    assert install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"]) == 0


# Full uninstall: --remove backs a tool's kit footprint out of a target (v0.13.0)

def test_remove_deletes_all_kit_prompt_files(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    assert rc == 0
    assert not (tmp_path / ".claude" / "skills").exists()  # all skill dirs gone


def test_remove_deletes_an_unmodified_guide(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])  # CLAUDE.md == template
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    assert not (tmp_path / "CLAUDE.md").exists()


def test_remove_keeps_an_edited_guide(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    (tmp_path / "CLAUDE.md").write_text("my own edits", encoding="utf-8")
    capsys.readouterr()
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    assert (tmp_path / "CLAUDE.md").read_text(encoding="utf-8") == "my own edits"
    assert "skip" in capsys.readouterr().out.lower()


def test_remove_keeps_an_edited_kit_prompt_file(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    skill = tmp_path / ".claude" / "skills" / "grill" / "SKILL.md"
    skill.write_text("customized", encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    assert skill.read_text(encoding="utf-8") == "customized"  # edits never silently deleted


def test_remove_unmerges_only_the_kit_deny_rules(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    settings = tmp_path / ".claude" / "settings.json"
    data = json.loads(settings.read_text(encoding="utf-8"))
    data["model"] = "opus"  # a user key
    data["permissions"]["deny"].append("Read(./mine)")  # a user deny rule
    settings.write_text(json.dumps(data), encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    after = json.loads(settings.read_text(encoding="utf-8"))
    assert after["model"] == "opus"  # user key preserved
    assert "Read(./mine)" in after["permissions"]["deny"]  # user rule preserved
    assert "Read(./.env)" not in after.get("permissions", {}).get("deny", [])  # kit rule gone


def test_remove_deletes_a_settings_file_that_was_only_kit(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])  # settings = just kit deny rules
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    assert not (tmp_path / ".claude" / "settings.json").exists()  # nothing of the user's was in it


def test_remove_drops_the_tool_from_the_manifest(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    install.main(["--tool", "codex", "--project", str(tmp_path)])
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    man = json.loads((tmp_path / ".outpost" / "manifest.json").read_text(encoding="utf-8"))
    assert set(man["tools"]) == {"codex"}


def test_remove_deletes_the_manifest_when_the_last_tool_goes(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    assert not (tmp_path / ".outpost").exists()


def test_remove_all_tools(tmp_path):
    install.main(["--tool", "all", "--project", str(tmp_path)])
    install.main(["--tool", "all", "--project", str(tmp_path), "--remove"])
    assert not (tmp_path / ".claude" / "skills").exists()
    assert not (tmp_path / ".agents" / "prompts").exists()
    assert not (tmp_path / ".cursor" / "rules" / "outpost").exists()
    assert not (tmp_path / ".github" / "prompts").exists()


def test_remove_on_an_empty_project_is_safe(tmp_path):
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    assert rc == 0  # nothing to remove, no crash


def test_remove_all_keeps_a_byte_identical_file_for_a_never_installed_tool(tmp_path):
    # codex is never installed in this project; claude is the only tool ever installed, so
    # codex's manifest entry does not exist at all (not even a legacy, files-less one). A user
    # file at a codex-shipped path, byte-identical to what codex would render, must survive
    # --remove --tool all: no manifest entry at all is no proof of authorship.
    reference = tmp_path / "_codex_reference"
    reference.mkdir()
    install.main(["--tool", "codex", "--project", str(reference)])
    kit_content = (reference / ".agents" / "prompts" / "grill.md").read_text(encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    mine = tmp_path / ".agents" / "prompts" / "grill.md"
    mine.parent.mkdir(parents=True)
    mine.write_text(kit_content, encoding="utf-8")
    assert "codex" not in _manifest(tmp_path).get("tools", {})
    rc = install.main(["--tool", "all", "--project", str(tmp_path), "--remove"])
    assert rc == 0
    assert mine.read_text(encoding="utf-8") == kit_content


def test_remove_and_verify_together_are_rejected(tmp_path):
    with pytest.raises(SystemExit) as e:
        install.main(["--tool", "claude", "--project", str(tmp_path), "--remove", "--verify"])
    assert e.value.code != 0


def test_remove_leaves_a_settings_file_that_held_no_kit_rules(tmp_path):
    # grill fix: a settings.json the kit never wrote into must survive --remove untouched
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "settings.json").write_text('{"model": "opus"}', encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    assert (claude / "settings.json").read_text(encoding="utf-8") == '{"model": "opus"}'


def test_remove_keeps_a_preexisting_settings_file_byte_equal_to_the_kits_merge(tmp_path):
    # reviewer repro: a user settings file byte-equal to the kit's merged output pre-exists, so
    # the kit's merge was a no-op; --remove must not delete the user's file
    from kit.installers.settings import merged_text as settings_merged_text
    claude = tmp_path / ".claude"
    claude.mkdir()
    settings = claude / "settings.json"
    settings.write_text(settings_merged_text(None), encoding="utf-8")
    before = settings.read_text(encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    rec = _manifest(tmp_path)["tools"]["claude"]["files"][".claude/settings.json"]
    assert rec["existed"] is True  # the manifest knows the settings file pre-existed the kit
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    assert settings.read_text(encoding="utf-8") == before


def test_unmerge_settings_keeps_a_file_for_a_never_installed_tool(tmp_path):
    project = tmp_path
    settings_path = project / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    # content shaped like the kit's own deny-only merge, so unmerged_text would return None
    # (nothing of the user's left) if this were treated as the kit's to reclaim
    settings_path.write_text(
        '{"permissions": {"deny": ["Read(./.env)", "Read(./.env.*)"]}}\n', encoding="utf-8")

    manifest = {"tools": {}}  # claude was never installed in this project: no entry at all

    results = install.unmerge_kit_settings(project, ["claude"], manifest, args_terse=False)

    assert results == [(".claude/settings.json", "skipped")] or (
        settings_path.exists()
        and settings_path.read_text(encoding="utf-8")
        == '{"permissions": {"deny": ["Read(./.env)", "Read(./.env.*)"]}}\n'
    )


def test_reinstall_after_remove_restores_cleanly(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    first = _tree(tmp_path)
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    assert _tree(tmp_path) == first  # uninstall then reinstall is a round trip
    assert install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"]) == 0


# --verify warns when the install was recorded at an older kit version (v0.13.1)

def _set_manifest_version(tmp_path, version):
    path = tmp_path / ".outpost" / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["kit_version"] = version
    path.write_text(json.dumps(data), encoding="utf-8")


def test_verify_warns_when_install_is_older(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    _set_manifest_version(tmp_path, "0.0.1")  # pretend it was installed by a much older kit
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    out = capsys.readouterr().out
    assert rc == 0  # the files are in sync; only the recorded version is stale
    assert "0.0.1" in out and "older" in out and "in sync" in out


def test_verify_warns_when_install_is_newer(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    _set_manifest_version(tmp_path, "99.0.0")
    capsys.readouterr()
    install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert "newer" in capsys.readouterr().out


def test_verify_no_version_note_when_current(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])  # manifest version == current
    capsys.readouterr()
    install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    out = capsys.readouterr().out
    assert "older" not in out and "newer" not in out and "re-install to refresh" not in out


# The terse output style is tracked in the manifest so verify/prune/remove handle it (v0.13.2)

def test_install_records_terse_in_the_manifest(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--terse"])
    assert _manifest(tmp_path)["tools"]["claude"]["terse"] is True
    install.main(["--tool", "claude", "--project", str(tmp_path)])  # re-install without terse
    assert _manifest(tmp_path)["tools"]["claude"]["terse"] is False


def test_verify_sees_terse_md_from_the_manifest(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--terse"])
    (tmp_path / ".claude" / "output-styles" / "terse.md").unlink()  # the recorded style file is gone
    # verify without re-passing --terse must still know the install was terse and flag the loss
    assert install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"]) == 1


def test_remove_terse_install_clears_style_and_outputstyle(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--terse"])
    assert (tmp_path / ".claude" / "output-styles" / "terse.md").is_file()
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])  # no --terse needed
    assert not (tmp_path / ".claude" / "output-styles" / "terse.md").exists()
    # no dangling outputStyle pointing at the deleted file
    settings = tmp_path / ".claude" / "settings.json"
    if settings.exists():
        assert json.loads(settings.read_text(encoding="utf-8")).get("outputStyle") != "terse"
    else:
        pass  # file removed entirely is also fine (nothing of the user's remained)


def test_remove_strips_only_a_terse_outputstyle_not_a_user_one(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    settings = tmp_path / ".claude" / "settings.json"
    data = json.loads(settings.read_text(encoding="utf-8"))
    data["outputStyle"] = "my-custom-style"  # a user style, not the kit's "terse"
    settings.write_text(json.dumps(data), encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    after = json.loads(settings.read_text(encoding="utf-8"))
    assert after["outputStyle"] == "my-custom-style"  # a non-terse user style is preserved


def test_remove_leaves_a_standalone_terse_outputstyle_the_kit_never_wrote(tmp_path):
    # grill fix: a settings file with only outputStyle:terse and no kit deny rules is not ours
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "settings.json").write_text('{"outputStyle": "terse"}', encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    assert (claude / "settings.json").read_text(encoding="utf-8") == '{"outputStyle": "terse"}'


# F2: ownership is proved by the manifest, not by a reserved path or matching
# bytes. The three reproduced data-loss probes become regression tests.

def test_first_install_preserves_a_preexisting_file_at_a_kit_path(tmp_path, capsys):
    # probe (a): a user file already at a kit-reserved path is the user's, not the kit's to replace
    prompts_dir = tmp_path / ".github" / "prompts"
    prompts_dir.mkdir(parents=True)
    mine = prompts_dir / "plan-change.prompt.md"
    mine.write_text("my own prompt", encoding="utf-8")
    rc = install.main(["--tool", "copilot", "--project", str(tmp_path)])
    assert rc == 0
    assert mine.read_text(encoding="utf-8") == "my own prompt"  # never silently overwritten
    out = capsys.readouterr().out
    assert "skip" in out and "plan-change.prompt.md" in out  # the skip is named, not silent
    # the skip is recorded: the manifest knows this path pre-existed and is not the kit's
    rec = _manifest(tmp_path)["tools"]["copilot"]["files"][".github/prompts/plan-change.prompt.md"]
    assert rec["existed"] is True and rec["pre_hash"]


def test_preexisting_file_survives_a_reinstall_too(tmp_path):
    prompts_dir = tmp_path / ".github" / "prompts"
    prompts_dir.mkdir(parents=True)
    mine = prompts_dir / "plan-change.prompt.md"
    mine.write_text("my own prompt", encoding="utf-8")
    install.main(["--tool", "copilot", "--project", str(tmp_path)])
    install.main(["--tool", "copilot", "--project", str(tmp_path)])
    assert mine.read_text(encoding="utf-8") == "my own prompt"


def test_remove_keeps_a_preexisting_guide_identical_to_the_template(tmp_path):
    # probe (b): a user AGENTS.md byte-identical to the kit template is not the kit's to delete
    template = (ROOT / "templates" / "AGENTS.md").read_text(encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(template, encoding="utf-8")
    install.main(["--tool", "codex", "--project", str(tmp_path)])
    install.main(["--tool", "codex", "--project", str(tmp_path), "--remove"])
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == template


def test_remove_keeps_a_preexisting_prompt_file_even_when_byte_identical(tmp_path):
    # the write-mode twin of the guide probe: matching bytes alone never prove kit ownership
    kit_content = (ROOT / "prompts" / "core" / "plan-change.md").read_text(encoding="utf-8")
    prompts_dir = tmp_path / ".github" / "prompts"
    prompts_dir.mkdir(parents=True)
    mine = prompts_dir / "plan-change.prompt.md"
    mine.write_text(kit_content, encoding="utf-8")
    install.main(["--tool", "copilot", "--project", str(tmp_path)])
    install.main(["--tool", "copilot", "--project", str(tmp_path), "--remove"])
    assert mine.read_text(encoding="utf-8") == kit_content


def test_remove_keeps_a_byte_identical_file_at_a_never_recorded_path(tmp_path):
    # same scenario as test_prune_keeps_a_byte_identical_file_at_a_never_recorded_path, for
    # --remove: a file at a path excluded from every install this project ran has no manifest
    # record, so --remove must never delete it on a byte match alone either.
    skill = tmp_path / ".claude" / "skills" / "grill" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    kit_content = (ROOT / "prompts" / "core" / "grill.md").read_text(encoding="utf-8")
    skill.write_text(kit_content, encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path), "--exclude", "grill"])
    assert ".claude/skills/grill/SKILL.md" not in _manifest(tmp_path)["tools"]["claude"]["files"]
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    assert rc == 0
    assert skill.read_text(encoding="utf-8") == kit_content  # never deleted


def test_verify_treats_a_recorded_preexisting_file_as_user_owned(tmp_path, capsys):
    prompts_dir = tmp_path / ".github" / "prompts"
    prompts_dir.mkdir(parents=True)
    (prompts_dir / "plan-change.prompt.md").write_text("my own prompt", encoding="utf-8")
    install.main(["--tool", "copilot", "--project", str(tmp_path)])
    capsys.readouterr()
    rc = install.main(["--tool", "copilot", "--project", str(tmp_path), "--verify"])
    assert rc == 0  # the recorded skip is not drift; the path is the user's
    assert "DRIFTED" not in capsys.readouterr().out


def test_removal_falls_back_to_byte_match_for_a_legacy_manifest(tmp_path):
    # a manifest written by a pre-records kit has no files field; removal still works by the
    # old rule (delete only what byte-matches the kit version)
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    mpath = tmp_path / ".outpost" / "manifest.json"
    data = json.loads(mpath.read_text(encoding="utf-8"))
    data["tools"]["claude"].pop("files", None)
    mpath.write_text(json.dumps(data), encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path), "--remove"])
    assert not (tmp_path / ".claude" / "skills").exists()


def test_reinstall_still_restores_a_drifted_kit_created_file(tmp_path):
    # the manifest proves the kit created it, so a reinstall may and must restore it
    install.main(["--tool", "copilot", "--project", str(tmp_path)])
    target = tmp_path / ".github" / "prompts" / "plan-change.prompt.md"
    original = target.read_text(encoding="utf-8")
    target.write_text("drifted", encoding="utf-8")
    install.main(["--tool", "copilot", "--project", str(tmp_path)])
    assert target.read_text(encoding="utf-8") == original


# F32: a reinstall without --terse withdraws the terse choice completely,
# and --verify flags any leftover terse state as drift

def test_plain_reinstall_clears_stale_terse_state(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--terse"])
    install.main(["--tool", "claude", "--project", str(tmp_path)])  # withdraw terse
    assert not (tmp_path / ".claude" / "output-styles" / "terse.md").exists()
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "outputStyle" not in settings
    assert install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"]) == 0


def test_verify_flags_a_stale_terse_leftover_as_drifted(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--terse"])
    # simulate a reinstall by a pre-fix kit: the manifest records terse false, the state stays
    mpath = tmp_path / ".outpost" / "manifest.json"
    data = json.loads(mpath.read_text(encoding="utf-8"))
    data["tools"]["claude"]["terse"] = False
    mpath.write_text(json.dumps(data), encoding="utf-8")
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "DRIFTED" in out and "terse" in out


def test_plain_reinstall_keeps_an_edited_terse_style(tmp_path, capsys):
    # an edited style file may be the user's work: the withdrawal skips it and says so
    install.main(["--tool", "claude", "--project", str(tmp_path), "--terse"])
    style = tmp_path / ".claude" / "output-styles" / "terse.md"
    style.write_text("my own tweaks", encoding="utf-8")
    capsys.readouterr()
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    assert style.read_text(encoding="utf-8") == "my own tweaks"
    assert "skip" in capsys.readouterr().out.lower()


def test_plain_reinstall_keeps_a_user_terse_style_byte_identical_to_the_kits(tmp_path):
    # ownership is the manifest record, never a byte match: the kit never installed terse here,
    # so a hand-placed style file with the kit's own bytes (and the user's key) is not the kit's
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    styles = tmp_path / ".claude" / "output-styles"
    styles.mkdir(parents=True)
    (styles / "terse.md").write_text(install.TERSE_OUTPUT_STYLE, encoding="utf-8")
    settings = tmp_path / ".claude" / "settings.json"
    data = json.loads(settings.read_text(encoding="utf-8"))
    data["outputStyle"] = "terse"
    settings.write_text(json.dumps(data), encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    assert (styles / "terse.md").read_text(encoding="utf-8") == install.TERSE_OUTPUT_STYLE
    after = json.loads(settings.read_text(encoding="utf-8"))
    assert after["outputStyle"] == "terse"


def test_stale_terse_check_names_a_malformed_settings_file_on_stderr(tmp_path, capsys):
    # the skip stands (a malformed file is not this cleanup's to judge), but it is named, not silent
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text("{ not json", encoding="utf-8")
    stale = install.stale_terse_state(tmp_path, True)
    assert ("clear", install.CLAUDE_SETTINGS_PATH) not in stale  # still skipped, never rewritten
    err = capsys.readouterr().err
    assert "warning" in err and "settings.json" in err


# A lingering outputStyle key whose style file is already gone is drift too: --verify flags it
# and a plain reinstall retries the clear (the manifest's kit-created style record is the proof)

def _withdraw_terse_but_leave_the_key(tmp_path):
    """Simulate a pre-fix withdrawal: the style file went, the settings key stayed, and the
    manifest records the install as non-terse (the kit-created file record remains)."""
    (tmp_path / ".claude" / "output-styles" / "terse.md").unlink()
    mpath = tmp_path / ".outpost" / "manifest.json"
    data = json.loads(mpath.read_text(encoding="utf-8"))
    data["tools"]["claude"]["terse"] = False
    mpath.write_text(json.dumps(data), encoding="utf-8")


def test_verify_flags_a_lingering_outputstyle_key_when_the_style_file_is_gone(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--terse"])
    _withdraw_terse_but_leave_the_key(tmp_path)
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    assert rc == 1  # a lingering kit-set key restyles the agent: that is drift, file or no file
    out = capsys.readouterr().out
    assert "DRIFTED" in out and "outputStyle" in out


def test_plain_reinstall_retries_a_lingering_outputstyle_clear(tmp_path):
    install.main(["--tool", "claude", "--project", str(tmp_path), "--terse"])
    _withdraw_terse_but_leave_the_key(tmp_path)
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "outputStyle" not in settings  # the missed clear is retried, not abandoned
    assert install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"]) == 0


def test_plain_reinstall_leaves_terse_state_the_kit_never_set(tmp_path):
    # no --terse was ever recorded, so the terse style and key are the user's, not stale state
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    styles = tmp_path / ".claude" / "output-styles"
    styles.mkdir(parents=True)
    (styles / "terse.md").write_text("my own style", encoding="utf-8")
    settings = tmp_path / ".claude" / "settings.json"
    data = json.loads(settings.read_text(encoding="utf-8"))
    data["outputStyle"] = "terse"
    settings.write_text(json.dumps(data), encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    assert (styles / "terse.md").read_text(encoding="utf-8") == "my own style"
    after = json.loads(settings.read_text(encoding="utf-8"))
    assert after["outputStyle"] == "terse"


def test_completed_withdrawal_releases_style_ownership(tmp_path):
    # residual (recorded on PR 101): a completed withdrawal left the manifest's style-path record
    # in place, so the kit's ownership claim outlived the withdrawal. A user who later hand-adopts
    # terse with kit-identical bytes and their own key then has both seized, and reported wrongly,
    # by the very next plain reinstall.
    install.main(["--tool", "claude", "--project", str(tmp_path), "--terse"])
    install.main(["--tool", "claude", "--project", str(tmp_path)])  # withdraw terse, full clean

    styles = tmp_path / ".claude" / "output-styles"
    styles.mkdir(parents=True)
    (styles / "terse.md").write_text(install.TERSE_OUTPUT_STYLE, encoding="utf-8")
    settings = tmp_path / ".claude" / "settings.json"
    data = json.loads(settings.read_text(encoding="utf-8"))
    data["outputStyle"] = "terse"
    settings.write_text(json.dumps(data), encoding="utf-8")

    install.main(["--tool", "claude", "--project", str(tmp_path)])  # a later plain reinstall

    assert (styles / "terse.md").read_text(encoding="utf-8") == install.TERSE_OUTPUT_STYLE
    after = json.loads(settings.read_text(encoding="utf-8"))
    assert after["outputStyle"] == "terse"
    assert install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"]) == 0


def _plant_retired_converge(tmp_path, kit_hash="recorded"):
    """Reproduce an install from a kit version that still shipped converge to Codex: the file on
    disk with the kit's own content, and a manifest record proving the kit created it.
    kit_hash="recorded" (the common case for a post-hash-fix install) records the real hash of
    the planted content; "missing" reproduces a pre-fix manifest with no kit_hash at all; "wrong"
    records a hash that will not match, standing in for a record whose content later changed."""
    install.main(["--tool", "codex", "--project", str(tmp_path)])
    content = (ROOT / "prompts" / "core" / "converge.md").read_text(encoding="utf-8")
    stale = tmp_path / ".agents" / "prompts" / "converge.md"
    stale.write_bytes(content.encode("utf-8"))  # byte-exact with what the kit itself would write
    mpath = tmp_path / ".outpost" / "manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    record = {"existed": False}
    if kit_hash == "recorded":
        record["kit_hash"] = install._hash_str(content)
    elif kit_hash == "wrong":
        record["kit_hash"] = install._hash_str(content + "\nnot this")
    manifest["tools"]["codex"]["files"][".agents/prompts/converge.md"] = record
    manifest["tools"]["codex"]["prompts"] = sorted(
        set(manifest["tools"]["codex"]["prompts"]) | {"converge"})
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    return stale


def test_verify_flags_a_retired_kit_file_as_leftover(tmp_path, capsys):
    # a host-retired prompt file from an earlier kit is not in the current plan, so plan-derived
    # verify saw nothing; the manifest record must surface it instead of reporting in sync
    stale = _plant_retired_converge(tmp_path)
    capsys.readouterr()
    rc = install.main(["--tool", "codex", "--project", str(tmp_path), "--verify"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "LEFTOVER" in out and ".agents/prompts/converge.md" in out
    assert "in sync" not in out
    assert stale.is_file()  # verify never deletes


def test_prune_deletes_a_retired_kit_file(tmp_path, capsys):
    stale = _plant_retired_converge(tmp_path)
    capsys.readouterr()
    rc = install.main(["--tool", "codex", "--project", str(tmp_path), "--prune"])
    out = capsys.readouterr().out
    assert rc == 0
    assert not stale.exists()
    assert "retired from this host" in out
    assert install.main(["--tool", "codex", "--project", str(tmp_path), "--verify"]) == 0


def test_prune_of_a_retired_file_ends_the_kit_ownership_claim(tmp_path):
    # the completed delete must also drop the manifest's kit-created record (the F32 residual
    # pattern): without that, a file the user later creates at the retired path is claimed by
    # the stale record and deleted by the very next prune
    stale = _plant_retired_converge(tmp_path)
    install.main(["--tool", "codex", "--project", str(tmp_path), "--prune"])
    assert not stale.exists()
    mpath = tmp_path / ".outpost" / "manifest.json"
    files = json.loads(mpath.read_text(encoding="utf-8"))["tools"]["codex"]["files"]
    assert ".agents/prompts/converge.md" not in files
    stale.write_text("my own converge notes", encoding="utf-8")
    install.main(["--tool", "codex", "--project", str(tmp_path), "--prune"])
    assert stale.read_text(encoding="utf-8") == "my own converge notes"


def test_remove_deletes_a_retired_kit_file(tmp_path):
    stale = _plant_retired_converge(tmp_path)
    rc = install.main(["--tool", "codex", "--project", str(tmp_path), "--remove"])
    assert rc == 0
    assert not stale.exists()
    assert not (tmp_path / ".agents" / "prompts").exists()


def test_prune_skips_a_hand_edited_retired_file(tmp_path, capsys):
    # a retired file whose recorded hash no longer matches was edited after install: the
    # manifest's ownership proof alone is not enough, unlike the clean-delete case above
    stale = _plant_retired_converge(tmp_path, kit_hash="wrong")
    capsys.readouterr()
    rc = install.main(["--tool", "codex", "--project", str(tmp_path), "--prune"])
    out = capsys.readouterr().out
    assert rc == 0
    assert stale.is_file()
    assert "skip" in out and ".agents/prompts/converge.md" in out and "edited" in out


def test_remove_skips_a_hand_edited_retired_file(tmp_path):
    stale = _plant_retired_converge(tmp_path, kit_hash="wrong")
    rc = install.main(["--tool", "codex", "--project", str(tmp_path), "--remove"])
    assert rc == 0
    assert stale.is_file()


def test_prune_skips_a_retired_file_with_no_recorded_hash(tmp_path, capsys):
    # a manifest written before this check existed has no kit_hash: honestly unknowable, so the
    # safe default is skip, never guess-delete
    stale = _plant_retired_converge(tmp_path, kit_hash="missing")
    capsys.readouterr()
    rc = install.main(["--tool", "codex", "--project", str(tmp_path), "--prune"])
    out = capsys.readouterr().out
    assert rc == 0
    assert stale.is_file()
    assert "skip" in out and ".agents/prompts/converge.md" in out


def test_remove_does_not_delete_a_file_outside_the_project_via_a_symlink(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "secret.txt"
    secret.write_text("do not delete me", encoding="utf-8")

    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / "link_dir").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    kit_hash = install._hash_str("do not delete me")
    manifest = {"kit_version": "0.3.0", "tools": {"claude": {
        "selection": "full", "prompts": [], "terse": False,
        "files": {"link_dir/secret.txt": {"existed": False, "kit_hash": kit_hash}},
    }}}

    removed, skipped, failed, retired = install.remove_for_tools(
        project, ["claude"], manifest, args_terse=False)

    assert "link_dir/secret.txt" not in removed
    assert "link_dir/secret.txt" not in retired
    assert secret.exists()
    assert secret.read_text(encoding="utf-8") == "do not delete me"


def test_install_skips_a_plan_derived_path_behind_a_dangling_symlink(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside_target = tmp_path / "outside-target.txt"
    try:
        (project / "CLAUDE.md").symlink_to("../outside-target.txt")
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    result = install.main(["--tool", "claude", "--project", str(project)])

    assert result == 0
    assert not outside_target.exists()
    assert (project / ".claude" / "skills" / "code-review" / "SKILL.md").is_file()
    assert (project / "CLAUDE.md").is_symlink()
    assert not (project / "CLAUDE.md").exists()  # still dangling; never followed or overwritten


def test_apply_skips_a_write_action_whose_target_escapes_via_a_symlink(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / "escaped.md").symlink_to("../outside.txt")
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    action = install.Action(path="escaped.md", mode="write", content="hello", note="test")
    tally = install.apply([action], project)

    assert not (project.parent / "outside.txt").exists()
    assert tally["skip (escapes)"] == 1


def test_unmerge_settings_skips_a_write_back_through_a_symlink(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = project.parent / "outside-settings.json"
    outside_content = '{"permissions": {"deny": ["Read(./.env)", "my-own-rule"]}}\n'
    outside.write_text(outside_content, encoding="utf-8")
    settings_dir = project / ".claude"
    settings_dir.mkdir()
    try:
        # Absolute target: see the note in test_apply_stale_terse_skips_a_clear_through_a_symlink.
        # The identical backslash-relative bug was here first (this is presumably where it got
        # copied from), silently passing on 3 of this repo's 4 CI legs for the same reason.
        (settings_dir / "settings.json").symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    manifest = {"tools": {"claude": {"selection": "full", "prompts": []}}}  # legacy manifest, files=None
    install.unmerge_kit_settings(project, ["claude"], manifest, args_terse=False)

    assert outside.read_text(encoding="utf-8") == outside_content  # untouched


def test_manifest_records_no_ownership_for_a_symlink_escaped_path(tmp_path):
    shared = tmp_path / "shared-claude"
    shared.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / ".claude").symlink_to(shared, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    result = install.main(["--tool", "claude", "--project", str(project)])
    assert result == 0

    manifest = json.loads((project / ".outpost" / "manifest.json").read_text(encoding="utf-8"))
    files = manifest.get("tools", {}).get("claude", {}).get("files") or {}
    escaped_paths = [p for p in files if p.startswith(".claude/")]
    assert escaped_paths == [], (
        f"manifest claims ownership of escaped paths it never wrote: {escaped_paths}")

    # simulate a real kit file legitimately arriving at the shared location later (another
    # project's own install), then confirm --remove in THIS project cannot delete it there
    real_skill = shared / "skills" / "code-review" / "SKILL.md"
    real_skill.parent.mkdir(parents=True)
    kit_content = (
        pathlib.Path(__file__).resolve().parents[1] / "plugins" / "outpost" / "skills"
        / "code-review" / "SKILL.md"
    ).read_text(encoding="utf-8")
    real_skill.write_text(kit_content, encoding="utf-8")

    remove_result = install.main(["--tool", "claude", "--project", str(project), "--remove"])
    assert remove_result == 0
    assert real_skill.exists(), "a file outside the project was deleted through the symlink"


def test_remove_for_tools_skips_a_path_that_escapes_via_a_symlink(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside-skill.md"
    # Byte-identical to the kit's own rendering: remove_for_tools's byte-match guard would
    # otherwise skip this path on content grounds alone, which would pass regardless of the
    # containment check this test targets and prove nothing about it.
    kit_content = (ROOT / "plugins" / "outpost" / "skills" / "code-review" / "SKILL.md").read_text(
        encoding="utf-8")
    outside.write_text(kit_content, encoding="utf-8")
    skills_dir = project / ".claude" / "skills" / "code-review"
    skills_dir.mkdir(parents=True)
    try:
        # An absolute target: a relative multi-level target string ("../../../../...") resolves
        # correctly through Path.resolve() on this Windows/Python 3.14 box, but exists()/stat()/
        # unlink() raise WinError 123 against it, which would exit this loop through the plain
        # "not target.exists(): continue" above the guard under test, for the wrong reason, and
        # pass without ever exercising it. Same quirk as commit 97b39f5 and Task 1's own fix.
        (skills_dir / "SKILL.md").symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    manifest = {"tools": {"claude": {"selection": "full", "prompts": []}}}  # legacy manifest, files=None
    removed, skipped, failed, retired = install.remove_for_tools(
        project, ["claude"], manifest, args_terse=False)

    assert ".claude/skills/code-review/SKILL.md" not in removed
    assert ".claude/skills/code-review/SKILL.md" in skipped
    assert outside.read_text(encoding="utf-8") == kit_content


def test_prune_orphans_skips_a_path_that_escapes_via_a_symlink(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside-skill.md"
    kit_content = (ROOT / "plugins" / "outpost" / "skills" / "code-review" / "SKILL.md").read_text(
        encoding="utf-8")
    outside.write_text(kit_content, encoding="utf-8")
    skills_dir = project / ".claude" / "skills" / "code-review"
    skills_dir.mkdir(parents=True)
    try:
        (skills_dir / "SKILL.md").symlink_to(outside)  # absolute target; see the note above
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    # A legacy manifest (no "files" map at all) that narrows the selection to nothing, so
    # code-review's SKILL.md reads as a de-selected orphan and falls to the byte-match-only
    # legacy path. An empty "files": {} map (present but empty) would instead skip this path
    # via the separate "no record for this path" rule, regardless of the containment check.
    manifest = {"tools": {"claude": {"selection": "only", "prompts": []}}}
    removed, skipped, failed, retired = install.prune_orphans(
        project, ["claude"], manifest, args_terse=False)

    assert ".claude/skills/code-review/SKILL.md" not in removed
    assert ".claude/skills/code-review/SKILL.md" in skipped
    assert outside.read_text(encoding="utf-8") == kit_content


def test_prune_does_not_persist_the_manifest_through_an_escaping_symlink(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    install.main(["--tool", "claude", "--project", str(project)])  # full pack
    install.main(["--tool", "claude", "--project", str(project), "--exclude", "grill"])  # orphans grill
    real_manifest = (project / ".outpost" / "manifest.json").read_text(encoding="utf-8")
    outside_manifest = tmp_path / "outside-manifest.json"
    outside_manifest.write_text(real_manifest, encoding="utf-8")
    (project / ".outpost" / "manifest.json").unlink()
    try:
        (project / ".outpost" / "manifest.json").symlink_to(outside_manifest)  # absolute target
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    # prune_orphans() itself never writes the manifest; only main()'s --prune block does, and
    # only when something was retired or removed. The grill orphan above is what drives
    # execution into the guarded write call this test targets, via a real main() --prune run.
    result = install.main(["--tool", "claude", "--project", str(project), "--prune"])

    assert result == 0
    assert not (project / ".claude" / "skills" / "grill").exists()  # the orphan is still pruned
    assert outside_manifest.read_text(encoding="utf-8") == real_manifest, (
        "the manifest outside the project was overwritten")


def test_remove_does_not_delete_the_manifest_through_an_escaping_symlink(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    install.main(["--tool", "claude", "--project", str(project)])
    real_manifest = (project / ".outpost" / "manifest.json").read_text(encoding="utf-8")
    outside_manifest = tmp_path / "outside-manifest.json"
    outside_manifest.write_text(real_manifest, encoding="utf-8")
    (project / ".outpost" / "manifest.json").unlink()
    try:
        (project / ".outpost" / "manifest.json").symlink_to("../../outside-manifest.json")
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    result = install.main(["--tool", "claude", "--project", str(project), "--remove"])

    assert result == 0
    assert outside_manifest.exists(), "the manifest outside the project was deleted"


def test_remove_does_not_overwrite_the_manifest_through_an_escaping_symlink(tmp_path):
    # Removing one tool out of several leaves manifest["tools"] non-empty, so main()'s --remove
    # block takes the WRITE branch (mpath.write_bytes) rather than the delete branch. write_bytes
    # follows a symlink to its target's content on this platform (unlink does not: it only
    # removes the link itself), so this is the branch of the guard under test that a
    # single-tool-installed fixture (the delete-branch test above) can never exercise.
    project = tmp_path / "project"
    project.mkdir()
    install.main(["--tool", "all", "--project", str(project)])  # several tools stay after one goes
    real_manifest = (project / ".outpost" / "manifest.json").read_text(encoding="utf-8")
    outside_manifest = tmp_path / "outside-manifest.json"
    outside_manifest.write_text(real_manifest, encoding="utf-8")
    (project / ".outpost" / "manifest.json").unlink()
    try:
        (project / ".outpost" / "manifest.json").symlink_to(outside_manifest)  # absolute target
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    result = install.main(["--tool", "claude", "--project", str(project), "--remove"])

    assert result == 0
    assert outside_manifest.read_text(encoding="utf-8") == real_manifest, (
        "the manifest outside the project was overwritten")


def test_retired_paths_excludes_a_path_that_escapes_through_a_symlink(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("x", encoding="utf-8")

    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / "link_dir").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    manifest = {"tools": {"claude": {"prompts": [], "files": {
        "link_dir/secret.txt": {"existed": False, "kit_hash": "sha256:irrelevant"},
    }}}}

    result = install._retired_paths(project, "claude", manifest, terse=False, tolerant=True)

    assert result == []


def test_a_user_owned_converge_file_is_never_touched(tmp_path, capsys):
    # the same path with no kit-created record (none at all, or recorded as pre-existing) is the
    # user's file: verify stays in sync, prune and remove leave it alone
    install.main(["--tool", "codex", "--project", str(tmp_path)])
    mine = tmp_path / ".agents" / "prompts" / "converge.md"
    mine.write_text("my own converge notes", encoding="utf-8")
    assert install.main(["--tool", "codex", "--project", str(tmp_path), "--verify"]) == 0
    install.main(["--tool", "codex", "--project", str(tmp_path), "--prune"])
    assert mine.read_text(encoding="utf-8") == "my own converge notes"

    mpath = tmp_path / ".outpost" / "manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    manifest["tools"]["codex"]["files"][".agents/prompts/converge.md"] = {
        "existed": True, "pre_hash": "sha256:0"}
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    assert install.main(["--tool", "codex", "--project", str(tmp_path), "--verify"]) == 0
    install.main(["--tool", "codex", "--project", str(tmp_path), "--prune"])
    install.main(["--tool", "codex", "--project", str(tmp_path), "--remove"])
    assert mine.read_text(encoding="utf-8") == "my own converge notes"


def test_only_warns_when_a_prompt_does_not_ship_to_the_tool(tmp_path, capsys):
    rc = install.main(["--tool", "codex", "--project", str(tmp_path),
                       "--only", "converge,grill"])
    err = capsys.readouterr().err
    assert rc == 0
    assert "converge" in err and "codex" in err
    assert (tmp_path / ".agents" / "prompts" / "grill.md").is_file()
    assert not (tmp_path / ".agents" / "prompts" / "converge.md").exists()


def test_records_less_fallback_keeps_a_user_file_outside_the_recorded_footprint(tmp_path, capsys):
    # subset install, files map stripped (a records-less manifest), a user file at a path the old
    # install never wrote, then a full reinstall. The user file must survive.
    install.main(["--tool", "copilot", "--project", str(tmp_path), "--only", "plan-change"])
    mpath = tmp_path / ".outpost" / "manifest.json"
    data = json.loads(mpath.read_text(encoding="utf-8"))
    data["tools"]["copilot"].pop("files")
    mpath.write_text(json.dumps(data), encoding="utf-8")
    mine = tmp_path / ".github" / "prompts" / "write-tests.prompt.md"
    mine.write_text("my own prompt", encoding="utf-8")
    capsys.readouterr()
    rc = install.main(["--tool", "copilot", "--project", str(tmp_path)])  # full reinstall
    assert rc == 0
    assert mine.read_text(encoding="utf-8") == "my own prompt"  # user bytes never overwritten
    rec = _manifest(tmp_path)["tools"]["copilot"]["files"][".github/prompts/write-tests.prompt.md"]
    assert rec["existed"] is True  # recorded as the user's, so --remove can never delete it
    install.main(["--tool", "copilot", "--project", str(tmp_path), "--remove"])
    assert mine.read_text(encoding="utf-8") == "my own prompt"


def test_records_less_fallback_claims_the_recorded_footprint(tmp_path):
    # inside the recorded footprint the kit's own files stay the kit's: a reinstall updates them,
    # so they are recorded existed=False, not read as the user's.
    install.main(["--tool", "copilot", "--project", str(tmp_path), "--only", "plan-change"])
    mpath = tmp_path / ".outpost" / "manifest.json"
    data = json.loads(mpath.read_text(encoding="utf-8"))
    data["tools"]["copilot"].pop("files")
    mpath.write_text(json.dumps(data), encoding="utf-8")
    install.main(["--tool", "copilot", "--project", str(tmp_path)])  # full reinstall
    files = _manifest(tmp_path)["tools"]["copilot"]["files"]
    for path in (".github/prompts/plan-change.prompt.md", ".github/copilot-instructions.md"):
        assert files[path]["existed"] is False
        assert files[path]["kit_hash"].startswith("sha256:")


def test_install_reports_a_symlink_escape_distinctly_from_an_ordinary_skip(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / "escaped.md").symlink_to("../outside-target.txt")
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    action = install.Action(path="escaped.md", mode="write", content="hello", note="test")
    tally = install.apply([action], project)

    assert tally.get("skip (escapes)") == 1
    assert tally.get("skip (exists)", 0) == 0


def test_verify_reports_escaped_distinctly_from_missing(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / "escaped.md").symlink_to("../outside.txt")
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    action = install.Action(path="escaped.md", mode="write", content="hello", note="test")
    ok, lines, escaped_paths, missing_or_drifted = install.verify([action], project)

    assert ok is False
    assert any("ESCAPED" in line and "escaped.md" in line for line in lines)
    assert not any("MISSING" in line and "escaped.md" in line for line in lines)
    # the caller (main()'s --verify summary) uses this split to avoid telling a symlink escape
    # to re-run install: an escaped-only verify has nothing a re-install would actually restore
    assert escaped_paths == ["escaped.md"]
    assert missing_or_drifted is False


def test_verify_reports_ok_for_a_user_owned_or_create_path_that_escapes_via_a_symlink(tmp_path):
    # A user who symlinks their own CLAUDE.md (or a manifest-recorded pre-existing file) to a
    # shared dotfiles location is not an attack: the kit never writes these paths regardless of
    # whether they escape, so there was never anything for re-running install to change. The
    # ESCAPED check must not fire here; verify()'s own docstring says a user-owned target is
    # "fine present or absent," which a false ESCAPED would contradict.
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / "CLAUDE.md").symlink_to("../outside-claude.md")
        (project / "mine.md").symlink_to("../outside-mine.md")
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    actions = [
        install.Action(path="CLAUDE.md", mode="create", content="guide", note="test"),
        install.Action(path="mine.md", mode="write", content="kit content", note="test"),
    ]
    ok, lines, escaped_paths, missing_or_drifted = install.verify(
        actions, project, user_owned={"mine.md"})

    assert ok is True
    assert not any("ESCAPED" in line for line in lines)
    assert any("ok" in line and "CLAUDE.md" in line for line in lines)
    assert any("ok" in line and "mine.md" in line for line in lines)
    assert escaped_paths == []
    assert missing_or_drifted is False


def test_orphans_splits_an_escaping_path_into_its_own_list(tmp_path):
    # A project whose .claude directory is a symlink to a location shared with another project
    # (the non-malicious scenario): a file genuinely present there, from an earlier
    # real install before the symlink was planted, reads as an ordinary de-selected orphan
    # unless _orphans() checks containment the same way apply()/verify() already do.
    shared = tmp_path / "shared-claude"
    grill = shared / "skills" / "grill" / "SKILL.md"
    grill.parent.mkdir(parents=True)
    grill.write_text("kit content", encoding="utf-8")
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / ".claude").symlink_to(shared, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    extras, escaped = install._orphans(project, "claude", set(), terse=False)

    assert ".claude/skills/grill/SKILL.md" not in extras
    assert ".claude/skills/grill/SKILL.md" in escaped


def test_verify_does_not_instruct_removing_an_orphan_that_escapes_via_a_symlink(tmp_path, capsys):
    # Live-reproduces the reviewer's I1: --verify must never tell a human to hand-delete a path
    # that resolves outside the project, the way an ordinary EXTRA/DRIFT line would.
    shared = tmp_path / "shared-claude"
    grill = shared / "skills" / "grill" / "SKILL.md"
    grill.parent.mkdir(parents=True)
    grill.write_text("kit content", encoding="utf-8")
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / ".claude").symlink_to(shared, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")
    (project / ".outpost").mkdir()
    manifest = {"tools": {"claude": {"selection": "only", "prompts": []}}}
    (project / ".outpost" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    rc = install.main(["--tool", "claude", "--project", str(project), "--verify"])
    out = capsys.readouterr().out

    assert rc == 1  # still surfaced, just not as an ordinary orphan
    lines = out.splitlines()
    assert not any("EXTRA" in ln and "grill" in ln for ln in lines), (
        "verify must not instruct removing a path outside the project")
    assert any("ESCAPED" in ln and "grill" in ln for ln in lines)


def test_verify_summary_does_not_claim_reinstall_fixes_an_escaped_path(tmp_path, capsys):
    # When the only reason --verify fails is a kit-owned file that now resolves outside the
    # project via a symlink, the summary must not send the user to re-run install: verify()'s own
    # per-path ESCAPED line already says the opposite (re-running install will not change this),
    # and apply() genuinely refuses to write an escaping path. The generic drift line would
    # flatly contradict the line printed just above it in the same --verify output.
    project = tmp_path / "project"
    project.mkdir()
    install.main(["--tool", "claude", "--project", str(project)])
    skill = project / ".claude" / "skills" / "plan-change" / "SKILL.md"
    outside = tmp_path / "outside-plan-change.md"
    outside.write_text(skill.read_text(encoding="utf-8"), encoding="utf-8")
    skill.unlink()
    try:
        # Absolute target: a relative multi-level target ("../../../../...") resolves correctly
        # through Path.resolve() on this Windows/Python 3.14 box, but exists()/stat()/unlink()
        # raise WinError 123 against it (see the note in
        # test_remove_for_tools_skips_a_path_that_escapes_via_a_symlink above).
        skill.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")
    capsys.readouterr()

    rc = install.main(["--tool", "claude", "--project", str(project), "--verify"])
    out = capsys.readouterr().out
    lines = out.splitlines()

    assert rc == 1  # still a real problem, just not one a re-install fixes
    assert any("ESCAPED" in ln and "plan-change" in ln for ln in lines)
    assert "re-run install to restore the kit files" not in out


def test_verify_summary_still_flags_reinstallable_drift_alongside_an_escaped_path(tmp_path, capsys):
    # Mixed case: one kit-owned file escapes via a symlink (a re-install cannot fix it) and a
    # different kit-owned file is genuinely drifted (a re-install does fix it), in the same
    # --verify run. Both summary lines must appear, each scoped to what it actually describes;
    # suppressing the generic "re-run install" line just because an escape is ALSO present would
    # wrongly hide real, fixable drift from the user.
    project = tmp_path / "project"
    project.mkdir()
    install.main(["--tool", "claude", "--project", str(project)])
    escaped_skill = project / ".claude" / "skills" / "plan-change" / "SKILL.md"
    outside = tmp_path / "outside-plan-change.md"
    outside.write_text(escaped_skill.read_text(encoding="utf-8"), encoding="utf-8")
    escaped_skill.unlink()
    try:
        escaped_skill.symlink_to(outside)  # absolute target; see the note above
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")
    drifted_skill = project / ".claude" / "skills" / "code-review" / "SKILL.md"
    drifted_skill.write_text("hand-edited, drifted from the kit version", encoding="utf-8")
    capsys.readouterr()

    rc = install.main(["--tool", "claude", "--project", str(project), "--verify"])
    out = capsys.readouterr().out
    lines = out.splitlines()

    assert rc == 1
    assert any("ESCAPED" in ln and "plan-change" in ln for ln in lines)
    assert any("DRIFTED" in ln and "code-review" in ln for ln in lines)
    assert "DRIFT: re-run install to restore the kit files" in out  # genuine drift: re-install helps
    assert any(ln.startswith("DRIFT:") and "resolve outside the project via a symlink" in ln
               for ln in lines)  # the escape gets its own distinct summary line, not folded in


def test_verify_summary_does_not_claim_reinstall_fixes_a_stale_terse_escape(tmp_path, capsys):
    # Live-reproduced contradiction: a genuinely stale outputStyle key (the style file already
    # went, same setup as _withdraw_terse_but_leave_the_key above) sitting in a settings.json that
    # now resolves outside the project via a symlink. stale_terse_state() had no containment
    # check, so it queued a "clear" op from the JSON content read straight through the symlink,
    # and --verify's stale-terse loop printed DRIFTED plus "re-run install to clean it" for the
    # same path its own ESCAPED line, from the ordinary verify() pass over the settings merge
    # action, already says re-running install will not change.
    project = tmp_path / "project"
    project.mkdir()
    install.main(["--tool", "claude", "--project", str(project), "--terse"])
    (project / ".claude" / "output-styles" / "terse.md").unlink()
    mpath = project / ".outpost" / "manifest.json"
    data = json.loads(mpath.read_text(encoding="utf-8"))
    data["tools"]["claude"]["terse"] = False
    mpath.write_text(json.dumps(data), encoding="utf-8")

    settings = project / ".claude" / "settings.json"
    outside = tmp_path / "outside-settings.json"
    outside.write_text(settings.read_text(encoding="utf-8"), encoding="utf-8")
    settings.unlink()
    try:
        # Absolute target; see the note in
        # test_verify_summary_does_not_claim_reinstall_fixes_an_escaped_path above.
        settings.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")
    capsys.readouterr()

    rc = install.main(["--tool", "claude", "--project", str(project), "--verify"])
    out = capsys.readouterr().out
    lines = out.splitlines()

    assert rc == 1  # still a real problem, just not one a re-install fixes
    assert any("ESCAPED" in ln and "outputStyle" in ln for ln in lines)
    assert not any(ln.strip().startswith("DRIFTED") and "settings.json" in ln for ln in lines)
    assert "re-run install to clean it" not in out
    assert "DRIFT: stale terse state left by an earlier terse install" not in out


def test_verify_summary_still_flags_reinstallable_stale_terse_alongside_an_escaped_one(
        tmp_path, capsys):
    # Mixed case scoped to stale-terse state alone: the style file is genuine, fixable leftover
    # state (a re-install removes it) while the settings.json outputStyle key is the same
    # escaping key as the test above. Both summary lines must appear, each scoped to what it
    # actually found; suppressing the genuine "re-run install to clean it" line just because an
    # escape is ALSO present would wrongly hide real, fixable stale-terse state from the user.
    project = tmp_path / "project"
    project.mkdir()
    install.main(["--tool", "claude", "--project", str(project), "--terse"])
    mpath = project / ".outpost" / "manifest.json"
    data = json.loads(mpath.read_text(encoding="utf-8"))
    data["tools"]["claude"]["terse"] = False  # simulate a pre-fix withdrawal: state stays on disk
    mpath.write_text(json.dumps(data), encoding="utf-8")

    settings = project / ".claude" / "settings.json"
    outside = tmp_path / "outside-settings.json"
    outside.write_text(settings.read_text(encoding="utf-8"), encoding="utf-8")
    settings.unlink()
    try:
        settings.symlink_to(outside)  # absolute target; see the note above
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")
    capsys.readouterr()

    rc = install.main(["--tool", "claude", "--project", str(project), "--verify"])
    out = capsys.readouterr().out
    lines = out.splitlines()

    assert rc == 1
    assert any(ln.strip().startswith("DRIFTED") and "terse.md" in ln for ln in lines)
    assert any("ESCAPED" in ln and "outputStyle" in ln for ln in lines)
    assert "DRIFT: stale terse state left by an earlier terse install; re-run install" in out
    assert any(ln.startswith("DRIFT:") and "stale terse path(s)" in ln for ln in lines)


def test_verify_summary_does_not_claim_in_sync_over_an_escaped_stale_terse_style(
        tmp_path, capsys):
    # The in-sync gate's "and not escaped_stale" clause has no dedicated coverage: both escaped
    # stale-terse tests above symlink settings.json itself, which also fails the ordinary
    # verify() pass over the settings merge action, so `ok` is already False there and the gate
    # is closed regardless of the clause. Escaping the style file's own directory instead keeps
    # every ordinary action clean (a non-terse verify's plan never includes the style path at
    # all, see kit/adapters/claude.py), so escaped_stale is the only thing keeping the gate
    # closed. Without the clause, --verify prints an ESCAPED line for the style file and then, in
    # the same breath, claims "in sync" and exits 0.
    project = tmp_path / "project"
    project.mkdir()
    install.main(["--tool", "claude", "--project", str(project), "--terse"])

    # A user replaces the local output-styles directory with a symlink to a location shared with
    # another project (the same non-malicious shared-dotfiles setup as the ancestor-directory
    # symlink tests above), empty at this point: the terse install's own style file goes with it.
    styles_dir = project / ".claude" / "output-styles"
    (styles_dir / "terse.md").unlink()
    styles_dir.rmdir()
    shared = tmp_path / "shared-output-styles"
    shared.mkdir()
    try:
        styles_dir.symlink_to(shared, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    # A plain reinstall withdraws terse. The style file is not reachable through the (still
    # empty) symlink target, so no remove op is queued for it and its manifest ownership record
    # survives untouched; settings.json, not itself behind any symlink, has its outputStyle key
    # cleared normally.
    install.main(["--tool", "claude", "--project", str(project)])
    settings = json.loads((project / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "outputStyle" not in settings

    # The shared location later gains a real terse.md, as if a sibling project also using this
    # kit with --terse installed into it: the survived ownership record now points at kit
    # content again, but only reachable outside the project via the symlink.
    (shared / "terse.md").write_text(install.TERSE_OUTPUT_STYLE, encoding="utf-8")
    capsys.readouterr()

    rc = install.main(["--tool", "claude", "--project", str(project), "--verify"])
    out = capsys.readouterr().out
    lines = out.splitlines()

    assert any("ESCAPED" in ln and "output-styles/terse.md" in ln for ln in lines)
    assert rc == 1  # a real, unfixed-by-reinstall problem: must not be reported as in sync
    assert "in sync" not in out  # would directly contradict the ESCAPED line above it


def test_render_plan_shows_an_escape_not_a_false_create(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / "escaped.md").symlink_to("../outside.txt")
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    action = install.Action(path="escaped.md", mode="write", content="hello", note="test")
    lines = install.render_plan([action], project)

    assert any("skip (escapes)" in ln and "escaped.md" in ln for ln in lines)
    assert not any(ln.strip().startswith("[create") for ln in lines)


def test_dry_run_shows_an_escape_not_a_false_create(tmp_path, capsys):
    # Live-reproduces the reviewer's I2: --dry-run must agree with what a real install would do,
    # matching this file's own docstring and docs/adapters.md's "the preview is exact" claim.
    shared = tmp_path / "shared-claude"
    shared.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / ".claude").symlink_to(shared, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    rc = install.main(["--tool", "claude", "--project", str(project), "--dry-run"])
    out = capsys.readouterr().out

    assert rc == 0
    claude_lines = [ln for ln in out.splitlines() if ".claude/" in ln]
    assert claude_lines, "expected at least one .claude/ line in the dry-run plan"
    assert all("skip (escapes)" in ln for ln in claude_lines)
    assert not any(ln.strip().startswith("[create") for ln in claude_lines)


def test_install_summary_notes_an_escape_when_one_occurs(tmp_path, capsys):
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / "CLAUDE.md").symlink_to("../outside-claude-guide.md")
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(project)])
    out = capsys.readouterr().out

    assert rc == 0
    assert "1 left alone (escaping the project via a symlink)" in out


def test_install_summary_omits_the_escape_note_when_nothing_escapes(tmp_path, capsys):
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path)])
    out = capsys.readouterr().out

    assert rc == 0
    assert "left alone (escaping the project via a symlink)" not in out


def test_apply_stale_terse_skips_a_clear_through_a_symlink(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = project.parent / "outside-style.json"
    outside_content = '{"outputStyle": "terse", "other": "value"}\n'
    outside.write_text(outside_content, encoding="utf-8")
    settings_dir = project / ".claude"
    settings_dir.mkdir()
    try:
        # Absolute target: a backslash-relative string ("..\\..\\...") is a path separator only
        # on Windows. On POSIX, backslash is a literal filename character, so the whole string
        # reads as one nonexistent path component still inside the project. _is_contained sees
        # it as contained, the guard never fires, and the resulting FileNotFoundError from
        # read_text() gets caught by this branch's own except (ValueError, OSError), so the test
        # would pass for the wrong reason on 3 of this repo's 4 CI legs (every ubuntu job).
        (settings_dir / "settings.json").symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    install.apply_stale_terse(project, [("clear", ".claude/settings.json")])

    assert outside.read_text(encoding="utf-8") == outside_content


def test_apply_stale_terse_skips_a_remove_through_a_symlink(tmp_path):
    # A leaf symlink (terse.md -> an outside file) cannot reproduce the reviewer's C1 finding:
    # Path.unlink() on a file symlink removes the link itself, never the target it points to, on
    # every platform (confirmed empirically here, not a Windows-only quirk). The reviewer's real
    # repro moved .claude itself out and replaced it with a directory symlink, so the leaf
    # terse.md the unlink() call reaches is a genuine file living outside the project, not a
    # symlink. Matches the ancestor-directory-symlink pattern already used in this file (see
    # test_remove_does_not_delete_a_file_outside_the_project_via_a_symlink above).
    outside = tmp_path / "outside-claude"
    (outside / "output-styles").mkdir(parents=True)
    real_terse = outside / "output-styles" / "terse.md"
    outside_content = "not the kit's terse style file, do not delete"
    real_terse.write_text(outside_content, encoding="utf-8")

    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / ".claude").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    install.apply_stale_terse(project, [("remove", ".claude/output-styles/terse.md")])

    assert real_terse.exists()
    assert real_terse.read_text(encoding="utf-8") == outside_content


def test_reinstall_keeps_terse_ownership_record_when_withdrawal_escapes_via_a_symlink(tmp_path):
    # Post-merge review of PR #36: the ownership-record pop for a completed terse withdrawal (the
    # F32 residual fix, test_completed_withdrawal_releases_style_ownership above) had no
    # containment check of its own, unlike apply_stale_terse's sibling remove/clear branches.
    # apply_stale_terse correctly refuses to delete the escaping style file here (see the test
    # just above), but the pop ran anyway and dropped the manifest's ownership record regardless
    # of whether the withdrawal actually reached the file -- so --verify silently stopped
    # mentioning a still-active terse style sitting at the shared, escaped location, instead of
    # reporting it ESCAPED like its settings.json sibling does.
    project = tmp_path / "project"
    project.mkdir()
    install.main(["--tool", "claude", "--project", str(project), "--terse"])

    outside = tmp_path / "outside-claude"
    (project / ".claude").rename(outside)
    try:
        (project / ".claude").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    install.main(["--tool", "claude", "--project", str(project)])  # plain reinstall: withdraws terse

    real_terse = outside / "output-styles" / "terse.md"
    assert real_terse.is_file()  # never deleted: apply_stale_terse's own guard skips it

    mpath = project / ".outpost" / "manifest.json"
    files = json.loads(mpath.read_text(encoding="utf-8"))["tools"]["claude"]["files"]
    assert install.TERSE_STYLE_PATH in files, (
        "the manifest dropped ownership of a terse style the withdrawal never actually reached")


def test_dry_run_shows_an_escape_not_an_unconditional_stale_terse_withdrawal(tmp_path, capsys):
    # main()'s --dry-run branch renders the stale-terse withdrawal preview in its own loop,
    # separate from render_plan(): it was never given the containment check
    # apply_stale_terse() already has, so a dry-run over a project whose .claude is now a
    # directory symlink still showed an unconditional [remove]/[clear] for a path a real
    # install would actually warn about and leave alone. Same ancestor-directory-symlink
    # repro as test_apply_stale_terse_skips_a_remove_through_a_symlink: a real --terse
    # install first, so the withdrawal is genuinely triggered by a recorded prior install,
    # not hand-built stale state.
    project = tmp_path / "project"
    project.mkdir()
    install.main(["--tool", "claude", "--project", str(project), "--terse"])

    outside = tmp_path / "outside-claude"
    (project / ".claude").rename(outside)
    try:
        (project / ".claude").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(project), "--dry-run"])
    out = capsys.readouterr().out

    assert rc == 0
    withdrawal_lines = [ln for ln in out.splitlines() if "] clean  " in ln]
    assert len(withdrawal_lines) == 2, withdrawal_lines  # terse.md remove + settings.json clear
    assert not any("terse withdrawn by this install" in ln for ln in withdrawal_lines), (
        "dry-run must not show an unconditional remove/clear for a path that escapes the "
        "project via a symlink")
    assert all("skip (escapes)" in ln for ln in withdrawal_lines)


def test_apply_checks_containment_before_the_pre_existing_and_warn_logic(tmp_path, capsys):
    # Task 1's review found that checking containment AFTER the WARN/protected logic (where it
    # originally shipped) misreports an escaping path two different ways: a content-matching
    # escape reads straight through to "unchanged" (never flagged as an escape at all), and a
    # drifted escape triggers a spurious WARN about an overwrite that is never going to happen.
    # Moving the check to the top of the loop must guarantee neither ever prints for an escaping
    # path. Only the escape skip does, regardless of what the outside content looks like.
    # Absolute symlink targets throughout: status() has to read real content through the symlink
    # for the pre-fix (reverted-ordering) comparison to mean anything, and a relative target's
    # exists()/read_text() behavior is unreliable on this box (see the other fixes on this
    # branch).
    project = tmp_path / "project"
    project.mkdir()
    outside_matching = tmp_path / "outside-matching.md"
    outside_matching.write_text("kit content", encoding="utf-8")
    outside_drifted = tmp_path / "outside-drifted.md"
    outside_drifted.write_text("hand-edited content", encoding="utf-8")
    try:
        (project / "escaped-matching.md").symlink_to(outside_matching)
        (project / "escaped-drifted.md").symlink_to(outside_drifted)
    except OSError:
        pytest.skip("symlink creation not permitted in this environment")

    actions = [
        install.Action(path="escaped-matching.md", mode="write", content="kit content", note="t"),
        install.Action(path="escaped-drifted.md", mode="write", content="kit content", note="t"),
    ]
    capsys.readouterr()
    tally = install.apply(actions, project)
    out = capsys.readouterr().out

    assert tally["skip (escapes)"] == 2
    assert tally["unchanged"] == 0
    assert "(unchanged)" not in out
    assert "WARN" not in out
    assert "skip   escaped-matching.md (resolves outside the project via a symlink" in out
    assert "skip   escaped-drifted.md (resolves outside the project via a symlink" in out


# Post-merge review of PR #36: a real symlink loop makes pathlib.Path.resolve(strict=False) raise
# RuntimeError on Python 3.9-3.12 (dropped in 3.13, confirmed empirically: 3.12 raises, 3.13 and
# this repo's own 3.14 do not), and nothing in _is_contained or main() caught it, so a symlink
# loop at any plan-derived path crashed --dry-run, install, --verify, and --remove with a raw
# traceback on 4 of this repo's declared-supported versions. Mocking resolve() to raise the same
# exception type tests the actual exception-handling branch regardless of which Python version
# runs this suite.

def test_is_contained_treats_a_symlink_loop_as_not_contained(tmp_path, monkeypatch):
    real_resolve = pathlib.Path.resolve
    loop = tmp_path / "loop"

    def fake_resolve(self, *args, **kwargs):
        if self == loop:
            raise RuntimeError(f"Symlink loop from '{self}'")
        return real_resolve(self, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "resolve", fake_resolve)
    # unresolvable fails closed, the same as an ordinary escape: never treated as contained
    assert install._is_contained(tmp_path, "loop") is False


def test_apply_skips_a_symlink_loop_instead_of_crashing(tmp_path, monkeypatch, capsys):
    real_resolve = pathlib.Path.resolve
    loop = tmp_path / "loop.md"

    def fake_resolve(self, *args, **kwargs):
        if self == loop:
            raise RuntimeError(f"Symlink loop from '{self}'")
        return real_resolve(self, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "resolve", fake_resolve)
    action = install.Action(path="loop.md", mode="write", content="hello", note="test")
    capsys.readouterr()
    tally = install.apply([action], tmp_path)
    out = capsys.readouterr().out

    assert tally["skip (escapes)"] == 1
    assert "loop.md (resolves outside the project via a symlink; left alone)" in out


# Phase 3b: verify reports a kit-written guide whose bytes no longer match the manifest kit_hash.
# The guide stays the user's: EDITED is information, never drift, so the exit code is unchanged.

def _verify_lines(out: str) -> list:
    return [" ".join(line.split()) for line in out.splitlines()]


def test_verify_reports_an_edited_kit_written_guide(tmp_path, capsys):
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    capsys.readouterr()
    assert install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"]) == 0
    assert "EDITED" not in capsys.readouterr().out  # an untouched guide is not edited
    guide = tmp_path / "CLAUDE.md"
    guide.write_text(guide.read_text(encoding="utf-8") + "\nmy own line\n", encoding="utf-8")
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    out = capsys.readouterr().out
    assert rc == 0  # information, not drift
    lines = _verify_lines(out)
    assert "EDITED CLAUDE.md (yours to keep; differs from what the kit wrote)" in lines
    assert not any(line.startswith("ok CLAUDE.md") for line in lines)
    assert "DRIFT:" not in out
    assert "in sync" in out
    assert sum(line.startswith("NOTE: 1 guide") for line in lines) == 1


def test_verify_is_silent_for_an_edited_pre_existing_guide(tmp_path, capsys):
    guide = tmp_path / "CLAUDE.md"
    guide.write_text("my own guide\n", encoding="utf-8")
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    guide.write_text("my own guide, edited\n", encoding="utf-8")
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "ok CLAUDE.md (present)" in _verify_lines(out)
    assert "EDITED" not in out and "NOTE:" not in out  # no kit baseline, nothing to report


def test_verify_edited_note_counts_across_tools(tmp_path, capsys):
    install.main(["--tool", "all", "--project", str(tmp_path)])
    for name in ("CLAUDE.md", "AGENTS.md"):
        guide = tmp_path / name
        guide.write_text(guide.read_text(encoding="utf-8") + "\nmy own line\n", encoding="utf-8")
    capsys.readouterr()
    rc = install.main(["--tool", "all", "--project", str(tmp_path), "--verify"])
    out = capsys.readouterr().out
    assert rc == 0
    lines = _verify_lines(out)
    assert any(line.startswith("EDITED CLAUDE.md ") for line in lines)
    assert any(line.startswith("EDITED AGENTS.md ") for line in lines)
    assert any(line.startswith("ok GEMINI.md (present)") for line in lines)  # untouched
    notes = [line for line in lines if line.startswith("NOTE:")]
    assert len(notes) == 1 and notes[0].startswith("NOTE: 2 guide")


def test_verify_baseline_is_the_manifest_hash_not_the_current_template(tmp_path, monkeypatch,
                                                                         capsys):
    # A guide the kit wrote at an older version, left alone, stays ok after the template changes:
    # the baseline is the manifest kit_hash, not a re-rendered template.
    install.main(["--tool", "claude", "--project", str(tmp_path)])
    real_plan = install.plan_for

    def newer_kit(*args, **kwargs):
        return [dataclasses.replace(a, content=a.content + "\nnewer kit line\n")
                if a.path == "CLAUDE.md" else a for a in real_plan(*args, **kwargs)]

    monkeypatch.setattr(install, "plan_for", newer_kit)
    capsys.readouterr()
    rc = install.main(["--tool", "claude", "--project", str(tmp_path), "--verify"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "ok CLAUDE.md (present)" in _verify_lines(out)
    assert "EDITED" not in out and "NOTE:" not in out
