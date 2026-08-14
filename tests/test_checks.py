"""The gate is green on the real repo, and each check actually catches its violation."""
import pathlib
import re
import subprocess

from kit.checks import commands, issue_forms, label_refs, prompts, secrets, voice
from kit.checks.run import run_all

ROOT = pathlib.Path(__file__).resolve().parents[1]

GOOD_PROMPT = (ROOT / "prompts" / "core" / "plan-change.md").read_text(encoding="utf-8")


def test_gate_is_green():
    results = run_all(ROOT)
    failed = [(name, detail) for name, ok, detail in results if not ok]
    assert not failed, failed


def test_run_all_reports_a_clean_failure_on_a_malformed_catalog(tmp_path):
    # a malformed catalog must not crash run_all with an uncaught exception: the runner turns
    # every individual check's exception into a reported failure, and the catalog load itself
    # (which happens before any check can run) must get the same treatment
    catalog_dir = tmp_path / "kit" / "catalog"
    catalog_dir.mkdir(parents=True)
    (catalog_dir / "catalog.json").write_text("not valid json", encoding="utf-8")
    results = run_all(tmp_path)
    assert len(results) == 1
    name, ok, detail = results[0]
    assert name == "catalog"
    assert ok is False
    assert "not valid JSON" in detail or "JSON" in detail


def test_prompt_lint_passes_on_real_prompt():
    assert prompts.lint_prompt(GOOD_PROMPT, "plan-change") == []


def test_prompt_lint_flags_a_stub():
    errors = prompts.lint_prompt("---\nname: x\n---\n# x\nthin", "x")
    assert errors


def test_prompt_lint_flags_missing_sections():
    text = "---\nname: x\ndescription: a real description that is plenty long to pass the length bar\n---\n# x\n" + ("word " * 80)
    errors = prompts.lint_prompt(text, "x")
    assert any("section" in e for e in errors)


def test_prompt_lint_flags_h1_missing_even_with_h2_present():
    # "# " is a substring of "## ", so a naive substring check on the whole body never fires when
    # only H2+ headings are present. A prompt with real section H2s but no true H1 must still fail.
    text = (
        "---\nname: stub\ndescription: " + "x" * 45 + "\n---\n"
        "## When to use\n\n" + ("word " * 15) + "\n\n"
        "## Required inputs\n\n" + ("word " * 15) + "\n\n"
        "## Steps\n\n" + ("word " * 15) + "\n\n"
        "## Output format\n\n" + ("word " * 15) + "\n\n"
        "## Stop conditions\n\n" + ("word " * 15) + "\n"
    )
    errors = prompts.lint_prompt(text, "stub")
    assert any("no H1 heading" in e for e in errors), errors


def test_prompt_lint_flags_banned_word():
    text = GOOD_PROMPT.replace("Most wasted work", "A robust approach to wasted work")
    assert any("banned" in e for e in prompts.lint_prompt(text, "plan-change"))


def _with_description(text, description):
    return re.sub(r"(?m)^description:.*$", "description: " + description, text)


def test_prompt_lint_flags_an_unquoted_colon_in_the_description():
    # the pre-fix converge description (audit F3): an unquoted ": " turns the scalar into a
    # nested mapping, the frontmatter stops being valid YAML, and hosts drop all of it
    bad = _with_description(
        GOOD_PROMPT,
        "Use when you want to drive an artifact to clean: run the full check set and re-run.")
    assert any("colon" in e for e in prompts.lint_prompt(bad, "plan-change"))


def test_prompt_lint_flags_a_value_ending_in_a_colon():
    bad = _with_description(GOOD_PROMPT, "Use when you want to drive an artifact to clean:")
    assert any("colon" in e for e in prompts.lint_prompt(bad, "plan-change"))


def test_prompt_lint_accepts_a_quoted_colon():
    quoted = _with_description(
        GOOD_PROMPT,
        '"Drive an artifact to clean: run the full check set until nothing remains or a cap."')
    assert prompts.lint_prompt(quoted, "plan-change") == []


def test_prompt_lint_flags_an_unterminated_quoted_value():
    bad = _with_description(
        GOOD_PROMPT,
        '"Drive an artifact to clean until nothing remains or a cap, then report honestly.')
    assert any("quote" in e for e in prompts.lint_prompt(bad, "plan-change"))


def test_prompt_lint_flags_a_plain_value_starting_with_a_yaml_indicator():
    bad = _with_description(
        GOOD_PROMPT,
        "[Use before writing code for any change that is not trivial, to scope the edit first]")
    assert any("indicator" in e for e in prompts.lint_prompt(bad, "plan-change"))


def test_commands_lints_every_real_plugin_command():
    ok, detail = commands.run(ROOT)
    assert ok and "9 plugin commands well-formed" in detail, detail


def test_voice_passes_clean_and_flags_a_dash(tmp_path):
    (tmp_path / "clean.md").write_text("# Clean\n\nNo dashes here.\n", encoding="utf-8")
    ok, _ = voice.run(tmp_path)
    assert ok
    (tmp_path / "dirty.md").write_text("# Dirty\n\nThis has an em-dash — right here.\n", encoding="utf-8")
    ok, detail = voice.run(tmp_path)
    assert not ok and "dash" in detail


def _git(path, *args):
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)


def test_voice_scans_tracked_files_only_in_a_git_repo(tmp_path):
    # In a git repo, untracked scratch (e.g. an SDD brief) must not trip the gate, but a tracked
    # doc with a dash still must. This is the kit's own landmine: walk_markdown used to rglob all .md.
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "t@t.test")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "tracked.md").write_text("# Clean\n\nNo dashes here.\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.md")
    _git(tmp_path, "commit", "-m", "add tracked")

    (tmp_path / "scratch.md").write_text("# Scratch\n\nAn untracked em-dash — here.\n", encoding="utf-8")
    ok, _ = voice.run(tmp_path)
    assert ok, "untracked .md with a dash must not fail voice"

    (tmp_path / "tracked.md").write_text("# Bad\n\nA tracked em-dash — here.\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.md")
    ok, detail = voice.run(tmp_path)
    assert not ok and "dash" in detail, "tracked .md with a dash must still fail voice"


def test_secrets_passes_with_gitignore_no_git(tmp_path):
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    # not a git repo, so the tracked-file scan is skipped; the gitignore path still passes
    ok, _ = secrets.run(tmp_path)
    assert ok


def test_secrets_flags_missing_gitignore(tmp_path):
    ok, detail = secrets.run(tmp_path)
    assert not ok and ".env" in detail


def test_secret_pattern_matches_private_key():
    # Assemble the header from parts so this test file does not itself contain a contiguous
    # key marker for the secrets check to flag.
    key = "-----BEGIN RSA PRIVATE" + " KEY-----\nabc\n-----END KEY-----"
    assert any(rx.search(key) for _, rx in secrets.SECRET_PATTERNS)


def test_secrets_scans_pem_and_extensionless_keys(tmp_path):
    # working-tree fallback (no git): a key in a .pem and in an extensionless file must be caught.
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    (tmp_path / "key.pem").write_text("-----BEGIN RSA PRIVATE" + " KEY-----\nx\n", encoding="utf-8")
    ok, detail = secrets.run(tmp_path)
    assert not ok and "key.pem" in detail
    (tmp_path / "key.pem").unlink()
    (tmp_path / "id_rsa").write_text("-----BEGIN OPENSSH PRIVATE" + " KEY-----\nx\n", encoding="utf-8")
    ok, detail = secrets.run(tmp_path)
    assert not ok and "id_rsa" in detail


def test_secrets_scan_runs_without_git(tmp_path):
    # no git repo: the scan still runs over the working tree instead of skipping
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    ok, detail = secrets.run(tmp_path)
    assert ok and "working-tree" in detail


def test_secrets_flags_an_aws_key(tmp_path):
    # split the literal so this test file does not itself carry a contiguous AWS key
    aws = "AKIA" + "1234567890ABCDEF"
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    (tmp_path / "config.txt").write_text(f"aws_key = {aws}\n", encoding="utf-8")
    ok, detail = secrets.run(tmp_path)
    assert not ok and "AWS access key id" in detail


def test_secrets_scans_non_utf8_file(tmp_path):
    # a key in a non-UTF-8 file used to be skipped; the latin-1 read now scans it (fail closed)
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    (tmp_path / "weird.txt").write_bytes(b"\xff\xfe-----BEGIN RSA PRIVATE" + b" KEY-----\n")
    ok, detail = secrets.run(tmp_path)
    assert not ok and "weird.txt" in detail


def test_secrets_flags_tracked_env_and_junk(tmp_path):
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    (tmp_path / ".env").write_text("TOKEN=x\n", encoding="utf-8")
    (tmp_path / "stale.pyc").write_text("x", encoding="utf-8")
    ok, detail = secrets.run(tmp_path)
    assert not ok and ".env" in detail and "junk" in detail


def test_voice_flags_any_non_ascii_not_just_dashes(tmp_path):
    # A curly quote and an accented letter are not dashes, so the dash regex alone misses them.
    curly = f"# Doc\n\nA {chr(0x201C)}curly{chr(0x201D)} quote.\n"
    (tmp_path / "quote.md").write_text(curly, encoding="utf-8")
    ok, detail = voice.run(tmp_path)
    assert not ok and "non-ascii" in detail and "U+201C" in detail
    (tmp_path / "quote.md").unlink()
    accented = f"# Doc\n\nAn accented caf{chr(0xE9)}.\n"
    (tmp_path / "accent.md").write_text(accented, encoding="utf-8")
    ok, detail = voice.run(tmp_path)
    assert not ok and "non-ascii" in detail


def test_voice_reports_a_dash_only_file_as_a_dash_not_generic_non_ascii(tmp_path):
    # The dash message is clearer, so a file whose only non-ASCII is a dash keeps it.
    dashed = f"# Doc\n\nAn em-dash {chr(0x2014)} here.\n"
    (tmp_path / "dash.md").write_text(dashed, encoding="utf-8")
    ok, detail = voice.run(tmp_path)
    assert not ok and "dash" in detail and "non-ascii" not in detail


def test_label_refs_extracts_and_validates_every_real_issue_form():
    # a plain ok-True would also pass under a "never fails" regression; pin the scanned file
    # count too (the 5 files under .github/ISSUE_TEMPLATE/, including config.yml, which carries
    # no labels: key but is still scanned), so a form silently disappearing from the glob fails
    ok, detail = label_refs.run(ROOT)
    assert ok and "5 file(s)" in detail, detail


def test_issue_forms_has_no_duplicate_ids_or_missing_options():
    ok, detail = issue_forms.run(ROOT)
    assert ok and "5 issue form(s)" in detail, detail


def test_extract_label_refs_handles_a_zero_indent_block_list():
    text = "labels:\n- type:bug\n- area:docs\n"
    assert label_refs.extract_label_refs(text) == ["type:bug", "area:docs"]


def test_extract_label_refs_skips_a_comment_inside_a_block_list():
    text = "labels:\n  - type:bug\n  # a note\n  - area:docs\n"
    assert label_refs.extract_label_refs(text) == ["type:bug", "area:docs"]


def test_extract_label_refs_strips_a_trailing_comment_on_a_flow_list():
    text = 'labels: ["type:bug", "area:docs"]  # keep in sync with the registry\n'
    assert label_refs.extract_label_refs(text) == ["type:bug", "area:docs"]


def test_extract_label_refs_zero_indent_block_list_stops_at_a_sibling_key():
    text = "labels:\n- type:bug\nbody:\n- type: markdown\n"
    assert label_refs.extract_label_refs(text) == ["type:bug"]


def test_label_refs_passes_with_nothing_to_check(tmp_path):
    # no .github/ISSUE_TEMPLATE and no .github/labeler.yml: the check must not fail closed
    (tmp_path / "kit" / "labels").mkdir(parents=True)
    (tmp_path / "kit" / "labels" / "registry.json").write_text(
        (pathlib.Path(__file__).resolve().parents[1] / "kit" / "labels" / "registry.json")
        .read_text(encoding="utf-8"),
        encoding="utf-8")
    ok, detail = label_refs.run(tmp_path)
    assert ok and "nothing to check" in detail


def test_extract_label_refs_flow_list():
    text = 'labels: ["type:bug", "area:docs"]\n'
    assert label_refs.extract_label_refs(text) == ["type:bug", "area:docs"]


def test_extract_label_refs_block_list():
    text = "labels:\n  - type:bug\n  - area:docs\nbody: []\n"
    assert label_refs.extract_label_refs(text) == ["type:bug", "area:docs"]


def test_extract_label_refs_stops_at_lower_indentation():
    text = "labels:\n  - type:bug\nbody:\n  - type: markdown\n"
    assert label_refs.extract_label_refs(text) == ["type:bug"]


def test_extract_label_refs_ignores_text_with_no_labels_key():
    assert label_refs.extract_label_refs("name: Bug\ndescription: x\n") == []


def test_voice_flags_banned_register_but_exempts_the_standard(tmp_path):
    (tmp_path / "doc.md").write_text("# Doc\n\nThis is a robust solution.\n", encoding="utf-8")
    ok, detail = voice.run(tmp_path)
    assert not ok and "banned register" in detail
    (tmp_path / "doc.md").unlink()
    # the writing standard names the banned words to ban them, so it is exempt
    std = tmp_path / "docs" / "writing-standard.md"
    std.parent.mkdir()
    std.write_text("# Standard\n\nDo not use: robust, comprehensive, leverage.\n", encoding="utf-8")
    ok, _ = voice.run(tmp_path)
    assert ok
