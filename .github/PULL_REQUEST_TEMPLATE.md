## Outcome

What this PR achieves, in one to three sentences. Closes #___ (or: no linked issue).

## What changed

- The key changes, as bullets.

## Why and scope

The reasoning a reviewer cannot infer from the diff. State what this deliberately does not do
(non-goals), if anything.

## Intent trace

- [ ] The diff matches the stated outcome: nothing from the plan is missing, no unrelated file
      changed.

## Evidence

| Command | Result |
|---|---|
| `python validate.py` | |
| `python -m pytest -q` | |

## Provenance

`OUTPOST-ORIGIN` / `CLEAN-ROOM` / `GENERAL-PRACTICE` / `REJECTED-PROPRIETARY` / `REJECTED-FIT` /
`UNKNOWN`, only if this PR adapts an idea observed outside Outpost. "N/A" otherwise.

## Release impact

- [ ] User-visible: `CHANGELOG.md`'s `[Unreleased]` section updated, one `release:*` label applied.
- [ ] Not user-visible.

## Generated files

- [ ] Regenerated via `python tools/build.py` and committed.
- [ ] No generated file touched.

## Risk, rollback, and limits

Known caveats, out-of-scope work, and how to revert if this is wrong. "None" is a valid answer.

## Notes for reviewers

Where to focus, the risky part, or anything a reviewer should know. "None" is a valid answer.
This is a solo repo: no automated PR reviewer is wired and CodeRabbit is off (`.coderabbit.yaml`).
