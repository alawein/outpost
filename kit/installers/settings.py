"""Merge kit settings into a Claude Code `.claude/settings.json` without disturbing anything else.

The merge adds secret-only deny rules and, optionally, a default output style. It never removes or
overwrites an unrelated key, it is idempotent (re-merging changes nothing), and it raises ValueError
on a malformed file so the caller can fail cleanly instead of crashing.
"""
from __future__ import annotations

import json

# Secret-only deny rules. The kit blocks reads of local secrets and nothing else; it does not ship
# eval, data, or governance rules. Kept deliberately small.
SECRET_DENY = (
    "Read(./.env)",
    "Read(./.env.*)",
    "Read(./secrets/**)",
)


def _as_object(value: object, name: str) -> dict:
    """Coerce a settings value to a dict copy. A missing or null value is an empty object; any
    other non-object is a malformed settings file and is rejected."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object, found {type(value).__name__}")
    return dict(value)


def _as_array(value: object, name: str) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a JSON array, found {type(value).__name__}")
    return list(value)


def merge_settings(existing: dict, output_style: str | None = None) -> dict:
    """Return existing settings with the secret deny rules merged in, plus the output style when
    given. Idempotent. Never removes or overwrites an unrelated key. Raises ValueError if a nested
    value has the wrong JSON type."""
    if not isinstance(existing, dict):
        raise ValueError("settings must be a JSON object")
    settings = dict(existing)

    perms = _as_object(settings.get("permissions"), "permissions")
    deny = _as_array(perms.get("deny"), "permissions.deny")
    for rule in SECRET_DENY:
        if rule not in deny:
            deny.append(rule)
    perms["deny"] = deny
    settings["permissions"] = perms

    if output_style:
        settings["outputStyle"] = output_style
    return settings


def merged_text(existing_text: str | None, output_style: str | None = None) -> str:
    """Parse existing settings text (or None for a new file), merge, and render to JSON text.
    Raises ValueError on malformed JSON or wrong-typed nested values."""
    if existing_text is None or existing_text.strip() == "":
        existing: dict = {}
    else:
        try:
            existing = json.loads(existing_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"settings is not valid JSON: {e}") from e
    return json.dumps(merge_settings(existing, output_style), indent=2) + "\n"


def unmerge_settings(existing: dict) -> dict:
    """Inverse of merge_settings: remove the kit's secret-deny rules and the `outputStyle: "terse"`
    the kit sets with --terse, leaving everything else (user deny rules, a non-terse outputStyle,
    unrelated keys) untouched. Drops a now-empty deny or permissions key so removal leaves no empty
    scaffolding. Raises ValueError on a wrong type. Used by `--remove`."""
    if not isinstance(existing, dict):
        raise ValueError("settings must be a JSON object")
    settings = dict(existing)
    had_kit_rule = False
    perms = settings.get("permissions")
    if isinstance(perms, dict):
        perms = dict(perms)
        deny = perms.get("deny")
        if isinstance(deny, list):
            kept = [r for r in deny if r not in SECRET_DENY]
            had_kit_rule = len(kept) != len(deny)
            if kept:
                perms["deny"] = kept
            else:
                perms.pop("deny", None)
        if perms:
            settings["permissions"] = perms
        else:
            settings.pop("permissions", None)
    # the kit only ever sets outputStyle to "terse" (via --terse), and only alongside its deny
    # rules, so drop that on un-install to avoid a dangling reference, but only when the kit deny
    # rules were actually here. That keeps remove from touching a settings file the kit never wrote
    # into (e.g. a user's own `{"outputStyle": "terse"}`).
    if had_kit_rule and settings.get("outputStyle") == "terse":
        settings.pop("outputStyle", None)
    return settings


def unmerged_text(existing_text: str) -> str | None:
    """Parse settings text and remove the kit's deny rules. Returns the original text unchanged when
    there was no kit rule to remove (so `--remove` never deletes a file the kit did not write into),
    None when removing the kit rules leaves nothing of the user's (delete the file), or the new JSON
    text otherwise. Raises ValueError on malformed JSON."""
    try:
        existing = json.loads(existing_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"settings is not valid JSON: {e}") from e
    result = unmerge_settings(existing)
    if result == existing:
        return existing_text  # nothing of the kit's was present: leave the file exactly as-is
    if not result:
        return None  # the kit rules were all that was here: the caller deletes the file
    return json.dumps(result, indent=2) + "\n"
