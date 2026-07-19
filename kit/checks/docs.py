"""The required docs exist and clear a word-count floor (a proxy for not-a-stub). An empty or
missing doc fails the gate. Matching shipped behavior is the author's job, not enforced here."""
from __future__ import annotations

import pathlib

REQUIRED_DOCS = {
    "README.md": 80,
    "docs/onboarding.md": 60,
    "docs/workflow.md": 200,
    "docs/writing-standard.md": 40,
    "docs/adapters.md": 60,
    "docs/contributing.md": 60,
    "docs/releasing.md": 60,
    "docs/ROADMAP.md": 120,
    "docs/cadence.md": 120,
    "docs/decisions/README.md": 20,
    "docs/decisions/0000-template.md": 20,
    "docs/plugin.md": 120,
    "docs/token-budget.md": 200,
    "docs/dogfooding.md": 120,
    "docs/DEBT.md": 60,
}


def run(root: pathlib.Path) -> tuple[bool, str]:
    errors: list[str] = []
    for rel, min_words in REQUIRED_DOCS.items():
        p = root / rel
        if not p.is_file():
            errors.append(f"{rel}: missing")
            continue
        words = len(p.read_text(encoding="utf-8").split())
        if words < min_words:
            errors.append(f"{rel}: too thin ({words} words, want >= {min_words})")
    if errors:
        return False, "; ".join(errors[:10])
    return True, f"{len(REQUIRED_DOCS)} docs present with real content"
