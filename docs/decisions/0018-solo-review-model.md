# 0018: Solo review model for the Outpost repo

Status: Accepted
Date: 2026-07-23

## Context

ADR-0006 set a maintainer-review gate for the kit's own repo: CODEOWNERS naming six maintainers,
branch protection requiring one code-owner approval plus green CI, with admin bypass so a
maintainer could still squash-merge. That fit a six-person team.

ADR-0017 forked the kit into a personal MIT project, `alawein/outpost`, with a single owner.
`.github/CODEOWNERS` now names only `@alawein`. GitHub forbids approving your own pull request, so
the one-approval rule ADR-0006 set is unsatisfiable for the sole author: every merge would be an
admin bypass, and the DEBT ledger already records that failure mode twice. Several docs (CLAUDE.md,
contributing.md, cadence.md's team profile) still describe the team gate as if it applied, which is
misleading for anyone reading them and impossible to follow.

## Decision

`alawein/outpost` is solo-maintained. Outside contributions get the owner's review before merge.
The owner's own pull requests merge on green CI (`python validate.py` and `pytest`) without a second
approval, because none can exist. CODEOWNERS routes review to the owner. This is the sanctioned
path, not an admin bypass.

This does not change what the kit installs: the cross-tool installer still ships no CODEOWNERS into
a consumer's repo (ADR-0001). It governs this repo only, the same scope ADR-0006 claimed.

Supersedes ADR-0006.

## Alternatives

- Keep the ADR-0006 gate and record each self-merge as an admin bypass. Rejected: every merge
  becomes a logged exception, which the DEBT ledger shows accreting rather than resolving; a rule
  no one can satisfy is worse than an honest one.
- Add a real second reviewer to CODEOWNERS. Rejected: no second maintainer exists for this personal
  repo; inventing one to satisfy a gate is ceremony, not review.
- Do nothing and leave the docs describing a team gate. Rejected: the docs would keep telling a
  contributor (or an agent running `prepare-pr`) to wait for an approval that cannot arrive.

## Consequences

- Easier: the owner merges own PRs directly on green CI, no bypass framing, and the docs match what
  GitHub actually allows for a solo repo.
- Harder: nothing enforces a second set of eyes on the owner's own changes; the green gate
  (`validate.py` + `pytest`) and the kit's own review prompts are the substitute.
- Watch: reverse this if the repo gains a second maintainer, at which point ADR-0006's one-approval
  gate becomes satisfiable again and should be restored by a new ADR.
