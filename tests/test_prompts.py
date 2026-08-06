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

    for term in (
        "read-only inventory",
        "dirty repo",
        "source evidence",
        "confidence",
        "route",
        "verification command copied from the target repo",
        "repo-defined commands",
        "evidence gate",
        "triage",
        "baseline gate",
        "final gate",
        "refactor test parity",
        "explicit authority",
    ):
        assert term in text
