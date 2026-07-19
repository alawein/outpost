#!/usr/bin/env python3
"""PostToolUse nudge: when a Read pulls a very large file with no offset or limit, print a one-line
reminder to read a targeted range or offload to a subagent. Advisory only: it always exits 0 and
never blocks. Pure stdlib, so it runs in any repo that enables the plugin.

The threshold is a byte size (OUTPOST_NUDGE_BYTES, default 100000). A read that already passes offset
or limit is the good path and stays silent; a small file stays silent. This teaches the
context-hygiene habit described in docs/token-budget.md without getting in the
way. If it proves noisy in real use, drop it; it is deliberately the weakest guard in the kit.
"""
from __future__ import annotations

import json
import os
import sys

_DEFAULT_THRESHOLD = 100000


def _threshold() -> int:
    """The nudge byte threshold. Fails open: a malformed or negative value falls back to the
    default rather than raising at import or nudging on nearly every read."""
    raw = os.environ.get("OUTPOST_NUDGE_BYTES") or ""
    try:
        value = int(raw)
    except ValueError:
        return _DEFAULT_THRESHOLD
    return value if value > 0 else _DEFAULT_THRESHOLD


THRESHOLD = _threshold()


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return 0
    if "offset" in tool_input or "limit" in tool_input:
        return 0  # a targeted read is already the good path
    path = tool_input.get("file_path")
    if not isinstance(path, str) or not path:
        return 0
    try:
        size = os.path.getsize(path)
    except OSError:
        return 0
    if size > THRESHOLD:
        print(
            f"nudge: read {size // 1000}KB of {path} with no offset/limit. "
            f"Prefer a targeted range or a subagent (see docs/token-budget.md).",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
