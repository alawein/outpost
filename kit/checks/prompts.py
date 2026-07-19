"""Every prompt has the right shape: a matching name, a description long enough to plausibly serve
as a trigger, YAML-parseable frontmatter, a substantive body, and all five contract sections (when
to use, required inputs, steps, output format, stop conditions). This proves form, not quality:
the length and heading checks catch an empty or truncated prompt, not a weak, vague, or misleading
one.
"""
from __future__ import annotations

import pathlib
import re

from . import banned_hits, frontmatter_field, split_frontmatter

REQUIRED_SECTIONS = ("when to use", "required inputs", "steps", "output format", "stop conditions")
MIN_BODY_WORDS = 60

# Characters YAML reserves at the start of a plain scalar; a value starting with one parses as
# flow syntax, an anchor, a tag, or a comment instead of the intended text.
_YAML_INDICATORS = tuple("[]{}>|*&!%#@`,")


def frontmatter_yaml_errors(fm: str, stem: str) -> list[str]:
    """Reject frontmatter a real YAML parser would not read as flat `key: value` string metadata.
    Hosts parse the frontmatter as YAML, and an invalid document loses every field at once (the
    audit's converge case: one unquoted colon and Claude dropped the whole frontmatter). The kit
    is standard library only, so this validates the failure classes instead of importing a YAML
    parser: an unquoted colon inside or at the end of a plain value (YAML reads it as a nested
    mapping), an unterminated quoted value, and a plain value opening with a YAML indicator."""
    errors: list[str] = []
    for line in fm.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s+(.*\S)\s*$", line)
        if m is None:
            errors.append(f"{stem}: frontmatter line is not a flat 'key: value' pair: {line!r}")
            continue
        key, value = m.groups()
        if value[0] in "\"'":
            quote = value[0]
            if len(value) < 2 or not value.endswith(quote):
                errors.append(f"{stem}: frontmatter {key} has an unterminated quote")
            continue
        if value.startswith(_YAML_INDICATORS):
            errors.append(f"{stem}: frontmatter {key} starts with the YAML indicator "
                          f"{value[0]!r}; quote the value")
            continue
        if ": " in value or value.endswith(":"):
            errors.append(f"{stem}: frontmatter {key} has an unquoted colon; YAML reads it as a "
                          f"nested mapping and hosts drop the whole frontmatter")
        if " #" in value:
            errors.append(f"{stem}: frontmatter {key} has an unquoted ' #'; YAML truncates the "
                          f"value at the comment")
    return errors


def lint_prompt(text: str, stem: str) -> list[str]:
    errors: list[str] = []
    fm, body = split_frontmatter(text)
    errors += frontmatter_yaml_errors(fm, stem)
    name = frontmatter_field(fm, "name")
    desc = frontmatter_field(fm, "description")
    if not name:
        errors.append(f"{stem}: missing frontmatter name")
    elif name != stem:
        errors.append(f"{stem}: frontmatter name {name!r} does not match the file")
    if not desc:
        errors.append(f"{stem}: missing frontmatter description")
    elif len(desc) < 40:
        errors.append(f"{stem}: description too short to be a real trigger ({len(desc)} chars)")
    words = len(body.split())
    if words < MIN_BODY_WORDS:
        errors.append(f"{stem}: body too thin ({words} words); a prompt is not a stub")
    if not any(line.lstrip().startswith("# ") for line in body.splitlines()):
        errors.append(f"{stem}: no H1 heading")
    headers = [line.lower() for line in body.splitlines() if line.lstrip().startswith("#")]
    for section in REQUIRED_SECTIONS:
        if not any(section in h for h in headers):
            errors.append(f"{stem}: missing a '{section}' section heading")
    errors += [f"{stem}: banned register word {w!r}" for w in banned_hits(text)]
    return errors


def run(root: pathlib.Path) -> tuple[bool, str]:
    core = root / "prompts" / "core"
    files = sorted(core.glob("*.md"))
    if not files:
        return False, "no prompts found under prompts/core/"
    errors: list[str] = []
    for p in files:
        errors += lint_prompt(p.read_text(encoding="utf-8"), p.stem)
    if errors:
        return False, "; ".join(errors[:10])
    return True, f"{len(files)} core prompts well-formed with all contract sections"
