---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-07-26
---

# Outpost

Outpost is a small personal kit that installs prompts for coding agents. This file is the short guide for work in this repo.

## First checks

Run `python validate.py` and `python -m pytest -q` from the repo root. A change is done when both pass.

## Prompt workflow

- Start in `prompts/core/`.
- Use `plan-change` before a non-trivial edit, then implement, test, review, and prepare the PR.

## Repo rules

- The whole kit is standard library only. No third-party imports in the core, the installer, or
  the checks.
- Stage exact paths. Do not use blanket `git add`. Keep `.env` and secrets out of the tree.
- `docs/superpowers/` and `.superpowers/` hold local planning scratch (plans, specs, handoffs,
  session ledgers). Both are gitignored; nothing under them is committed.
- Commit one concern. Use an imperative subject under about 70 characters. Do not add emoji or a trailer line.
- Squash merge PRs.
- This is a solo repo (ADR-0018). An outside PR gets the owner's review before merge; the owner's own PRs merge on green CI (`python validate.py` and `pytest`) without a second approval. `.github/CODEOWNERS` names the owner and routes the review request.

## Documentation map

| Fact | Home |
|---|---|
| What the kit is and how to install it | `README.md` |
| Idea-to-PR workflow | `docs/workflow.md` |
| House voice | `docs/writing-standard.md` |
| Adding a prompt, adapter, or check | `docs/contributing.md` |
| Contribution cadence (commit, PR, tracker rhythm) | `docs/cadence.md` |
| Release flow | `docs/releasing.md` |
| Decisions | `docs/decisions/` |
| Deferred work | `docs/DEBT.md` |
| Roadmap and versions | `docs/ROADMAP.md` |
