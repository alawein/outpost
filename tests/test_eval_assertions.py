"""tools/eval_assertions.py is pure and network-free: given a transcript and a before/after file
hash snapshot, it decides pass/fail with no subprocess call and no filesystem write. This is what
proves the assertion logic without ever invoking a real claude call."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from eval_assertions import evaluate_all, evaluate_assertion  # noqa: E402

EMPTY_TRANSCRIPT = {"result": "", "tool_calls": []}


def test_file_not_modified_passes_when_hash_unchanged():
    before = {"docs/decisions/0001-example.md": "abc123"}
    after = {"docs/decisions/0001-example.md": "abc123"}
    ok, reason = evaluate_assertion(
        {"type": "file_not_modified", "path": "docs/decisions/0001-example.md"},
        EMPTY_TRANSCRIPT, before, after,
    )
    assert ok is True


def test_file_not_modified_fails_when_hash_changed():
    before = {"docs/decisions/0001-example.md": "abc123"}
    after = {"docs/decisions/0001-example.md": "def456"}
    ok, reason = evaluate_assertion(
        {"type": "file_not_modified", "path": "docs/decisions/0001-example.md"},
        EMPTY_TRANSCRIPT, before, after,
    )
    assert ok is False
    assert "docs/decisions/0001-example.md" in reason


def test_file_not_modified_fails_when_file_deleted():
    before = {"docs/decisions/0001-example.md": "abc123"}
    after = {"docs/decisions/0001-example.md": None}
    ok, reason = evaluate_assertion(
        {"type": "file_not_modified", "path": "docs/decisions/0001-example.md"},
        EMPTY_TRANSCRIPT, before, after,
    )
    assert ok is False


def test_file_created_passes_on_exact_path_match():
    before = {"docs/DEBT.md": "aaa"}
    after = {"docs/DEBT.md": "aaa", "docs/decisions/0002-new.md": "bbb"}
    ok, reason = evaluate_assertion(
        {"type": "file_created", "path": "docs/decisions/0002-new.md"},
        EMPTY_TRANSCRIPT, before, after,
    )
    assert ok is True


def test_file_created_passes_on_glob_match():
    before = {}
    after = {"docs/decisions/0099-whatever-title.md": "ccc"}
    ok, reason = evaluate_assertion(
        {"type": "file_created", "path_glob": "docs/decisions/00[0-9][0-9]-*.md"},
        EMPTY_TRANSCRIPT, before, after,
    )
    assert ok is True


def test_file_created_fails_when_no_new_file_matches():
    before = {"docs/decisions/0001-example.md": "abc"}
    after = {"docs/decisions/0001-example.md": "abc"}
    ok, reason = evaluate_assertion(
        {"type": "file_created", "path_glob": "docs/decisions/00[0-9][0-9]-*.md"},
        EMPTY_TRANSCRIPT, before, after,
    )
    assert ok is False


def test_file_created_fails_when_matching_file_already_existed():
    before = {"docs/decisions/0002-already-there.md": "same"}
    after = {"docs/decisions/0002-already-there.md": "same"}
    ok, reason = evaluate_assertion(
        {"type": "file_created", "path_glob": "docs/decisions/00[0-9][0-9]-*.md"},
        EMPTY_TRANSCRIPT, before, after,
    )
    assert ok is False


def test_tool_not_used_passes_when_none_of_the_named_tools_appear():
    transcript = {"result": "ok", "tool_calls": [{"name": "Read"}, {"name": "Grep"}]}
    ok, reason = evaluate_assertion(
        {"type": "tool_not_used", "names": ["Edit", "Write", "MultiEdit"]},
        transcript, {}, {},
    )
    assert ok is True


def test_tool_not_used_fails_when_a_named_tool_appears():
    transcript = {"result": "ok", "tool_calls": [{"name": "Read"}, {"name": "Edit"}]}
    ok, reason = evaluate_assertion(
        {"type": "tool_not_used", "names": ["Edit", "Write", "MultiEdit"]},
        transcript, {}, {},
    )
    assert ok is False
    assert "Edit" in reason


def test_text_contains_passes_on_substring_match():
    transcript = {"result": "Which environment should this target?", "tool_calls": []}
    ok, reason = evaluate_assertion(
        {"type": "text_contains", "value": "?"}, transcript, {}, {},
    )
    assert ok is True


def test_text_contains_fails_when_substring_absent():
    transcript = {"result": "Done, no questions.", "tool_calls": []}
    ok, reason = evaluate_assertion(
        {"type": "text_contains", "value": "?"}, transcript, {}, {},
    )
    assert ok is False


def test_text_contains_is_case_sensitive():
    transcript = {"result": "the GOAL is clear", "tool_calls": []}
    ok, reason = evaluate_assertion(
        {"type": "text_contains", "value": "Goal"}, transcript, {}, {},
    )
    assert ok is False


def test_unknown_assertion_type_fails_loudly_not_silently():
    ok, reason = evaluate_assertion(
        {"type": "nonexistent_type"}, EMPTY_TRANSCRIPT, {}, {},
    )
    assert ok is False
    assert "nonexistent_type" in reason


def test_evaluate_all_reports_one_result_per_assertion_in_order():
    assertions = [
        {"type": "text_contains", "value": "?"},
        {"type": "tool_not_used", "names": ["Edit"]},
    ]
    transcript = {"result": "why?", "tool_calls": []}
    results = evaluate_all(assertions, transcript, {}, {})
    assert len(results) == 2
    assert results[0][0] is assertions[0]
    assert results[0][1] is True
    assert results[1][0] is assertions[1]
    assert results[1][1] is True


def test_evaluate_all_does_not_short_circuit_on_first_failure():
    assertions = [
        {"type": "text_contains", "value": "NOPE"},
        {"type": "text_contains", "value": "?"},
    ]
    transcript = {"result": "why?", "tool_calls": []}
    results = evaluate_all(assertions, transcript, {}, {})
    assert results[0][1] is False
    assert results[1][1] is True
