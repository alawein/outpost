"""Discover a skill library the kit does not own (a source).

A source is a directory the user cloned themselves, holding skills in the Agent Skills layout:
`<source>/skills/<name>/SKILL.md`, or `<source>/<name>/SKILL.md` when there is no `skills/`
directory. The kit never fetches. The source name is the directory's basename, lowercased and
restricted to `[a-z0-9-]`, so it can namespace a Cursor rule directory, a Copilot prompt file, a
Windsurf workflow, or a Gemini command without escaping the tool's own tree.

Discovery reads every skill once and validates it: the frontmatter `name` matches the directory
and the same character rule, and a `description` is present on one line. A violation raises
ValueError naming the skill, so a bad library fails before any write. Supporting files under a
skill directory are read as bytes, keyed by their skill-relative POSIX path; that path passes the
same check as a manifest file key (see `is_project_relative`), and a link anywhere inside a source
(a symlink, or an NTFS junction, which Path.is_symlink() does not report) is skipped and reported,
never followed. A link is detected by resolving the path and comparing it with its own logical
place, so a loop and a link back inside the source are caught the same way as one pointing out.
"""
from __future__ import annotations

import os
import pathlib
import re
import stat
from dataclasses import dataclass

from .checks import frontmatter_field, split_frontmatter
from .installers.manifest import is_project_relative

NAME_RE = re.compile(r"^[a-z0-9-]+$")
NAME_RULE = "lowercase letters, digits, and hyphens only ([a-z0-9-])"


@dataclass(frozen=True)
class Skill:
    name: str
    body: str                    # the SKILL.md text, installed verbatim
    description: str
    files: dict                  # supporting files: skill-relative POSIX path -> bytes
    chars: int                   # len(body), judged against the Windsurf cap
    skipped: tuple = ()          # (skill-relative path, reason): "symlink" | "bad path" | "vcs"


@dataclass(frozen=True)
class Source:
    name: str
    path: pathlib.Path           # the resolved source directory
    skills: list
    skipped: tuple = ()          # (source-relative path, reason) pairs for a skipped skill dir


_BLOCK_SCALARS = (">", "|", ">-", "|-", ">+", "|+")

# The NTFS reparse tags that redirect a path: a symlink and a junction (mount point). The stat
# module names them on Windows only, so the values are pinned for the other platforms, where a
# faked stat result in a test is the only way they appear.
_LINK_TAGS = (getattr(stat, "IO_REPARSE_TAG_SYMLINK", 0xA000000C),
              getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003))


def source_name(source_dir: pathlib.Path) -> str:
    """The source name a directory gets: its basename, lowercased. Raises ValueError naming the
    rule when the result does not fit `[a-z0-9-]` (fullmatch, so a trailing newline fails too)."""
    name = source_dir.name.lower()
    if not NAME_RE.fullmatch(name):
        raise ValueError(f"source directory name {source_dir.name!r} is not a source name "
                         f"({NAME_RULE}); rename the clone")
    return name


def is_link(path: pathlib.Path) -> bool:
    """True when `path` is a link or sits under one: a symlink (Path.is_symlink), an NTFS
    reparse point whose tag is a symlink or a junction (a junction is not a symlink to
    Path.is_symlink() on Python 3.12+, and os.walk descends into it; the tag comes from
    os.lstat), or a path that resolves anywhere but its own logical place. The tag, not the
    reparse attribute, decides: a cloud placeholder (a OneDrive or Dropbox online-only file) is
    a reparse point too and must read as a plain file. `path` must be built from an already
    resolved root, so that last comparison is exact. A loop, a broken link, or an unresolvable
    path counts as a link: skipped, never followed. Works on the 3.9 floor and on every OS the
    same way."""
    try:
        if path.is_symlink():
            return True
        if getattr(os.lstat(path), "st_reparse_tag", 0) in _LINK_TAGS:
            return True
        return path.resolve() != path
    except (OSError, RuntimeError):
        return True


def _read_skill(skill_dir: pathlib.Path, skill_md: pathlib.Path) -> Skill:
    try:
        body = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"skill {skill_dir.name}: SKILL.md is not UTF-8 text") from e
    fm, _ = split_frontmatter(body)
    name = frontmatter_field(fm, "name")
    if name is None:
        raise ValueError(f"skill {skill_dir.name}: SKILL.md frontmatter has no name")
    if name != skill_dir.name:
        raise ValueError(f"skill {skill_dir.name}: frontmatter name {name!r} does not match its "
                         "directory")
    if not NAME_RE.fullmatch(name):
        raise ValueError(f"skill {skill_dir.name}: name must be {NAME_RULE}")
    description = frontmatter_field(fm, "description")
    if not description:
        raise ValueError(f"skill {skill_dir.name}: SKILL.md frontmatter has no description")
    if description in _BLOCK_SCALARS:
        # frontmatter_field reads one line, so a YAML block scalar would install as ">" or "|"
        raise ValueError(f"skill {skill_dir.name}: multi-line description is not supported; "
                         "use one line")
    files: dict = {}
    skipped: list = []
    skill_root = skill_dir.resolve()
    for dirpath, dirnames, filenames in os.walk(skill_root, followlinks=False):
        here = pathlib.Path(dirpath)
        # git metadata inside a skill (a nested clone, or a submodule's .git file) would install
        # as supporting files and hand the project a repo config it then honors (hooksPath,
        # aliases); drop it here, reported once, never read
        if ".git" in dirnames:
            skipped.append(((here / ".git").relative_to(skill_root).as_posix(), "vcs"))
            dirnames.remove(".git")
        # os.walk lists a linked directory and, for a junction, would descend into it; drop it
        # here so it is reported once and its contents never read
        for sub in sorted(dirnames):
            if is_link(here / sub):
                skipped.append(((here / sub).relative_to(skill_root).as_posix(), "symlink"))
                dirnames.remove(sub)
        dirnames.sort()
        for filename in sorted(filenames):
            p = here / filename
            rel = p.relative_to(skill_root).as_posix()
            if rel == "SKILL.md":
                continue
            if filename == ".git":
                skipped.append((rel, "vcs"))
                continue
            if is_link(p):
                skipped.append((rel, "symlink"))
                continue
            if not is_project_relative(rel):
                skipped.append((rel, "bad path"))
                continue
            files[rel] = p.read_bytes()
    return Skill(name=name, body=body, description=description, files=files, chars=len(body),
                 skipped=tuple(skipped))


def discover(source_dir) -> Source:
    """Read a source directory into a Source. Raises ValueError when the directory is missing,
    its name breaks the rule, it holds no skills, or a skill fails validation."""
    given = pathlib.Path(source_dir)
    if not given.is_dir():
        raise ValueError(f"source {given} is not a directory")
    root = given.resolve()
    name = source_name(root)
    skills_root = root
    if (root / "skills").is_dir():
        if is_link(root / "skills"):
            raise ValueError(f"source {root}: skills/ is a symlink or junction; never followed")
        skills_root = root / "skills"
    skills: list = []
    skipped: list = []
    for child in sorted(skills_root.iterdir()):
        if not child.is_dir():
            continue  # a file at the top level is not a skill
        rel = child.relative_to(root).as_posix()
        if is_link(child):
            skipped.append((rel, "symlink"))
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.is_symlink() and not skill_md.exists():
            continue  # a directory without a SKILL.md (docs/, scripts/) is not a skill
        if is_link(skill_md):
            skipped.append((rel, "symlink"))  # a linked, broken, or junctioned SKILL.md
            continue
        if not skill_md.is_file():
            continue
        skills.append(_read_skill(child, skill_md))
    if not skills:
        raise ValueError(f"source {root} holds no skills (expected <source>/skills/<name>/SKILL.md "
                         "or <source>/<name>/SKILL.md)")
    return Source(name=name, path=root, skills=skills, skipped=tuple(skipped))
