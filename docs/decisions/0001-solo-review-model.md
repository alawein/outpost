# 0001: Solo review model

Status: Accepted
Date: 2026-08-27

## Context

One maintainer. GitHub cannot let an author approve their own pull request, so a required
second approval would block every change the maintainer makes.

## Decision

An outside pull request gets the maintainer's review before merge. The maintainer's own pull
requests merge on green CI (`python validate.py` and `pytest` on Linux and Windows) with no
second approval. `.github/CODEOWNERS` names the maintainer so review requests route there;
branch protection requires the four CI legs, linear history, and no force push.

## Alternatives

A required review from a second account (blocks the maintainer); no protection at all (loses
the CI gate on outside changes).

## Consequences

The gate is the reviewer for the maintainer's work, so the gate has to stay strict. If a
second maintainer joins, this record is superseded by one that names the new rule.
