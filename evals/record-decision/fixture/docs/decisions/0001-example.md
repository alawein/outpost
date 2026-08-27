# 0001: Use SQLite for local storage

Status: Accepted
Date: 2026-01-01

## Context

The app needs local persistence with no external service dependency.

## Decision

Use SQLite via the standard library's sqlite3 module.

## Alternatives

- A JSON file: rejected, no query support at scale.
- Postgres: rejected, adds an external service dependency this app does not need.

## Consequences

Simple to deploy, no server to run. Revisit if concurrent-write volume grows past what SQLite
handles well.
