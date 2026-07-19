# 0012: The tracked tree carries no personal trace

Status: Accepted
Date: 2026-07-10

## Context

The kit began as one person's work. A sweep found the owner's email stamped into both plugin
manifests by the generator's author constant. A manifest value ships on every install, so a
personal address was shipping as the kit's contact. Nothing enforced the boundary between the
kit's team surface and its author's identity.

## Decision

No tracked file carries a personal email, handle, home-directory path, or sync-estate path. The
allowed homes are .github/CODEOWNERS (review routing needs real handles), docs/decisions/ and
CHANGELOG.md (append-only records are never edited to scrub), and the check's own pattern list.
The plugin author field is the org name with no email; the schemas make the address optional.
The `traces` check enforces this in the gate.

## Alternatives

- Replace the personal email with a team address. Deferred, not rejected: no team address exists
  today, and dropping the optional field needs no invented value. A future address is a one-line
  change to the same constant.
- Scrub docs/decisions/ retroactively if a trace ever lands there. Rejected: decision records are
  append-only; the exemption exists so the rule and the ledger never conflict.

## Consequences

The gate grows to 17 checks. Contributors cannot commit a file naming the owner's identity or
machine outside the allowed homes; a seeded-violation test pins the catch. The pattern list is
per-owner and lives in one file; a new maintainer's markers are added there.
