"""The install manifest records each tool's installed prompts, accumulates across tools, and
fails cleanly on a malformed file."""
import json

import pytest

from kit.installers.manifest import (
    MANIFEST_PATH, dumps, merge_manifest, parse_manifest)


def test_path_is_under_a_dotdir():
    assert MANIFEST_PATH == ".outpost/manifest.json"


def test_records_selection_and_sorted_prompts():
    out = merge_manifest({}, {"claude": {"selection": "only", "prompts": ["write-tests", "plan-change"]}}, "0.10.0")
    assert out["kit_version"] == "0.10.0"
    assert out["tools"]["claude"] == {"selection": "only", "prompts": ["plan-change", "write-tests"],
                                      "terse": False}


def test_records_terse_when_set():
    out = merge_manifest({}, {"claude": {"selection": "full", "prompts": ["a"], "terse": True}}, "0.10.0")
    assert out["tools"]["claude"]["terse"] is True


def test_accumulates_a_second_tool_without_dropping_the_first():
    first = merge_manifest({}, {"claude": {"selection": "full", "prompts": ["a", "b"]}}, "0.10.0")
    second = merge_manifest(first, {"codex": {"selection": "only", "prompts": ["a"]}}, "0.10.0")
    assert set(second["tools"]) == {"claude", "codex"}


def test_reinstall_of_one_tool_updates_only_its_entry_and_version():
    first = merge_manifest({}, {"claude": {"selection": "only", "prompts": ["a"]}}, "0.10.0")
    second = merge_manifest(first, {"claude": {"selection": "full", "prompts": ["a", "b"]}}, "0.11.0")
    assert second["kit_version"] == "0.11.0"
    assert second["tools"]["claude"]["selection"] == "full"


def test_dumps_is_canonical_and_round_trips():
    # install.py writes the record as dumps(merge_manifest(...)); prove that path is canonical.
    text = dumps(merge_manifest({}, {"claude": {"selection": "full", "prompts": ["b", "a"]}}, "0.10.0"))
    assert text.endswith("\n")
    assert json.loads(text)["tools"]["claude"]["prompts"] == ["a", "b"]


def test_merge_rejects_malformed_tools():
    with pytest.raises(ValueError):
        merge_manifest({"tools": ["not", "an", "object"]}, {}, "0.10.0")


def test_parse_manifest_accepts_a_valid_manifest():
    text = dumps(merge_manifest({}, {"claude": {"selection": "only", "prompts": ["a"]}}, "0.10.0"))
    assert parse_manifest(text)["tools"]["claude"]["prompts"] == ["a"]


def test_parse_manifest_rejects_bad_json():
    with pytest.raises(ValueError):
        parse_manifest("{ not json")


def test_parse_manifest_rejects_non_object_top_level():
    with pytest.raises(ValueError):
        parse_manifest("[]")


def test_parse_manifest_rejects_tools_not_an_object():
    with pytest.raises(ValueError):
        parse_manifest('{"tools": ["nope"]}')


def test_parse_manifest_rejects_prompts_not_a_string_list():
    with pytest.raises(ValueError):
        parse_manifest('{"tools": {"claude": {"selection": "only", "prompts": "plan-change"}}}')


def test_parse_manifest_rejects_parent_traversal_file_key():
    # a crafted manifest in a cloned repo must not steer --prune/--remove outside the project
    with pytest.raises(ValueError):
        parse_manifest('{"tools": {"codex": {"prompts": [], "selection": "full", '
                       '"files": {"../victim/.git/HEAD": {"existed": false}}}}}')


def test_parse_manifest_rejects_absolute_file_key():
    with pytest.raises(ValueError):
        parse_manifest('{"tools": {"codex": {"prompts": [], "selection": "full", '
                       '"files": {"/etc/passwd": {"existed": false}}}}}')


def test_parse_manifest_accepts_a_normal_relative_file_key():
    data = parse_manifest('{"tools": {"codex": {"prompts": [], "selection": "full", '
                          '"files": {".agents/prompts/grill.md": {"existed": false}}}}}')
    assert ".agents/prompts/grill.md" in data["tools"]["codex"]["files"]
