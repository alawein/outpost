"""Every label an issue form or a path-based labeler config names must be a real one: in the
label registry, or one of the retained GitHub defaults the registry does not migrate away. A
typo or a stale label name here would silently produce an unlabeled issue or a failed labeler
run. Scoped to `.github/ISSUE_TEMPLATE/*.yml` and `.github/labeler.yml`, the two places this repo
names labels in config; a workflow step that sets a label via a shell command is out of scope,
the same way doc_truth does not parse arbitrary prose.
"""
from __future__ import annotations

import pathlib
import re

from ..labels import load_labels

_LABELS_KEY = re.compile(r"^(?P<indent>[ \t]*)labels:[ \t]*(?P<inline>.*)$")
_LIST_ITEM = re.compile(r"^(?P<indent>[ \t]*)-[ \t]*(?P<value>.+?)[ \t]*$")


def _strip_comment(line: str) -> str:
    """Drop a trailing ` #comment`, honoring quotes so a `#` inside a quoted label name (not
    that one would ever contain one, but a stray one should not corrupt parsing) is not mistaken
    for one."""
    in_quote = None
    for i, ch in enumerate(line):
        if in_quote:
            if ch == in_quote:
                in_quote = None
        elif ch in "\"'":
            in_quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
    return line


def _unquote(token: str) -> str:
    token = token.strip()
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    return token


def _parse_inline_list(inline: str) -> list[str]:
    body = inline.strip()
    if body.startswith("[") and body.endswith("]"):
        body = body[1:-1]
    if not body:
        return []
    return [_unquote(item) for item in body.split(",") if item.strip()]


def extract_label_refs(text: str) -> list[str]:
    """Every label name a `labels:` key names in the text, flow-list (`labels: [a, b]`) or
    block-list (`labels:\\n  - a\\n  - b`, indented under the key or flush with it) style. A
    trailing `# comment` is dropped; a blank or comment-only line inside a block list does not
    end it."""
    lines = [_strip_comment(line) for line in text.splitlines()]
    refs: list[str] = []
    i = 0
    while i < len(lines):
        m = _LABELS_KEY.match(lines[i])
        if not m:
            i += 1
            continue
        inline = m.group("inline")
        if inline.strip():
            refs += _parse_inline_list(inline)
            i += 1
            continue
        base_indent = len(m.group("indent"))
        i += 1
        while i < len(lines):
            if not lines[i].strip():
                i += 1
                continue
            item = _LIST_ITEM.match(lines[i])
            if not item or len(item.group("indent")) < base_indent:
                break
            refs.append(_unquote(item.group("value")))
            i += 1
    return refs


def run(root: pathlib.Path) -> tuple[bool, str]:
    try:
        registry = load_labels(root / "kit" / "labels" / "registry.json")
    except ValueError as e:
        return False, str(e)

    files: list[pathlib.Path] = []
    issue_forms_dir = root / ".github" / "ISSUE_TEMPLATE"
    if issue_forms_dir.is_dir():
        files += sorted(issue_forms_dir.glob("*.yml"))
    labeler = root / ".github" / "labeler.yml"
    if labeler.is_file():
        files.append(labeler)

    unknown: list[str] = []
    for p in files:
        for name in extract_label_refs(p.read_text(encoding="utf-8")):
            if name not in registry.known_names:
                unknown.append(f"{p.relative_to(root).as_posix()}: unregistered label {name!r}")

    if unknown:
        return False, "; ".join(unknown[:10])
    if not files:
        return True, "no issue forms or labeler config yet; nothing to check"
    return True, f"{len(files)} file(s) name only registered labels"
