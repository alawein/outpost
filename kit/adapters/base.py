"""Shared adapter machinery: the Action type, the prompt loader, and the terse output style.

An Action is a planned change to the target project. It carries its final content so a dry-run can
show exactly what an install would do. Three modes keep the install safe:

- write:  kit-owned path. Overwrite with the rendered content. Idempotent (same content each run).
- create: user-owned path. Write only if absent. If present, skip and leave the user's file alone.
- merge:  a shared config file. The content is already the merged result; write it.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass


# The legal modes, owned here so the type validates its own invariant. The adapters check imports
# this rather than redefining the set, so the two cannot drift.
MODES = ("write", "create", "merge")


@dataclass(frozen=True)
class Action:
    path: str        # relative to the project root, POSIX style
    content: str     # the final content to write
    mode: str        # one of MODES: "write" | "create" | "merge"
    note: str = ""   # short human note for the dry-run plan

    def __post_init__(self) -> None:
        # validate at construction, so a bad mode fails loudly instead of falling through status()
        # to the overwrite branch and clobbering a file. Covers every code path, including terse.
        if self.mode not in MODES:
            raise ValueError(f"invalid Action mode {self.mode!r}; expected one of {MODES}")

    def status(self, project_root: pathlib.Path) -> str:
        """What this action would do against the current disk state."""
        target = project_root / self.path
        if self.mode == "create" and target.exists():
            return "skip (exists)"
        if target.exists():
            try:
                on_disk = target.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                return "overwrite"
            if on_disk == self.content:
                return "unchanged"
            # A merge action's content is canonical JSON. A user-formatted settings file
            # (different indent, key order, or trailing newline) is the same install, so
            # compare parsed JSON, not bytes. This keeps re-install a no-op and stops a
            # false --verify drift on a correctly-installed file.
            if self.mode == "merge":
                try:
                    if json.loads(on_disk) == json.loads(self.content):
                        return "unchanged"
                except (json.JSONDecodeError, ValueError):
                    pass
            return "update"
        return "create"


@dataclass(frozen=True)
class Skip:
    """A source file the plan leaves out on purpose, so a dry-run and an install can say so.
    `path` is the path the file would have taken (or the source-relative path when a whole skill
    directory was skipped), `kind` the short cause ("over cap"), `reason` the fuller note."""
    path: str
    kind: str
    reason: str

    @property
    def label(self) -> str:
        """The status a dry-run plan line shows, shaped like Action.status() values."""
        return f"skip ({self.kind})"


_SKIP_REASONS = {
    "symlink": "a symlink inside the source; never followed",
    "bad path": "supporting file path is not a plain relative path",
}


def source_actions(tool: str, source, select=None, skipped=None) -> list[Action]:
    """The Actions that install one source's skills for `tool`, appended after the core plan.
    Claude and Codex take the skill directory whole (SKILL.md plus every UTF-8 text supporting
    file at its relative path); Cursor, Copilot, and Windsurf take SKILL.md verbatim under a
    source-namespaced name; Gemini renders it as a command with `to_command_toml`. Every path is
    `write` mode: the installer's own ownership records keep a user's pre-existing file of the same
    name untouched. Whatever is left out (an over-cap Windsurf skill, a non-text or symlinked
    supporting file, a skill Gemini cannot render) is appended to `skipped` as a Skip, never
    installed truncated or altered. `select` (a set of names, or None for all) filters skills."""
    from .gemini import to_command_toml
    from .windsurf import WINDSURF_LIMIT
    skips = skipped if skipped is not None else []
    actions: list[Action] = []
    for rel, kind in source.skipped:
        skips.append(Skip(f"{source.name}/{rel}", kind, _SKIP_REASONS[kind]))
    for skill in source.skills:
        if select is not None and skill.name not in select:
            continue
        note = f"skill {skill.name} from source {source.name}"
        if tool in ("claude", "codex"):
            base = (".claude/skills" if tool == "claude" else ".agents/skills") + f"/{skill.name}"
            actions.append(Action(path=f"{base}/SKILL.md", content=skill.body, mode="write",
                                  note=note + " (verbatim)"))
            for rel, data in sorted(skill.files.items()):
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    skips.append(Skip(f"{base}/{rel}", "not text",
                                      "supporting file is not UTF-8 text; not installed"))
                    continue
                # the same newline translation read_text gives SKILL.md, so a clone checked out
                # with CRLF installs with the kit's LF policy and verifies in sync
                text = text.replace("\r\n", "\n").replace("\r", "\n")
                actions.append(Action(path=f"{base}/{rel}", content=text, mode="write",
                                      note=f"supporting file of {note}"))
            for rel, kind in skill.skipped:
                skips.append(Skip(f"{base}/{rel}", kind, _SKIP_REASONS[kind]))
        elif tool == "cursor":
            actions.append(Action(path=f".cursor/rules/{source.name}/{skill.name}.md",
                                  content=skill.body, mode="write", note=note + " (verbatim)"))
        elif tool == "copilot":
            actions.append(Action(path=f".github/prompts/{source.name}-{skill.name}.prompt.md",
                                  content=skill.body, mode="write", note=note + " (verbatim)"))
        elif tool == "windsurf":
            path = f".windsurf/workflows/{source.name}-{skill.name}.md"
            if skill.chars > WINDSURF_LIMIT:
                skips.append(Skip(path, "over cap",
                                  f"{skill.chars} characters, over Windsurf's {WINDSURF_LIMIT}-"
                                  "character workflow cap; not installed, never truncated"))
                continue
            actions.append(Action(path=path, content=skill.body, mode="write",
                                  note=note + f", invoked as /{source.name}-{skill.name}"))
        elif tool == "gemini":
            path = f".gemini/commands/{source.name}/{skill.name}.toml"
            try:
                content = to_command_toml(skill.name, skill.body)
            except ValueError as e:
                skips.append(Skip(path, "unrenderable", f"{e}; not installed"))
                continue
            actions.append(Action(path=path, content=content, mode="write",
                                  note=note + f", invoked as /{source.name}:{skill.name}"))
        else:
            raise ValueError(f"unknown tool {tool!r}")
    return actions


def _host_excluded(kit_root: pathlib.Path, tool: str) -> set[str]:
    """Prompt names whose catalog entry limits them to other hosts (`converge`
    ships to Claude only). One home for the rule: the catalog `hosts` field, honored here so
    every adapter and the plugin builder filter the same way. A kit tree without a catalog
    (a unit-test fixture) excludes nothing."""
    cat_path = kit_root / "kit" / "catalog" / "catalog.json"
    if not cat_path.is_file():
        return set()
    from ..catalog import load_catalog
    cat = load_catalog(cat_path)
    allowed = {p["name"] for p in cat.prompts_for(tool)}
    return {p["name"] for p in cat.prompts} - allowed


def load_prompts(kit_root: pathlib.Path, tool: str, select=None) -> list[tuple[str, str]]:
    """Load the core prompts, with a tool overlay taking precedence by name. Returns
    (name, content) pairs sorted by name. The overlay lets a tool override one prompt without
    forking the whole pack; it is empty by default. `select` (a set of names, or None for the
    full pack) filters the result, so a tailored install writes only the chosen prompts. A
    prompt the catalog limits to other hosts is dropped for this tool regardless of `select`."""
    core_dir = kit_root / "prompts" / "core"
    overlay_dir = kit_root / "prompts" / tool
    prompts: dict[str, str] = {}
    for p in sorted(core_dir.glob("*.md")):
        prompts[p.stem] = p.read_text(encoding="utf-8")
    if overlay_dir.is_dir():
        for p in sorted(overlay_dir.glob("*.md")):
            if p.stem == "README":
                continue
            prompts[p.stem] = p.read_text(encoding="utf-8")
    for name in _host_excluded(kit_root, tool):
        prompts.pop(name, None)
    if select is not None:
        prompts = {k: v for k, v in prompts.items() if k in select}
    return sorted(prompts.items())


def read_template(kit_root: pathlib.Path, filename: str) -> str:
    return (kit_root / "templates" / filename).read_text(encoding="utf-8")


TERSE_OUTPUT_STYLE = """\
---
name: terse
description: Lead with the answer, cut preamble, format natively, stop when done. Toggle with /output-style.
---

# Output Style: terse

Sharp and to the point. The reader is busy and technical. Say the thing, format it well, stop.

## Voice

- Lead with the answer. No preamble, no restating the question.
- Match length to the question. One sentence when one sentence answers it.
- Plain, declarative sentences. One idea each. American spelling.
- No filler openers or closers that add nothing.
- Honest over agreeable. If something is wrong, say so and why.
- No em-dashes or en-dashes. Use a comma, a period, or parentheses.

## Format natively

- Use the terminal's markdown: tables for things compared on shared axes, fenced blocks for code,
  backticks for files and flags.
- Bullets and headers earn their place or they go. Default to prose for one or two points.
- Show, do not narrate: a three-line diff beats a paragraph describing it.

## What to cut

- Recaps of what you just did, unless asked.
- Lists of options you will not take.
- Hedging on settled facts.

This style governs tone and shape only. It does not change what tools you use or what work you do.
"""
