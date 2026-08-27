# Guide templates

One guide per supported tool, not one generic file under six names. Each tool reads a fixed
filename from a fixed place, with its own prompt path and loading model. That is why each guide has
its own head. The rest, the working agreement and the prompt list, is one shared core.

| Tool | Installed as | Prompts |
|---|---|---|
| Claude | `CLAUDE.md` | `.claude/skills/` |
| Codex | `AGENTS.md` | `.agents/prompts/` |
| Cursor | `.cursor/rules/outpost.mdc` | `.cursor/rules/outpost/` |
| GitHub Copilot | `.github/copilot-instructions.md` | `.github/prompts/` |
| Windsurf | `.windsurf/rules/outpost.md` | `.windsurf/workflows/` |
| Gemini CLI | `GEMINI.md` | `.gemini/commands/outpost/` |

## Editing

`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `cursor-rules.md`, `copilot-instructions.md`, and
`windsurf-rules.md` are generated. Do not edit them directly. Edit the sources under `_src/`:

- `_src/core.md` is the shared core, identical in every guide.
- `_src/head/<tool>.md` is the per-tool head.

Run `python tools/build.py templates`, then `python validate.py`. The `templates_sync` check fails if a committed guide no longer matches the build.
