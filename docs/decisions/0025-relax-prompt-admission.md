# 0025: Relax the prompt admission bar

Status: Accepted
Date: 2026-08-08

## Context

ADR-0013 requires six fields for prompt 26 onward: distinct job, nearest sibling, unsafe
default, binding mechanism, dogfood case, deletion condition. All six, upfront, before a new
prompt ships. That bar was sized for a pack that had settled; Outpost's architecture is expected
to change substantially over the near term, and writing all six fields in full before a single
line of a new prompt can ship is a drag on that pace, not a correctness problem the six fields
were solving.

Two of the six directly address ADR-0013's actual reason for existing: overlapping prompts with
no test for duplication (the audit that produced ADR-0013 found `refactor-safely` and `simplify`
scoring five on overlap). Distinct job and nearest sibling are that test. Unsafe default is the
field that answers a different, also load-bearing question: why does this prompt need to exist
at all, not just why isn't it a duplicate. The remaining three (binding mechanism, dogfood case,
deletion condition) are important but procedural: they describe how the prompt enforces itself,
prove it once, and name its own exit condition. None of the three block a reviewer from judging
whether the prompt is a real, distinct, justified addition.

## Decision

Supersede ADR-0013's admission bar with a three-required, three-recommended split.

**Required at admission (blocking; a prompt lacking any of these does not enter the pack):**
- Distinct job: the recurring task the new prompt owns that no shipped prompt already owns.
- Nearest sibling: the closest existing prompt, and what the new one does differently.
- Unsafe default: the wrong behavior an agent falls into without this prompt.

**Recommended, not blocking (expected in a follow-up PR, not optional forever):**
- Binding mechanism: the contract line that blocks the unsafe default.
- Dogfood case: one real run in this repo, recorded in `docs/dogfooding.md`.
- Deletion condition: the observation that would justify removing the prompt later.

An admission record missing the three recommended fields must say so explicitly and name the
follow-up that will add them, rather than silently omitting them. This is a relaxed bar, not an
abolished one.

## Alternatives

- Keep all six fields, only relax the append-only rule instead. Rejected: the friction named was
  specifically the six fields at admission time, not the inability to revise a record later.
- Drop to only distinct job and nearest sibling, no unsafe default required. Rejected: unsafe
  default is the field that justifies adding the prompt at all, not just proves it is not a
  duplicate; dropping it risks admitting a prompt nobody can say is actually needed.
- Keep all six fields, only lighten the format (inline PR-body answers instead of a dedicated ADR
  file, promoted to a full record later). Not chosen: it does not reduce what must be written at
  admission time, only where it is written.

## Consequences

A new prompt ships faster during a period of active architectural change, while the two checks
that prevent silent duplication (distinct job, nearest sibling) and the one that justifies adding
complexity at all (unsafe default) stay mandatory. What to watch: the three deferred fields
becoming permanently skipped in practice rather than genuinely filled in later, which would
quietly erode the enforcement mechanism and the dogfood evidence ADR-0013 was built to require.
Reverse this (return to all six required at admission) if that pattern shows up.
