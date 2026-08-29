---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-08-27
---

# Sources: watch a skill library you do not own

A source is a directory of skills the kit did not write. Point the installer at it and those skills install next to the core prompts, for every tool, recorded in the same manifest and checked by the same `--verify`. The first target is obra/superpowers; any tree in the Agent Skills layout works.

## What counts as a source

A source is a directory on disk holding `<source>/skills/<name>/SKILL.md`, or `<source>/<name>/SKILL.md` when there is no `skills/` directory. Each `SKILL.md` carries `name` and `description` frontmatter, and `name` must match its directory. A skill may carry supporting files (a guide, a `scripts/` directory) beside its `SKILL.md`.

You clone the source yourself; the kit never fetches. The source name is the directory's basename, lowercased, and it may hold only lowercase letters, digits, and hyphens. A directory name that does not fit is an error that names the rule, so rename the clone rather than guess.

## Install

```bash
git clone https://github.com/obra/superpowers /path/to/superpowers
python install.py --tool claude --project /path/to/your/repo --source /path/to/superpowers
python install.py --tool claude --project /path/to/your/repo --verify
```

`--source` repeats for more than one library. It works with `--dry-run`, `--verify`, `--prune`, and `--remove` the same way the core prompts do, and `--only` and `--exclude` apply to source skill names too, when `--source` is passed in the same run. Without `--source`, only the core prompts install. With `--verify`, `--prune`, and `--remove`, `--source` only replaces the recorded path of a source of the same name; a library never installed for that tool is ignored.

The manifest (`.outpost/manifest.json`) records each source once: its path, and per tool the skills that tool kept from it, since installs are per tool. A source installed for Codex alone is never demanded of Claude, and re-installing one tool never rewrites another tool's list. The installed files land under each tool's `files` map like any other kit-written path.

A later `--verify` or `--prune` with no `--source` reads the recorded path back and checks the installed copies against the source's current state. A recorded path that no longer exists prints `SOURCE MISSING <name> <path>` and exits 1. The recorded path is absolute, so on another machine pass `--source` again; a `--source` with the same name replaces the recorded path.

## What each tool gets

The skill's `name` is its directory name, so the installed path is predictable:

| Tool | Path | Content |
|---|---|---|
| claude | `.claude/skills/<name>/SKILL.md` plus every supporting file under the skill directory, at the same relative paths | verbatim |
| codex | `.agents/skills/<name>/SKILL.md` plus supporting files (Codex reads `.agents/skills/`) | verbatim |
| cursor | `.cursor/rules/<source>/<name>.md` | `SKILL.md` verbatim |
| copilot | `.github/prompts/<source>-<name>.prompt.md` | `SKILL.md` verbatim |
| windsurf | `.windsurf/workflows/<source>-<name>.md`, run as `/<source>-<name>` | `SKILL.md` verbatim; a skill over 12,000 characters is skipped, never truncated |
| gemini | `.gemini/commands/<source>/<name>.toml`, run as `/<source>:<name>` | rendered as a Gemini command by the same code that renders the core prompts |

Verbatim means the text as written; line endings are normalized to LF like the core prompts.

A path the manifest records as kit-written is overwritten on re-install, so a pulled source lands. A path that exists with no record is yours: it is left alone and reported as `skip (exists)`, so your own skill of the same name is never overwritten.

## Limitations

- No fetch. The kit reads a clone you made; keeping it current is a `git pull` you run.
- Supporting files install for Claude and Codex only. Cursor, Copilot, Windsurf, and Gemini get `SKILL.md` alone, so a skill whose body links to a sibling file keeps that link as text there.
- File modes are not copied. A supporting script installs as a plain file, so on Linux and macOS run it through its interpreter (`bash scripts/start-server.sh`) or `chmod +x` it yourself.
- Cross-references between skills (`superpowers:<name>` and the like) stay as text. The kit does not rewrite them per tool.
- Windsurf caps a workflow at 12,000 characters. A skill over the cap is skipped with a plan line `skip (over cap) <path>` and a note; it is never truncated.
- Gemini skips a skill it cannot render as a command: a body holding `'''`, `!{`, `@{`, or a control character is reported as `skip (unrenderable)` and not installed. Gemini CLI would run `!{` and `@{` as a shell command or file injection.
- Text only. A supporting file the kit cannot read as UTF-8 text is skipped with a plan line rather than copied.
- One name per skill where the path keys on it. For Claude, a source skill named like a core prompt stops the install with an error naming the path; for Claude and Codex, two sources sharing a skill name do the same. Nothing is written. The other tools namespace by source, so both copies install. Two clones with the same directory name are rejected the same way, so rename one clone; a clone named `outpost` collides with the core pack for every tool.
- `--verify` checks the skills recorded at install. A skill the source added since is not reported; re-install with `--source` to pick it up. A skill the source dropped reads `LEFTOVER`, and `--prune` removes it.
- One bad skill fails the whole source. A skill whose `name` does not match its directory or breaks the name rule, has no `description`, writes the description as a YAML block (`>` or `|`), or is not UTF-8 text stops discovery with an error naming the skill, and `--exclude` cannot skip it: fix the clone first. A description must be one line.
- Git metadata inside a skill (a nested clone's `.git` directory, or a submodule's `.git` file) is skipped with a plan line `skip (vcs)` and never installed, so a project never gains a repo config it did not write.

## Path safety

Every write and delete goes through the same containment check as the core prompts. A supporting file's relative path is checked the way a manifest key is: project-relative POSIX, no absolute path, no parent traversal, no backslash, no colon, no null byte. A symlink inside a source skill directory is skipped and reported, never followed.

## Verify a source install

`--verify` compares every installed copy, byte for byte, against the source's current state. Pull the clone and every installed copy of a skill that changed reads `DRIFTED` until you re-install with `--source`. That is the point, and this is how to see it:

```bash
git clone https://github.com/obra/superpowers /path/to/superpowers
python install.py --tool all --project /path/to/scratch --source /path/to/superpowers
python install.py --tool all --project /path/to/scratch --verify   # in sync
echo "local edit" >> /path/to/scratch/.claude/skills/writing-plans/SKILL.md
python install.py --tool all --project /path/to/scratch --verify   # DRIFTED, one copy
python install.py --tool all --project /path/to/scratch --source /path/to/superpowers
echo "upstream change" >> /path/to/superpowers/skills/writing-plans/SKILL.md
python install.py --tool all --project /path/to/scratch --verify   # DRIFTED, every tool's copy
git -C /path/to/superpowers checkout -- skills   # reset the clone
```

The second install restores the edited copy from the source. The last verify shows the case a source exists for: the library moved, and every installed copy is now behind it.

## Follow-ups

- A git URL as a source, with the kit cloning for you, is listed and not built. Today the source is a directory you cloned.
- The drift benchmark (`benchmarks/drift/`) does not cover sources yet. A source-ahead scenario is the listed next step.
