"""House voice in markdown: plain ASCII everywhere, and no banned register in shipped prose.
Em and en-dashes keep their own named error, since they are the commonest slip; the general
non-ASCII scan rejects every other character over 127. The writing standard and the ledger-voice
output style are exempt from the banned scan, since each names those words to ban them.
"""
from __future__ import annotations

import pathlib
import re

from . import banned_hits, walk_markdown

DASH = re.compile("[–—]")
NON_ASCII = re.compile(r"[^\x00-\x7f]")
BANNED_EXEMPT = {
    "docs/writing-standard.md",
    "plugins/outpost/output-styles/ledger-voice.md",
}


def run(root: pathlib.Path) -> tuple[bool, str]:
    dash_offenders: list[str] = []
    ascii_offenders: list[str] = []
    banned_offenders: list[str] = []
    unreadable: list[str] = []
    for p in walk_markdown(root):
        rel = p.relative_to(root).as_posix()
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            unreadable.append(f"{rel} ({e})")
            continue
        if DASH.search(text):
            dash_offenders.append(rel)
        # The dash message above is clearer, so the general scan skips the two dash characters.
        others = sorted({c for c in NON_ASCII.findall(text) if not DASH.match(c)})
        if others:
            shown = " ".join(f"U+{ord(c):04X}" for c in others[:3])
            ascii_offenders.append(f"{rel}: {shown}")
        if rel not in BANNED_EXEMPT:
            for w in banned_hits(text):
                banned_offenders.append(f"{rel}: {w!r}")
    problems = []
    if unreadable:
        problems.append("unreadable (fail closed): " + ", ".join(unreadable[:8]))
    if dash_offenders:
        problems.append("em/en-dash in: " + ", ".join(dash_offenders[:8]))
    if ascii_offenders:
        problems.append("non-ascii in: " + ", ".join(ascii_offenders[:8]))
    if banned_offenders:
        problems.append("banned register: " + ", ".join(banned_offenders[:8]))
    if problems:
        return False, "; ".join(problems)
    return True, "markdown is plain ASCII with no banned register"
