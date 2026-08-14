"""kit/checks/issue_forms.py's two pure scan functions (duplicate_ids, fields_missing_options),
tested directly against small in-memory YAML snippets before the check is wired into the gate."""
from kit.checks.issue_forms import duplicate_ids, fields_missing_options


def test_duplicate_ids_finds_a_repeated_id():
    lines = [
        "body:",
        "  - type: textarea",
        "    id: problem",
        "  - type: textarea",
        "    id: problem",
    ]
    assert duplicate_ids(lines) == ["problem"]


def test_duplicate_ids_passes_when_all_unique():
    lines = ["  - type: textarea", "    id: a", "  - type: textarea", "    id: b"]
    assert duplicate_ids(lines) == []


def test_fields_missing_options_catches_a_dropdown_with_no_options_key():
    lines = [
        "  - type: dropdown",
        "    id: severity",
        "    attributes:",
        "      label: Severity",
        "    validations:",
        "      required: true",
    ]
    assert fields_missing_options(lines) == ["dropdown"]


def test_fields_missing_options_catches_an_options_key_with_no_items():
    lines = [
        "  - type: checkboxes",
        "    id: confirm",
        "    attributes:",
        "      options:",
        "  - type: textarea",
        "    id: next_field",
    ]
    assert fields_missing_options(lines) == ["checkboxes"]


def test_fields_missing_options_passes_when_options_present():
    lines = [
        "  - type: dropdown",
        "    id: severity",
        "    attributes:",
        "      options:",
        "        - low",
        "        - high",
    ]
    assert fields_missing_options(lines) == []


def test_fields_missing_options_ignores_textarea_and_input_fields():
    lines = ["  - type: textarea", "    id: notes"]
    assert fields_missing_options(lines) == []
