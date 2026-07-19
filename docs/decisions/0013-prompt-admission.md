# 0013: Prompt admission

Status: Proposed
Date: 2026-07-11

## Context

ADR-0002 says widening the prompt pack is a new decision, but it does not say what such a
decision must show. ADR-0011 admitted three prompts by naming their jobs; `deassume` made the
pack 25 with only a changelog entry, and no accepted decision covers it under a repeatable
entry test (audit F12). Growth without a test breeds siblings that overlap (`refactor-safely`
and `simplify` score five on overlap in the audit scorecard) and contracts that do not bind
(`converge` and `prove` score one on bind). The pack needs an entry bar a reviewer can check,
not a case-by-case argument.

## Decision

Prompt 26 onward enters the pack only with an admission record: a decision in this
directory that names, for the candidate prompt,

- the distinct job: the recurring task it owns that no shipped prompt owns;
- the nearest sibling: the closest existing prompt and what the candidate does that it does not;
- the unsafe default: the wrong behavior an agent falls into without this prompt (no unsafe
  default, no entry);
- the binding mechanism: the contract line (an input, step, or stop condition) that blocks the
  unsafe default, not a line that describes good practice;
- the dogfood case: one real run in this repo, recorded in the dogfooding ledger, before or
  with the admitting PR;
- the deletion condition: the observation that would remove the prompt, for example two
  recorded sessions where callers route to its sibling instead.

A prompt produced by consolidating existing prompts (a merge or a rename) follows the same
record; retiring the absorbed prompts is its deletion evidence. The rule governs admission
only. It does not evict `deassume`, `prove`, or `panel` retroactively; their keep-or-retire
calls are separate rulings.

## Alternatives

- Amend ADR-0011 to cover `deassume` after the fact. Rejected: records are append-only, and a
  patched record still leaves prompt 26 without a test.
- A numeric cap on pack size. Rejected: a cap forces a fight over slots instead of a test of
  fit; the scorecard shows the problem is overlap and weak binding, not raw count.
- Leave admission to per-PR review judgment. Rejected: that is the current state, and it
  admitted the 25th prompt with no decision at all.

## Consequences

Adding a prompt costs one short record and one dogfood run, which is the point: the record is
cheaper than the pack carrying a duplicate. The six fields give a reviewer a checklist and
give retirement a trigger named at entry. What to watch: an admission record can be written as
advocacy; the dogfood case and the deletion condition are the two fields that keep it
falsifiable. Reversed by a future decision if the record proves heavier than the drift it
prevents.
