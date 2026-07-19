# 0006: Require a maintainer review on the kit's own repo

Status: Accepted
Date: 2026-06-30

## Context

The kit's own repo banned a CODEOWNERS file. The `secrets` gate failed on any `.github/CODEOWNERS` that named a person. CLAUDE.md and the contributing guide said to name no reviewer. That rule fits the kit's product stance: the installer ships prompts, not reviewers, and must never drop a CODEOWNERS into a consumer's repo. But the ban also applied to the kit's own repo, so `main` had no review gate. Any push could merge unreviewed. With the team at six maintainers, we wanted a maintainer to approve a change to `main` before it merges.

## Decision

Reverse the no-CODEOWNERS rule for the kit's own repo only. Add `.github/CODEOWNERS` naming the six maintainers. Protect `main` to require one code-owner approval plus green CI, with admins able to bypass so a maintainer can still squash-merge. The `secrets` gate no longer bans a CODEOWNERS file. CLAUDE.md and the contributing guide carry the new policy. This is governance for this repo, not a change to what the kit installs: the cross-tool installer still ships no CODEOWNERS into a consumer's repo (ADR-0001).

## Alternatives

- Branch protection alone, no CODEOWNERS. Rejected: protection can require a review, but CODEOWNERS is what routes the request to the maintainers; without it, no one is auto-requested.
- Keep the `secrets` ban and exempt the repo's own file. Rejected: the check has no repo-versus-consumer context, so the clean move is to drop the ban and keep the check's real job (keys and junk).
- Do nothing. Rejected: `main` had no review gate as the team grew.

## Consequences

- Easier: every change to `main` gets a maintainer's eyes, and the six are routed automatically.
- Harder: a solo change needs a second approver or an admin bypass; an author cannot self-approve.
- Watch: the `secrets` check no longer flags a stray auto-request CODEOWNERS, but the kit never installs one, so the exposure is only in this repo, which is the intent. Reverse this if the kit ever needs to hold its own repo to the no-CODEOWNERS rule again.
