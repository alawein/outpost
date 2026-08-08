#!/usr/bin/env python3
"""The pure, stdlib-only assertion engine tools/run_evals.py checks a claude -p transcript
against. Every function here takes plain data (dicts, lists, strings) and returns plain data: no
subprocess call, no filesystem write, no network. This is what tests/test_eval_assertions.py
proves with fixed, fake input, so the eval harness's logic gets real pytest coverage without a
live LLM call.

Assertion types:
  file_not_modified {"path": str}        - the file's hash must be identical before and after,
                                            and must not have gone from present to absent.
  file_created      {"path": str} or      - at least one path (exact or glob) must be present
                    {"path_glob": str}      after the run that was absent before.
  tool_not_used     {"names": [str, ...]} - none of the named tools may appear in tool_calls.
  text_contains     {"value": str}        - the transcript's final result text must contain
                                            value as a case-sensitive substring.
"""
from __future__ import annotations

import fnmatch


def _file_not_modified(assertion: dict, before: dict, after: dict) -> tuple[bool, str]:
    path = assertion["path"]
    before_hash = before.get(path)
    after_hash = after.get(path)
    if before_hash == after_hash:
        return True, f"{path} unchanged"
    if after_hash is None:
        return False, f"{path} was deleted"
    return False, f"{path} was modified (hash changed)"


def _matches(path: str, assertion: dict) -> bool:
    if "path" in assertion:
        return path == assertion["path"]
    return fnmatch.fnmatch(path, assertion["path_glob"])


def _file_created(assertion: dict, before: dict, after: dict) -> tuple[bool, str]:
    pattern = assertion.get("path") or assertion.get("path_glob")
    newly_present = [
        path for path, after_hash in after.items()
        if after_hash is not None
        and before.get(path) is None
        and _matches(path, assertion)
    ]
    if newly_present:
        return True, f"created: {', '.join(sorted(newly_present))}"
    return False, f"no new file matching {pattern!r} was created"


def _tool_not_used(assertion: dict, transcript: dict) -> tuple[bool, str]:
    forbidden = set(assertion["names"])
    used = [call["name"] for call in transcript.get("tool_calls", []) if call["name"] in forbidden]
    if used:
        return False, f"forbidden tool(s) used: {', '.join(used)}"
    return True, "none of the forbidden tools were used"


def _text_contains(assertion: dict, transcript: dict) -> tuple[bool, str]:
    value = assertion["value"]
    text = transcript.get("result", "")
    if value in text:
        return True, f"{value!r} found in result text"
    return False, f"{value!r} not found in result text"


_HANDLERS = {
    "file_not_modified": lambda a, t, b, af: _file_not_modified(a, b, af),
    "file_created": lambda a, t, b, af: _file_created(a, b, af),
    "tool_not_used": lambda a, t, b, af: _tool_not_used(a, t),
    "text_contains": lambda a, t, b, af: _text_contains(a, t),
}


def evaluate_assertion(
    assertion: dict, transcript: dict, before_hashes: dict, after_hashes: dict
) -> tuple[bool, str]:
    """Evaluate one assertion. Returns (passed, reason). An unknown assertion type fails loudly
    (never silently passes), naming the unrecognized type in the reason."""
    handler = _HANDLERS.get(assertion.get("type"))
    if handler is None:
        return False, f"unknown assertion type: {assertion.get('type')!r}"
    return handler(assertion, transcript, before_hashes, after_hashes)


def evaluate_all(
    assertions: list[dict], transcript: dict, before_hashes: dict, after_hashes: dict
) -> list[tuple[dict, bool, str]]:
    """Evaluate every assertion, in order, never short-circuiting on the first failure (so a
    caller sees every problem in one run, not just the first)."""
    return [
        (assertion, *evaluate_assertion(assertion, transcript, before_hashes, after_hashes))
        for assertion in assertions
    ]
