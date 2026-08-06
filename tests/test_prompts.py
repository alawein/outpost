"""Every shipped prompt is complete: it lints clean against the prompt contract."""
import pathlib

from kit.catalog import load_catalog
from kit.checks.prompts import lint_prompt

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORE = ROOT / "prompts" / "core"

EXPECTED = {p["name"] for p in load_catalog(ROOT / "kit" / "catalog" / "catalog.json").prompts}


def test_all_prompts_present():
    assert {p.stem for p in CORE.glob("*.md")} == EXPECTED


def test_every_prompt_lints_clean():
    for p in sorted(CORE.glob("*.md")):
        errors = lint_prompt(p.read_text(encoding="utf-8"), p.stem)
        assert errors == [], (p.stem, errors)


def test_repo_hygiene_sweep_binds_evidence_before_mutation():
    text = (CORE / "repo-hygiene-sweep.md").read_text(encoding="utf-8").lower()

    assert "read-only inventory" in text
    assert "do not edit a dirty target" in text
    assert "do not edit an archived target" in text
    assert "do not edit a generated target" in text
    assert "do not edit a vendored target" in text
    assert "do not edit an untested target" in text
    assert "do not edit an unreadable target" in text
    assert "source evidence" in text
    assert "confidence" in text
    assert "route" in text
    assert "verification command copied from the target repo" in text
    assert "repo-defined commands" in text
    assert "inspect each copied command's effects before execution" in text
    assert "read-only local checks may run" in text
    assert "move requires explicit authority" in text
    assert "delete requires explicit authority" in text
    assert "archive requires explicit authority" in text
    assert "commit requires explicit authority" in text
    assert "push requires explicit authority" in text
    assert "dependency change requires explicit authority" in text
    assert "external action requires explicit authority" in text
    assert "evidence gate" in text
    assert "triage" in text
    assert "baseline gate" in text
    assert "final gate" in text
    assert "refactor test parity" in text
    assert "explicit authority" in text

    assert text.index("topology and catalog optimization") < text.index("workflow triage")
    assert text.index("workflow triage") < text.index("simplification")
    assert text.index("simplification") < text.index("technical debt reduction")
    assert text.index("technical debt reduction") < text.index("behavior-preserving refactoring")
