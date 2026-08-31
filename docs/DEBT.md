---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-08-31
---

# Debt

One entry per deliberate shortcut: what it is, why it was taken, what would close it. An entry
moves to Closed with the change that closed it; it is never deleted.

## Open

- 2026-08-27: nine of twenty-eight prompts have a behavioral eval (`evals/`, `tools/run_evals.py`).
  The exploratory prompts (`panel`, `prove`, `grill`, `premortem`) have no mechanically
  checkable assertion yet. Taken because a bad assertion is worse than none. Close by an
  assertion type that checks structure (headings present, no file modified) for each.
- 2026-08-27: `plugins/outpost/` is listed in no outside plugin marketplace; the repo serves as
  its own through `.claude-plugin/marketplace.json`. Taken because a listing needs an outside
  submission. 1.0 shipped 2026-08-31, so close by submitting now.
- 2026-08-27: the `code-review` eval's `text_contains_any` list (`evals/code-review/assertions.json`)
  is generic: any bounds discussion passes without naming the seeded `pct` defect. Taken to get
  the eval running. Close by asserting on `pct` and the missing test file.

## Closed

- 2026-08-27: `--verify` reads no create-mode guide, so `guide-edited` is a published miss in
  `benchmarks/drift/results.json`. Taken because the guide is the user's file. Close by an
  information line for a kit-written guide whose bytes no longer match the manifest `kit_hash`,
  then re-run `python benchmarks/drift/run.py --write`. Closed 2026-08-27: `--verify` reports `EDITED`.
