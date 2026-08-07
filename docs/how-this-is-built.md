---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-08-07
---

# How this is built

Outpost is a prompt pack, but the pack itself is held to a standard most prompt collections are
not: nothing ships without evidence.

## Every prompt clears an admission bar

[ADR-0013](decisions/0013-prompt-admission.md) sets the entry test for prompt 26 onward: a
distinct job no shipped prompt already owns, the nearest sibling and what the new one does
differently, a real unsafe default it prevents, the exact contract line that blocks it, one real
dogfood run, and a stated condition that would justify deleting it later. A prompt that cannot
state all six does not enter the pack.

[ADR-0023](decisions/0023-admit-check-intent.md) and
[ADR-0024](decisions/0024-prose-length-check.md) are recent, real examples: both name their
distinct job, their nearest sibling, and their unsafe default before either shipped.

## The dogfooding ledger is honest, not curated

[docs/dogfooding.md](dogfooding.md) is append-only: a finding stays recorded whether it flatters
the tool or not. The `check-intent` prompt's own first admission run is one example: its first
pass reported clean, then the test suite caught a real gap the prompt itself had missed. The row
stays, unedited, because the point of the ledger is to be checkable, not to look clean.

## The gate is the gate

`python validate.py` runs 21 checks on every change: the catalog matches the prompt files, the
generated plugin matches the catalog, no personal trace or secret is tracked, and (since
[ADR-0024](decisions/0024-prose-length-check.md)) no paragraph in the tracked docs sprawls past
100 words. The same gate that blocks a stranger's pull request blocked every change that built
this page.
