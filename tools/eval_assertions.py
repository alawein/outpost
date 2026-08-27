#!/usr/bin/env python3
"""The pure, stdlib-only assertion engine tools/run_evals.py checks a claude -p transcript
against. Every function here takes plain data (dicts, lists, strings) and returns plain data: no
subprocess call, no filesystem write, no network. This is what tests/test_eval_assertions.py
proves with fixed, fake input, so the eval harness's logic gets real pytest coverage without a
live LLM call.

Assertion types:
  file_not_modified {"path": str}        - the file's hash must be identical before and after,
                                            and must not have gone from present to absent.
  file_modified     {"path": str}        - the file must be present both before and after, with
                                            a different hash (the inverse of file_not_modified).
  file_created      {"path": str} or      - at least one path (exact or glob) must be present
                    {"path_glob": str}      after the run that was absent before.
  tool_not_used     {"names": [str, ...]} - none of the named tools may appear in tool_calls.
  text_contains     {"value": str}        - the transcript's final result text must contain
                                            value as a case-sensitive substring.
  text_contains_any {"values": [str, ...]}  - the transcript's final result text must contain at
                                              least one of values as a case-sensitive substring.
  workspace_unchanged {}                     - every file's hash in `after` must equal `before`
                                              with no paths added or removed (the whole tree, not
                                              one named path).
"""
from __future__ import annotations

import fnmatch


def _file_not_modified(assertion: dict, before: dict, after: dict) -> tuple[bool, str]:
    path = assertion.get("path")
    if path is None:
        return False, "file_not_modified assertion missing required 'path' field"
    if path not in before:
        return False, f"{path} did not exist before the run (misspelled path or bad fixture?)"
    before_hash = before[path]
    after_hash = after.get(path)
    if before_hash == after_hash:
        return True, f"{path} unchanged"
    if after_hash is None:
        return False, f"{path} was deleted"
    return False, f"{path} was modified (hash changed)"


def _file_modified(assertion: dict, before: dict, after: dict) -> tuple[bool, str]:
    path = assertion.get("path")
    if path is None:
        return False, "file_modified assertion missing required 'path' field"
    if path not in before:
        return False, f"{path} did not exist before the run (misspelled path or bad fixture?)"
    before_hash = before[path]
    after_hash = after.get(path)
    if after_hash is None:
        return False, f"{path} was deleted"
    if before_hash == after_hash:
        return False, f"{path} unchanged"
    return True, f"{path} modified (hash changed)"


def _matches(path: str, assertion: dict) -> bool:
    if "path" in assertion:
        return path == assertion["path"]
    return fnmatch.fnmatch(path, assertion["path_glob"])


def _file_created(assertion: dict, before: dict, after: dict) -> tuple[bool, str]:
    pattern = assertion.get("path") or assertion.get("path_glob")
    if pattern is None:
        return False, "file_created assertion missing required 'path' or 'path_glob' field"
    newly_present = [
        path for path, after_hash in after.items()
        if after_hash is not None
        and before.get(path) is None
        and _matches(path, assertion)
    ]
    if newly_present:
        return True, f"created: {', '.join(sorted(newly_present))}"
    return False, f"no new file matching {pattern!r} was created"


def _workspace_unchanged(assertion: dict, before: dict, after: dict) -> tuple[bool, str]:
    if before == after:
        return True, "workspace unchanged (no files created, deleted, or modified)"
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(p for p in before.keys() & after.keys() if before[p] != after[p])
    parts = []
    if added:
        parts.append(f"created: {', '.join(added)}")
    if removed:
        parts.append(f"deleted: {', '.join(removed)}")
    if changed:
        parts.append(f"modified: {', '.join(changed)}")
    return False, "; ".join(parts)


def _tool_not_used(assertion: dict, transcript: dict) -> tuple[bool, str]:
    names = assertion.get("names")
    if not names or isinstance(names, str):
        return False, ("tool_not_used assertion missing required non-empty 'names' list "
                        "(got a bare string?)")
    forbidden = set(names)
    used = [call["name"] for call in transcript.get("tool_calls", []) if call["name"] in forbidden]
    if used:
        return False, f"forbidden tool(s) used: {', '.join(used)}"
    return True, "none of the forbidden tools were used"


def _text_contains(assertion: dict, transcript: dict) -> tuple[bool, str]:
    value = assertion.get("value")
    if value is None:
        return False, "text_contains assertion missing required 'value' field"
    text = transcript.get("result", "")
    if value in text:
        return True, f"{value!r} found in result text"
    return False, f"{value!r} not found in result text"


def _text_contains_any(assertion: dict, transcript: dict) -> tuple[bool, str]:
    values = assertion.get("values")
    if not values or isinstance(values, str):
        return False, ("text_contains_any assertion missing required non-empty 'values' list "
                        "(got a bare string?)")
    text = transcript.get("result", "")
    matched = [v for v in values if v in text]
    if matched:
        return True, f"found: {', '.join(repr(v) for v in matched)}"
    return False, f"none of {values!r} found in result text"


_HANDLERS = {
    "file_not_modified": lambda a, t, b, af: _file_not_modified(a, b, af),
    "file_modified": lambda a, t, b, af: _file_modified(a, b, af),
    "file_created": lambda a, t, b, af: _file_created(a, b, af),
    "tool_not_used": lambda a, t, b, af: _tool_not_used(a, t),
    "text_contains": lambda a, t, b, af: _text_contains(a, t),
    "text_contains_any": lambda a, t, b, af: _text_contains_any(a, t),
    "workspace_unchanged": lambda a, t, b, af: _workspace_unchanged(a, b, af),
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
