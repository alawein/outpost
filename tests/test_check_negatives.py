"""Negative tests: each check that exists to catch drift or collision must actually fail when the
violation is present. The gate-green test proves the in-sync state; these prove the catch."""
import pathlib
import re
import shutil

import pytest

from kit.adapters.base import Action
from kit.checks import (adapters, banned_sync, catalog, command_lists, commands, doc_truth, docs,
                        issue_forms, label_refs, plugin_orphans, prompts, prose_length, registries,
                        roadmap, structure, template_refs, templates, traces)

ROOT = pathlib.Path(__file__).resolve().parents[1]
# .claude holds machine-local tool config (untracked, gitignored); exclude it so an untracked
# settings file cannot leak a home path into the copied tree and trip the traces walk-fallback,
# which the real git-tracked scan never sees.
IGNORE = shutil.ignore_patterns(".git", ".claude", "__pycache__", ".pytest_cache", ".benchmarks",
                                ".venv", "venv", "*.egg-info")


@pytest.fixture
def repo_copy(tmp_path):
    dst = tmp_path / "kit"
    shutil.copytree(ROOT, dst, ignore=IGNORE)
    return dst


def test_doc_truth_catches_a_dangling_prompt_ref_in_onboarding(repo_copy):
    # a prompt-shaped backtick token in an instruction doc that resolves to no catalog prompt
    # (a rename or typo left it dangling) must fail, not just in workflow.md
    p = repo_copy / "docs" / "onboarding.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n\nRun `plan-changge` first.\n",
                 encoding="utf-8")
    ok, detail = doc_truth.run(repo_copy)
    assert not ok and "plan-changge" in detail


def test_banned_sync_catches_a_word_only_in_the_doc(repo_copy):
    p = repo_copy / "docs" / "writing-standard.md"
    text = p.read_text(encoding="utf-8").replace(
        "furthermore, utilize.", "furthermore, utilize, newfangled.")
    assert "newfangled" in text  # guard
    p.write_text(text, encoding="utf-8")
    ok, detail = banned_sync.run(repo_copy)
    assert not ok and "newfangled" in detail


def test_banned_sync_catches_a_word_only_in_the_code(repo_copy):
    # the other direction: a word enforced by BANNED but dropped from the doc
    p = repo_copy / "docs" / "writing-standard.md"
    text = p.read_text(encoding="utf-8").replace("furthermore, utilize.", "furthermore.")
    assert "utilize" not in text.split("## Banned register", 1)[1]  # guard: dropped from the list
    p.write_text(text, encoding="utf-8")
    ok, detail = banned_sync.run(repo_copy)
    assert not ok and "enforced but not in the doc" in detail and "utilize" in detail


def test_plugin_orphans_catches_a_stale_skill(repo_copy):
    ghost = repo_copy / "plugins" / "outpost" / "skills" / "ghost"
    ghost.mkdir(parents=True)
    (ghost / "SKILL.md").write_text("---\nname: ghost\n---\nx\n", encoding="utf-8")
    ok, detail = plugin_orphans.run(repo_copy)
    assert not ok and "ghost" in detail


def test_catalog_catches_unlisted_prompt(repo_copy):
    (repo_copy / "prompts" / "core" / "stray.md").write_text(
        "---\nname: stray\ndescription: x\n---\n# stray\nbody\n", encoding="utf-8")
    ok, detail = catalog.run(repo_copy)
    assert not ok and "not in the catalog" in detail


def test_catalog_catches_version_drift(repo_copy):
    # replace whatever version is in pyproject with a bogus one, so the test does not pin a release
    pj = repo_copy / "pyproject.toml"
    text = re.sub(r'(?m)^version\s*=\s*"[^"]+"', 'version = "9.9.9"', pj.read_text(encoding="utf-8"))
    pj.write_text(text, encoding="utf-8")
    ok, detail = catalog.run(repo_copy)
    assert not ok and "version drift" in detail


def test_catalog_catches_unlisted_template(repo_copy):
    (repo_copy / "templates" / "extra.md").write_text("# extra\n" + ("word " * 50), encoding="utf-8")
    ok, detail = catalog.run(repo_copy)
    assert not ok and "not in the catalog" in detail


def test_template_refs_catches_a_dangling_prompt_name(repo_copy):
    # a template that names a prompt not in the catalog (a rename left behind) must fail
    agents = repo_copy / "templates" / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8") + "\n- `was-renamed`: a stale reference.\n",
                      encoding="utf-8")
    ok, detail = template_refs.run(repo_copy)
    assert not ok and "was-renamed" in detail


def test_registries_catches_an_unregistered_check_module(repo_copy):
    # a check module on disk but not in the catalog would silently never run; the gate must catch it
    (repo_copy / "kit" / "checks" / "stray.py").write_text(
        "def run(root):\n    return True, 'noop'\n", encoding="utf-8")
    ok, detail = registries.run(repo_copy)
    assert not ok and "stray" in detail


def test_doc_truth_passes_on_the_repo(repo_copy):
    ok, detail = doc_truth.run(repo_copy)
    assert ok, detail


def test_doc_truth_catches_tool_dropped_from_a_table(repo_copy):
    p = repo_copy / "docs" / "adapters.md"
    text = "\n".join(l for l in p.read_text(encoding="utf-8").splitlines()
                      if not l.startswith("| Cursor "))
    assert "| Cursor " not in text  # guard: the row we drop must have existed
    p.write_text(text, encoding="utf-8")
    ok, detail = doc_truth.run(repo_copy)
    assert not ok and "cursor" in detail.lower()


def test_doc_truth_catches_stale_backtick_ref_in_workflow(repo_copy):
    p = repo_copy / "docs" / "workflow.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n\nSee `plan-the-thing` next.\n", encoding="utf-8")
    ok, detail = doc_truth.run(repo_copy)
    assert not ok and "plan-the-thing" in detail


def test_doc_truth_catches_stale_single_word_ref(repo_copy):
    # a single-word prompt name (grill, prove, ...) is as checkable as a hyphenated one
    p = repo_copy / "docs" / "workflow.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n\nRun `grull` next.\n", encoding="utf-8")
    ok, detail = doc_truth.run(repo_copy)
    assert not ok and "grull" in detail


def test_structure_catches_missing_file(repo_copy):
    (repo_copy / "README.md").unlink()
    ok, detail = structure.run(repo_copy)
    assert not ok and "README.md" in detail


def test_docs_catches_thin_doc(repo_copy):
    (repo_copy / "docs" / "onboarding.md").write_text("# tiny\n", encoding="utf-8")
    ok, detail = docs.run(repo_copy)
    assert not ok and "onboarding.md" in detail


def test_docs_requires_the_plugin_doc(repo_copy):
    # the plugin doc is required; removing it must fail the docs check
    p = repo_copy / "docs" / "plugin.md"
    p.write_text("# tiny\n", encoding="utf-8")
    ok, detail = docs.run(repo_copy)
    assert not ok and "plugin.md" in detail


def test_docs_requires_the_workflow_hub(repo_copy):
    # the workflow hub is a required doc; thinning it below the floor must fail the docs check
    p = repo_copy / "docs" / "workflow.md"
    p.write_text("# Workflow\n\nstub\n", encoding="utf-8")
    ok, detail = docs.run(repo_copy)
    assert not ok and "workflow.md" in detail


def test_templates_catches_missing_anchor(repo_copy):
    (repo_copy / "templates" / "cursor-rules.md").write_text("# rule\n" + ("word " * 60), encoding="utf-8")
    ok, detail = templates.run(repo_copy)
    assert not ok and "prompt pack" in detail


def test_adapters_catches_path_collision(monkeypatch):
    import kit.adapters.codex as codex
    monkeypatch.setattr(codex, "plan",
                        lambda kit_root, project_root, terse=False:
                        [Action(path=".claude/settings.json", content="x", mode="write")])
    ok, detail = adapters.run(ROOT)
    assert not ok and "collide" in detail


def test_action_rejects_bad_mode():
    # the invariant is enforced at construction, so a typo cannot reach the installer
    with pytest.raises(ValueError):
        Action(path="x", content="y", mode="bogus")


def test_plugin_sync_passes_on_the_repo(repo_copy):
    from kit.checks import plugin_sync
    ok, detail = plugin_sync.run(repo_copy)
    assert ok, detail


def test_plugin_sync_catches_drifted_skill(repo_copy):
    from kit.checks import plugin_sync
    # corrupt a generated skill so it no longer matches the generator output
    skills = list((repo_copy / "plugins" / "outpost" / "skills").glob("*/SKILL.md"))
    assert skills  # guard
    skills[0].write_text("drifted\n", encoding="utf-8")
    ok, detail = plugin_sync.run(repo_copy)
    assert not ok and "drift" in detail.lower()


def test_plugin_sync_catches_command_naming_unknown_prompt(repo_copy):
    from kit.checks import plugin_sync
    cmd = repo_copy / "plugins" / "outpost" / "commands" / "ship.md"
    cmd.write_text(cmd.read_text(encoding="utf-8") + "\n\nThen `not-a-prompt`.\n", encoding="utf-8")
    ok, detail = plugin_sync.run(repo_copy)
    assert not ok and "not-a-prompt" in detail


def test_docs_sync_passes_on_the_repo(repo_copy):
    from kit.checks import docs_sync
    ok, detail = docs_sync.run(repo_copy)
    assert ok, detail


def test_docs_sync_catches_a_hand_edited_generated_span(repo_copy):
    from kit.checks import docs_sync
    p = repo_copy / "docs" / "workflow.md"
    text = p.read_text(encoding="utf-8").replace(
        "<!-- GENERATED:core-count-digits -->27<!-- /GENERATED:core-count-digits -->",
        "<!-- GENERATED:core-count-digits -->99<!-- /GENERATED:core-count-digits -->")
    assert "99" in text  # guard: the corruption must exist
    p.write_text(text, encoding="utf-8")
    ok, detail = docs_sync.run(repo_copy)
    assert not ok
    assert "workflow.md" in detail


def test_docs_sync_catches_a_stripped_required_marker(repo_copy):
    from kit.checks import docs_sync
    p = repo_copy / "docs" / "workflow.md"
    text = p.read_text(encoding="utf-8")
    text = text.replace("<!-- GENERATED:skills-table -->", "").replace("<!-- /GENERATED:skills-table -->", "")
    assert "GENERATED:skills-table" not in text  # guard: the marker must genuinely be gone
    p.write_text(text, encoding="utf-8")
    ok, detail = docs_sync.run(repo_copy)
    assert not ok
    assert "skills-table" in detail


def test_docs_sync_catches_a_hand_edited_roadmap_checks_line(repo_copy):
    from kit.checks import docs_sync
    p = repo_copy / "docs" / "ROADMAP.md"
    # corrupt whatever number-word the generator wrote, so the test does not pin the check count
    # (the word can be hyphenated, e.g. "twenty-one", once the count crosses 20)
    text, n = re.subn(r"(<!-- GENERATED:checks-line -->)[\w-]+ checks",
                      r"\1zero checks", p.read_text(encoding="utf-8"))
    assert n == 1 and "zero checks" in text  # guard: the corruption must exist
    p.write_text(text, encoding="utf-8")
    ok, detail = docs_sync.run(repo_copy)
    assert not ok
    assert "ROADMAP.md" in detail


def test_docs_sync_catches_a_stripped_roadmap_marker(repo_copy):
    from kit.checks import docs_sync
    p = repo_copy / "docs" / "ROADMAP.md"
    text = p.read_text(encoding="utf-8")
    text = text.replace("<!-- GENERATED:checks-line -->", "").replace("<!-- /GENERATED:checks-line -->", "")
    assert "GENERATED:checks-line" not in text  # guard: the marker must genuinely be gone
    p.write_text(text, encoding="utf-8")
    ok, detail = docs_sync.run(repo_copy)
    assert not ok
    assert "checks-line" in detail


def test_catalog_catches_stray_core_file(repo_copy):
    # a .md file under prompts/core/ that is not in the catalog must be caught
    (repo_copy / "prompts" / "core" / "ghost.md").write_text(
        "---\nname: ghost\ndescription: stray core prompt\n---\n# ghost\nbody\n",
        encoding="utf-8",
    )
    ok, detail = catalog.run(repo_copy)
    assert not ok and "not in the catalog" in detail


def test_adapters_catches_invalid_mode(monkeypatch):
    # a plan that tries to build an invalid action surfaces as a check failure, not a crash
    import kit.adapters.cursor as cursor

    def bad_plan(kit_root, project_root, terse=False):
        return [Action(path=".cursor/x", content="x", mode="bogus")]

    monkeypatch.setattr(cursor, "plan", bad_plan)
    ok, detail = adapters.run(ROOT)
    assert not ok and "invalid action" in detail


def test_command_lists_passes_on_the_repo(repo_copy):
    ok, detail = command_lists.run(repo_copy)
    assert ok, detail


def test_command_lists_catches_a_command_dropped_from_the_workflow_hub(repo_copy):
    # a plugin command file on disk but missing from the hub's shortcuts table must fail, naming it
    p = repo_copy / "docs" / "workflow.md"
    text = "\n".join(l for l in p.read_text(encoding="utf-8").splitlines()
                      if not l.startswith("| `/outpost:doctor`"))
    assert "| `/outpost:doctor`" not in text  # guard: the row we drop must have existed
    p.write_text(text, encoding="utf-8")
    ok, detail = command_lists.run(repo_copy)
    assert not ok and "/outpost:doctor" in detail and "workflow.md" in detail


def test_command_lists_catches_a_command_removed_from_table_but_named_in_prose(repo_copy):
    # /outpost:doctor dropped from the hub's shortcuts table but still mentioned in prose must still
    # fail: proves the scan is scoped to the table, not the whole file
    p = repo_copy / "docs" / "workflow.md"
    text = p.read_text(encoding="utf-8")
    assert "| `/outpost:doctor` |" in text  # guard: the row we drop must have existed
    text = "\n".join(l for l in text.splitlines() if not l.startswith("| `/outpost:doctor`"))
    text += "\n\nSee `/outpost:doctor` for details.\n"
    assert "`/outpost:doctor`" in text  # guard: the stray prose mention landed
    p.write_text(text, encoding="utf-8")
    ok, detail = command_lists.run(repo_copy)
    assert not ok and "/outpost:doctor" in detail and "workflow.md" in detail


def test_command_lists_rejects_a_bare_unnamespaced_name(repo_copy):
    # a table row naming the bare `/doctor` form must not satisfy the check: only `/outpost:doctor` counts
    p = repo_copy / "docs" / "workflow.md"
    text = p.read_text(encoding="utf-8").replace("| `/outpost:doctor` |", "| `/doctor` |")
    assert "| `/doctor` |" in text  # guard: the substitution landed
    p.write_text(text, encoding="utf-8")
    ok, detail = command_lists.run(repo_copy)
    assert not ok and "/outpost:doctor" in detail and "workflow.md" in detail


def test_roadmap_catches_stale_current_release(repo_copy):
    # rewrite the ROADMAP "Current release" line to a wrong version; the check must fail
    p = repo_copy / "docs" / "ROADMAP.md"
    text = re.sub(r"Current release:\s*v\d+\.\d+\.\d+", "Current release: v0.0.0",
                  p.read_text(encoding="utf-8"))
    assert "v0.0.0" in text  # guard: the substitution landed
    p.write_text(text, encoding="utf-8")
    ok, detail = roadmap.run(repo_copy)
    assert not ok and "does not match" in detail


def test_traces_catches_a_seeded_personal_email(repo_copy):
    marker = "meshal" + "@example.com"
    (repo_copy / "docs" / "example.md").write_text(f"contact {marker}\n", encoding="utf-8")
    ok, detail = traces.run(repo_copy)
    assert not ok and "personal email" in detail


def test_traces_catches_a_seeded_home_path(repo_copy):
    marker = "C:\\Users\\" + "mesha" + "\\clone"
    (repo_copy / "docs" / "example.md").write_text(f"cloned at {marker}\n", encoding="utf-8")
    ok, detail = traces.run(repo_copy)
    assert not ok and "home directory path" in detail


def test_traces_passes_on_the_clean_copy(repo_copy):
    # CODEOWNERS keeps its handles (allowed home); scratch dirs are skipped in walk mode
    ok, detail = traces.run(repo_copy)
    assert ok, detail


def test_traces_catches_a_seeded_sync_estate_path(repo_copy):
    # doubled backslashes, the JSON-escaped form a manifest would carry
    marker = "Dropbox" + "\\\\Desktop" + "\\\\Projects"
    (repo_copy / "docs" / "example.md").write_text(f"cloned from {marker}\n", encoding="utf-8")
    ok, detail = traces.run(repo_copy)
    assert not ok and "sync estate path" in detail


def test_label_refs_catches_an_unregistered_label_in_a_flow_list(repo_copy):
    forms = repo_copy / ".github" / "ISSUE_TEMPLATE"
    forms.mkdir(parents=True, exist_ok=True)
    (forms / "bug.yml").write_text(
        'name: Bug report\ndescription: x\nlabels: ["type:bug", "needs-triage"]\nbody: []\n',
        encoding="utf-8")
    ok, detail = label_refs.run(repo_copy)
    assert not ok and "needs-triage" in detail


def test_label_refs_catches_an_unregistered_label_in_a_block_list(repo_copy):
    forms = repo_copy / ".github" / "ISSUE_TEMPLATE"
    forms.mkdir(parents=True, exist_ok=True)
    (forms / "feature.yml").write_text(
        "name: Feature request\ndescription: x\nlabels:\n  - type:feature\n  - stale-label\nbody: []\n",
        encoding="utf-8")
    ok, detail = label_refs.run(repo_copy)
    assert not ok and "stale-label" in detail


def test_label_refs_passes_with_only_registered_and_retained_labels(repo_copy):
    forms = repo_copy / ".github" / "ISSUE_TEMPLATE"
    forms.mkdir(parents=True, exist_ok=True)
    (forms / "bug.yml").write_text(
        'name: Bug report\ndescription: x\nlabels: ["type:bug", "area:prompts", "good first issue"]\n'
        "body: []\n",
        encoding="utf-8")
    ok, detail = label_refs.run(repo_copy)
    assert ok, detail


def test_issue_forms_catches_a_duplicate_id(repo_copy):
    forms = repo_copy / ".github" / "ISSUE_TEMPLATE"
    (forms / "bug.yml").write_text(
        "name: Bug report\ndescription: x\nbody:\n"
        "  - type: textarea\n    id: problem\n    attributes:\n      label: Problem\n"
        "  - type: textarea\n    id: problem\n    attributes:\n      label: Problem again\n",
        encoding="utf-8")
    ok, detail = issue_forms.run(repo_copy)
    assert not ok and "duplicate id 'problem'" in detail


def test_issue_forms_catches_a_dropdown_with_no_options(repo_copy):
    forms = repo_copy / ".github" / "ISSUE_TEMPLATE"
    (forms / "bug.yml").write_text(
        "name: Bug report\ndescription: x\nbody:\n"
        "  - type: dropdown\n    id: severity\n    attributes:\n      label: Severity\n"
        "    validations:\n      required: true\n",
        encoding="utf-8")
    ok, detail = issue_forms.run(repo_copy)
    assert not ok and "dropdown field has no options" in detail


def test_issue_forms_catches_a_duplicate_id_with_a_trailing_comment(repo_copy):
    forms = repo_copy / ".github" / "ISSUE_TEMPLATE"
    (forms / "bug.yml").write_text(
        "name: Bug report\ndescription: x\nbody:\n"
        "  - type: textarea\n    id: problem  # first\n    attributes:\n      label: Problem\n"
        "  - type: textarea\n    id: problem\n    attributes:\n      label: Problem again\n",
        encoding="utf-8")
    ok, detail = issue_forms.run(repo_copy)
    assert not ok and "duplicate id 'problem'" in detail


def test_prose_length_catches_a_sprawling_paragraph_in_a_real_doc(repo_copy):
    p = repo_copy / "docs" / "contributing.md"
    long_para = " ".join(["word"] * (prose_length.MAX_PARAGRAPH_WORDS + 1))
    p.write_text(p.read_text(encoding="utf-8") + f"\n\n{long_para}\n", encoding="utf-8")
    ok, detail = prose_length.run(repo_copy)
    assert not ok and "docs/contributing.md" in detail and "paragraph too long" in detail


def test_commands_catches_a_short_description(repo_copy):
    cmd = repo_copy / "plugins" / "outpost" / "commands" / "repo-review.md"
    cmd.write_text(
        '---\ndescription: "short"\n---\n\n# /repo-review\n\nAudit the whole repo and report '
        'findings shaped for triage, covering structure, docs truth, test coverage, and dead '
        'code.\n',
        encoding="utf-8")
    ok, detail = commands.run(repo_copy)
    assert not ok and "repo-review" in detail and "too short" in detail
    assert "body is empty" not in detail and "too thin" not in detail


def test_commands_catches_an_empty_body(repo_copy):
    cmd = repo_copy / "plugins" / "outpost" / "commands" / "repo-review.md"
    cmd.write_text(
        '---\ndescription: "Audit the whole repo: structure, docs truth, tests, dead code, drift."\n---\n',
        encoding="utf-8")
    ok, detail = commands.run(repo_copy)
    assert not ok and "repo-review" in detail and "body is empty" in detail
