"""Templates exist, carry content, and point at the prompt pack. A template that no longer
references the prompts has drifted from what the adapters install."""
from __future__ import annotations

import pathlib

from . import banned_hits

TEMPLATES = ("CLAUDE.md", "AGENTS.md", "cursor-rules.md", "copilot-instructions.md",
             "windsurf-rules.md", "GEMINI.md")
# A few prompt names a healthy template should reference, so it stays tied to the pack.
ANCHOR_PROMPTS = ("plan-change", "handoff-session")


def run(root: pathlib.Path) -> tuple[bool, str]:
    errors: list[str] = []
    for name in TEMPLATES:
        p = root / "templates" / name
        if not p.is_file():
            errors.append(f"{name}: missing")
            continue
        text = p.read_text(encoding="utf-8")
        if len(text.split()) < 40:
            errors.append(f"{name}: too thin to be a real template")
        for anchor in ANCHOR_PROMPTS:
            if anchor not in text:
                errors.append(f"{name}: does not reference the prompt pack ({anchor!r} missing)")
        errors += [f"{name}: banned register word {w!r}" for w in banned_hits(text)]
    if errors:
        return False, "; ".join(errors[:10])
    return True, f"{len(TEMPLATES)} templates present and tied to the prompt pack"
