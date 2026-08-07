---
type: canonical
status: accepted
last_updated: 2026-08-07
---

# ADR 0001: This directory is a compliance stub, not Outpost's ADR ledger

## Status

Accepted.

## Context

The alawein org's shared doctrine CI (`alawein/alawein/.github/workflows/doctrine-reusable.yml`)
runs an unconditional hard gate that fails when `docs/adr/` is absent or empty. Adopting that
workflow (PR #5, PR #6) auto-generated a boilerplate ADR here that itself declared `docs/adr/`
the place to track architecture decisions, contradicting Outpost's real, pre-existing ledger at
[docs/decisions/](../decisions/), which already holds 20 append-only records and is the location
named in [docs/architecture/topology.md](../architecture/topology.md). See
[docs/decisions/0021-adr-ledger-conflict.md](../decisions/0021-adr-ledger-conflict.md) for the
full decision record.

## Decision

This file exists only to keep the alawein doctrine gate's `docs/adr/` presence check satisfied.
It is not a decision record and nothing new is added here. Outpost's actual architecture
decisions live in [docs/decisions/](../decisions/); start from
[docs/decisions/0000-template.md](../decisions/0000-template.md) when recording one.

## Consequences

The org's doctrine CI stays green without moving or duplicating Outpost's real ADR history.
