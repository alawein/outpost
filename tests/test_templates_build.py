"""The guide templates build from one shared core plus a per-tool head, and the committed files
match that build."""
import json
import pathlib

import pytest

from kit.templates_build import build_templates
from kit.checks import templates_sync

ROOT = pathlib.Path(__file__).resolve().parents[1]

EXPECTED_PATHS = {
    "templates/CLAUDE.md",
    "templates/AGENTS.md",
    "templates/cursor-rules.md",
    "templates/copilot-instructions.md",
}


def test_build_covers_every_catalog_template():
    assert set(build_templates(ROOT)) == EXPECTED_PATHS


def test_every_built_guide_carries_both_anchors():
    # the templates check requires plan-change and handoff-session in each file; they live in the
    # shared core, so every built guide carries them
    for content in build_templates(ROOT).values():
        assert "plan-change" in content
        assert "handoff-session" in content


def test_committed_guides_match_the_build():
    # the heart of the fix: what is on disk equals head + shared core, so the four cannot drift
    for rel, content in build_templates(ROOT).items():
        assert (ROOT / rel).read_text(encoding="utf-8") == content


def test_templates_sync_passes_on_the_real_repo():
    ok, detail = templates_sync.run(ROOT)
    assert ok, detail


def test_templates_sync_flags_a_drifted_guide(tmp_path):
    # a tiny kit root: one-entry catalog, the two sources, and a committed file that is NOT the
    # build. The check must fail. Same tiny-root idiom test_adapters uses.
    cat = tmp_path / "kit" / "catalog"
    cat.mkdir(parents=True)
    (cat / "catalog.json").write_text(json.dumps({
        "version": "0.0.0", "stages": [], "prompts": [], "adapters": [], "checks": [],
        "templates": [{"name": "x", "path": "templates/X.md"}],
    }), encoding="utf-8")
    src = tmp_path / "templates" / "_src"
    (src / "head").mkdir(parents=True)
    (src / "core.md").write_text("## Core\n\nshared body\n", encoding="utf-8")
    (src / "head" / "x.md").write_text("# Head\n\nintro\n", encoding="utf-8")
    (tmp_path / "templates" / "X.md").write_text("hand-edited, not the build\n", encoding="utf-8")
    ok, detail = templates_sync.run(tmp_path)
    assert not ok and "drift" in detail


def _tiny_catalog(tmp_path):
    cat = tmp_path / "kit" / "catalog"
    cat.mkdir(parents=True)
    (cat / "catalog.json").write_text(json.dumps({
        "version": "0.0.0", "stages": [], "prompts": [], "adapters": [], "checks": [],
        "templates": [{"name": "x", "path": "templates/X.md"}],
    }), encoding="utf-8")


def test_templates_sync_surfaces_a_missing_source(tmp_path):
    # no core.md: build_templates raises ValueError, the check returns it as a clean (False, detail)
    _tiny_catalog(tmp_path)
    (tmp_path / "templates" / "_src").mkdir(parents=True)
    ok, detail = templates_sync.run(tmp_path)
    assert not ok and "core" in detail


def test_build_names_the_file_on_an_unreadable_source(tmp_path):
    # a non-UTF-8 head must fail loudly AND name the file, not surface a bare codec error
    _tiny_catalog(tmp_path)
    src = tmp_path / "templates" / "_src"
    (src / "head").mkdir(parents=True)
    (src / "core.md").write_text("## Core\n", encoding="utf-8")
    (src / "head" / "x.md").write_bytes(b"\xff\xfe not utf-8")
    with pytest.raises(ValueError, match="head"):
        build_templates(tmp_path)
