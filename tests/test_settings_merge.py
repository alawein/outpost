"""The settings merge adds only what it should, preserves the rest, and fails cleanly on a
malformed file."""
import json

import pytest

from kit.installers.settings import SECRET_DENY, merge_settings, merged_text


def test_adds_secret_deny_rules_to_empty():
    out = merge_settings({})
    for rule in SECRET_DENY:
        assert rule in out["permissions"]["deny"]


def test_preserves_unrelated_keys():
    existing = {"model": "opus", "permissions": {"allow": ["Bash(ls)"], "deny": ["Read(./foo)"]}}
    out = merge_settings(existing)
    assert out["model"] == "opus"
    assert "Bash(ls)" in out["permissions"]["allow"]
    assert "Read(./foo)" in out["permissions"]["deny"]
    for rule in SECRET_DENY:
        assert rule in out["permissions"]["deny"]


def test_is_idempotent():
    once = merge_settings({})
    twice = merge_settings(once)
    assert once == twice


def test_output_style_set_only_when_given():
    assert "outputStyle" not in merge_settings({})
    assert merge_settings({}, output_style="terse")["outputStyle"] == "terse"


def test_malformed_permissions_type_raises():
    with pytest.raises(ValueError):
        merge_settings({"permissions": ["not", "an", "object"]})


def test_malformed_deny_type_raises():
    with pytest.raises(ValueError):
        merge_settings({"permissions": {"deny": "should-be-a-list"}})


def test_merged_text_handles_blank_and_bad_json():
    assert json.loads(merged_text(""))["permissions"]["deny"]
    assert json.loads(merged_text(None))["permissions"]["deny"]
    with pytest.raises(ValueError):
        merged_text("{ not json")
