---
type: canonical
last_updated: 2026-07-26
---

# Repository topology

**Archetype:** `python-platform-cli` (fleet `type=tooling`, surface `cli`)

Outpost is a zero-dependency Python kit. `install.py` writes prompts into a
consumer project; `validate.py` gates the kit source tree. The Claude plugin
under `plugins/outpost/` is generated from the catalog and committed.

## On-disk layout

```text
outpost/
  install.py                 # install prompts into a target project
  validate.py                # kit source-tree checks
  kit/
    catalog/                 # prompt catalog and version SSOT
    adapters/                # Claude, Codex, Cursor, Copilot writers
    installers/              # install / verify / prune / remove
    checks/                  # structure, docs truth, catalog gates
    docs_build.py            # generated README / workflow spans
  prompts/                   # core + per-tool prompt overlays
  plugins/outpost/           # Claude Code plugin (skills, commands, hooks)
  templates/                 # consumer guides and overlays
  docs/                      # onboarding, workflow, ADRs, releasing
  tests/                     # pytest
  tools/                     # build helpers (plugin / docs / templates)
```

## Role boundaries

- `kit/catalog/` owns prompt identity and version; do not invent parallel lists in docs.
- `kit/adapters/` owns per-tool install paths; consumer overlays stay under `prompts/<tool>/`.
- `plugins/outpost/` is generated; regenerate with `python tools/build.py plugin` instead of hand-editing skills.
- `validate.py` / `kit/checks/` prove kit truth; they do not validate a consumer install (use `--verify`).
- `docs/decisions/` is append-only ADR history.

## Related

- [README.md](../../README.md): install, commands, supported tools.
- [docs/onboarding.md](../onboarding.md): full install path.
- [docs/workflow.md](../workflow.md): ordered prompt path and Claude shortcuts.
- [docs/releasing.md](../releasing.md): version bump and release checklist.
- [docs/decisions/0001-repo-architecture.md](../decisions/0001-repo-architecture.md): architecture ADR.
