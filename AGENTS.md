---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-07-26
---

# Agent guide for Outpost

Outpost installs coding-agent prompts for Claude, Codex, Cursor, and Copilot. The
working rules live in `CLAUDE.md`; read that first. This file adds the review guidelines an
automated reviewer applies to a pull request.

## Working agreement

Follow `CLAUDE.md`. In short: standard library only, stage exact paths, one concern per commit,
and run `python validate.py` and `python -m pytest -q` before calling a change done.

## Review guidelines

Review a pull request against these, most serious first. Comment only on a real issue; if the PR
is clean, say so.

- Correctness: the change does what its description says. A refactor must not drift behavior.
- The gate: `python validate.py` (the check suite) and `pytest` must pass. A change that reddens
  either is a blocker.
- Standard library only: no third-party import in the kit, the installer, or the checks.
- Writing standard: plain ASCII, no em or en-dashes, none of the banned words in
  `docs/writing-standard.md`. Applies to prose, comments, and docs. The files that must name the
  banned words to define them are exempt, as the voice check already allows
  (`docs/writing-standard.md` and the ledger-voice output style).
- No secrets or personal traces: no key, token, personal email, handle, or machine path in a
  tracked file. Real handles are allowed where the traces check allows them: `.github/CODEOWNERS`,
  the decision records, and the changelog.
- Scope: one concern per PR. Flag a diff that mixes unrelated changes.
- Tests: new behavior carries a test that asserts the contract, not the implementation detail.
- The catalog is the source of truth: a new prompt, template, adapter, or check lands in
  `kit/catalog/catalog.json` and the file it points at, together.
