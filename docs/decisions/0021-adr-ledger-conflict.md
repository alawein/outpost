# 0021: docs/adr/ is a compliance stub, docs/decisions/ stays authoritative

Status: Accepted
Date: 2026-08-07

## Context

The alawein org's shared doctrine CI (`alawein/alawein/.github/workflows/doctrine-reusable.yml`,
adopted into Outpost by PR #5 and PR #6) runs `validate-repo-framework.py`, an unconditional hard
gate that does not honor the workflow's `strict` input and runs before any other check. It fails
when `docs/adr/` is absent or empty. Adopting the workflow auto-created
`docs/adr/0001-repo-architecture.md`, a generic boilerplate ADR whose own text read "Track
architecture decisions under `docs/adr/`," directly contradicting Outpost's real ledger: 20
append-only records under `docs/decisions/`, referenced throughout the repo (README, the
`record-decision` prompt, and `docs/architecture/topology.md`, which already states "`docs/
decisions/` is append-only ADR history"). Two files both claimed to be "ADR 0001" for the same
repo with opposite answers about where decisions live.

## Decision

`docs/decisions/` remains the sole ADR ledger for Outpost. `docs/adr/0001-repo-architecture.md`
is rewritten to say plainly that it is a compliance stub for the alawein doctrine gate, points to
`docs/decisions/`, and takes no new records. Nothing moves: the 20 existing records, their
numbering, and every cross-reference to `docs/decisions/` stay as they are.

## Alternatives

- Delete `docs/adr/`. Rejected: `validate-repo-framework.py`'s presence check is unconditional
  and would fail the org's required doctrine CI on every future PR.
- Move the real ledger from `docs/decisions/` to `docs/adr/` to match the org default. Rejected:
  rewrites an append-only history, breaks 20 records' own cross-references and every doc that
  names `docs/decisions/`, for churn far larger than a one-file compliance stub avoids.
- Fix the org's gate script to accept `docs/decisions/` as an alternate valid path. Rejected for
  now: out of scope here, since `validate-repo-framework.py` lives in a different repository
  (`alawein/alawein`) this work has no authority to change. Worth revisiting as a cross-repo
  follow-up.

## Consequences

The org's doctrine CI stays green and Outpost's real ADR history stays put, unmoved and
uncontested. A new reader who opens `docs/adr/` first sees one short stub explaining the
redirect, rather than a second, contradictory ledger. Reverse this if the org's gate script
starts accepting a configurable ADR path, or if `alawein/alawein` changes the requirement.
