"""The catalog loads, matches the version sources, and points at files that exist."""
import json
import pathlib
import re

import pytest

from kit import KIT_VERSION
from kit.catalog import load_catalog

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_catalog_loads():
    cat = load_catalog(ROOT / "kit" / "catalog" / "catalog.json")
    assert cat.prompts and cat.templates and cat.adapters and cat.checks


def test_version_agrees_across_sources():
    cat = load_catalog(ROOT / "kit" / "catalog" / "catalog.json")
    pj = re.search(r'(?m)^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pj and pj.group(1) == cat.version == KIT_VERSION


def test_every_listed_prompt_exists():
    cat = load_catalog(ROOT / "kit" / "catalog" / "catalog.json")
    for p in cat.prompts:
        assert (ROOT / p["path"]).is_file(), p["path"]


def test_malformed_catalog_raises(tmp_path):
    bad = tmp_path / "catalog.json"
    bad.write_text("{ not json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_catalog(bad)


def test_missing_key_raises(tmp_path):
    bad = tmp_path / "catalog.json"
    bad.write_text(json.dumps({"version": "0.1.0", "prompts": []}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_catalog(bad)


def test_missing_file_raises_valueerror(tmp_path):
    # the contract is one error type: a missing file is a ValueError, not FileNotFoundError
    with pytest.raises(ValueError):
        load_catalog(tmp_path / "does-not-exist.json")


def test_catalog_has_stages_and_every_core_prompt_references_one():
    cat = load_catalog(ROOT / "kit" / "catalog" / "catalog.json")
    assert cat.stages, "catalog must carry a non-empty stages list"
    stage_names = {s["name"] for s in cat.stages}
    for p in cat.prompts:
        assert p.get("stage") in stage_names, (
            f"{p['name']!r} has no stage, or an unknown one: {p.get('stage')!r}"
        )
