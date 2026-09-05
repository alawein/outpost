---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-09-05
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
- Commit one concern. New commits in this repository use `type(scope): imperative subject`,
  with the scope optional and the full subject under about 70 characters. Types are `feat`,
  `fix`, `docs`, `refactor`, `chore`, `ci`, and `test`. Do not add emoji or a trailer line.
  This approved repository exception applies going forward; leave existing commit subjects
  unchanged. Installing an Outpost prompt does not impose this exception on another repo.
- Squash merge PRs.
- This is a solo repo (see docs/decisions/0001-solo-review-model.md). An outside PR gets the owner's review before merge; the owner's own PRs merge on green CI (`python validate.py` and `pytest`) without a second approval. `.github/CODEOWNERS` names the owner and routes the review request.
- Write a decision record only when at least two hold: the choice crosses a boundary (a tool,
  a consumer, a repo); reversing it is costly or security-sensitive; a future maintainer will
  need the rationale; it sets ownership, a contract, or a durable exception. A prompt addition
  never qualifies on its own. Records live in `docs/decisions/`, numbered, append-only.
- A deliberate shortcut lands in docs/DEBT.md in the same PR (the debt-log prompt does this); closing one moves the entry to Closed.

## Agent authority

What an agent may do in this repo without asking, what needs an explicit go-ahead for that
specific action, and what it must never do. This is additional to the repo rules above; an
approval covers the one action named, not the next one down the line.

Do without asking:
- Read, review, and edit the labels or the title/body text of an existing PR.
- Fetch, and fast-forward a local branch to a remote it has not diverged from.
- Delete a local branch whose remote is gone or whose content already landed on the default
  branch.
- Commit a draft change locally, on its own branch, never on the default branch.
- Run `python validate.py` and `pytest`.

Ask first, every time, for that one action:
- Pushing a branch.
- Opening, merging, or closing a PR.
- Deleting a branch or tag a remote still carries.
- A release cut, or any rewrite of already-pushed history.

Never:
- Commit on the default branch directly.
- Force-push, or any destructive git command, without being told to by name.

## Documentation map

| Fact | Home |
|---|---|
| What the kit is and how to install it | `README.md` |
| Idea-to-PR workflow | `docs/workflow.md` |
| House voice | `docs/writing-standard.md` |
| Adding a prompt, adapter, or check | `docs/contributing.md` |
| Release flow | `docs/releasing.md` |
| Decisions | `docs/decisions/` |
| Deferred work | `docs/DEBT.md` |
| Roadmap and versions | `docs/ROADMAP.md` |
