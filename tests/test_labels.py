"""The label registry is well-formed and internally consistent: no network required."""
import pathlib
import re

import pytest

from kit.labels import load_labels

ROOT = pathlib.Path(__file__).resolve().parents[1]
HEX_COLOR = re.compile(r"^[0-9a-f]{6}$")


@pytest.fixture
def registry():
    return load_labels(ROOT / "kit" / "labels" / "registry.json")


def test_registry_loads_from_the_real_file(registry):
    assert registry.labels
    assert registry.migration
    assert registry.retained_defaults


def test_every_label_is_namespaced_with_a_known_family(registry):
    families = {"type", "area", "priority", "status", "release", "provenance"}
    for label in registry.labels:
        assert ":" in label["name"], label["name"]
        family, _, rest = label["name"].partition(":")
        assert family in families, label["name"]
        assert rest, label["name"]


def test_no_duplicate_label_names(registry):
    names = [label["name"] for label in registry.labels]
    assert len(names) == len(set(names))


def test_every_color_is_a_deterministic_six_digit_hex(registry):
    for label in registry.labels:
        assert HEX_COLOR.match(label["color"]), label["name"]


def test_every_label_has_a_real_description(registry):
    for label in registry.labels:
        assert len(label["description"]) >= 10, label["name"]


def test_migration_targets_are_real_registered_labels(registry):
    for old_name, targets in registry.migration.items():
        for target in targets:
            assert target in registry.names, (old_name, target)


def test_migration_source_is_a_current_github_default():
    # the three defaults this policy supersedes; catches a typo in the migration key itself
    from kit.labels import load_labels as _load
    reg = _load(ROOT / "kit" / "labels" / "registry.json")
    assert set(reg.migration) == {"bug", "enhancement", "documentation"}


def test_retained_defaults_have_no_namespaced_overlap(registry):
    assert not (set(registry.retained_defaults) & registry.names)


def test_known_names_is_the_union(registry):
    assert registry.known_names == registry.names | set(registry.retained_defaults)


def test_family_helper():
    assert load_labels(ROOT / "kit" / "labels" / "registry.json").family("type:bug") == "type"
    assert load_labels(ROOT / "kit" / "labels" / "registry.json").family("wontfix") is None


def test_load_labels_raises_on_malformed_json(tmp_path):
    p = tmp_path / "registry.json"
    p.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        load_labels(p)


def test_load_labels_raises_on_missing_top_level_key(tmp_path):
    p = tmp_path / "registry.json"
    p.write_text('{"labels": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="missing top-level key"):
        load_labels(p)
