---
name: repo-hygiene-sweep
description: Use when several repositories need a read-only hygiene sweep before any repair work begins. Inventories the fleet, proves each finding from its source, and routes safe work without mutating protected targets.
---

# repo-hygiene-sweep

A fleet sweep finds work before it changes work. Begin with a read-only inventory, classify each
target, discover its own gates, and review only targets that are safe to inspect. A finding is a
claim with evidence, not a reason to edit.

## When to use

- A group of repositories needs a hygiene review before a repair, handoff, or ownership change.
- You need one report that distinguishes safe work from dirty, archived, generated, vendored,
  untested, or unreadable targets.
- You need findings routed for later action, not a batch of unapproved edits.

## Required inputs

- The fleet roots and the scope of the sweep.
- Read access to each target and its git state, when it has git metadata.
- Explicit authority for any mutation or external action beyond reading and approved local checks.

## Steps

1. Fleet inventory. Build a read-only inventory of every target. Record its root, git state,
   branch when present, and visible ownership or archive markers. Do not edit during inventory.
2. Topology classification. Classify each target as active, dirty, archived, generated, vendored,
   untested, or unreadable. Protected target rules mean:
   - Do not edit a dirty target.
   - Do not edit an archived target.
   - Do not edit a generated target.
   - Do not edit a vendored target.
   - Do not edit an untested target.
   - Do not edit an unreadable target.
3. Workflow gate discovery. Read each target's contributor rules, CI, scripts, and test setup.
   Use only repo-defined commands. Copy its baseline and final gate commands from the target repo.
   Inspect each copied command's effects before execution. Read-only local checks may run. A
   repo-defined command is not automatically safe. Commands that install or update dependencies,
   write outside an approved state directory, access external systems, or otherwise mutate state
   require explicit authority. Each copied command is an evidence gate. Do not invent a command.
4. Repo review. Review only active, clean targets. Inspect structure, docs, tests, stale files,
   traces, and declared dependencies without changing them. Capture source evidence for every
   finding as a path and line, command output, or other source location.
5. Triage. Give every finding a confidence tag and a route: fix now, defer, reject, or investigate.
   Include a verification command copied from the target repo for the routed work.
   For routed work, topology and catalog optimization comes first, workflow triage comes second,
   then simplification, technical debt reduction, and behavior-preserving refactoring. This order
   routes work only; it does not authorize a change.
6. Clean-target baseline. Before a small change, run the copied baseline gate on the clean target.
   A red baseline is a finding and stops mutation until the route or authority says otherwise.
7. Small changes. Make only the approved smallest change on a clean target. Keep the change tied
   to one routed finding. No move, delete, archive, commit, push, or dependency change without
   explicit authority.
8. Unchanged-test proof. When refactoring, keep refactor test parity: the same target behavior
   remains covered before and after the change. Run the copied verification command and record its
   result. Do not claim a test result that was not run.
9. Final fleet report. Run the copied final gate for each changed clean target. Report untouched
   protected targets, findings, routes, authority used, baseline and final gate results, and gaps.

## Output format

- Fleet table: target, topology classification, git state, baseline gate, final gate, and action.
- Findings table: id, finding, source evidence, confidence, route, and verification command copied
  from the target repo.
- Change record: target, approved scope, authority, command results, and unchanged-test proof.
- Gaps: targets not reviewed or changed, with the reason and the next required authority.

## Stop conditions

- Stop before mutation when a target is dirty, archived, generated, vendored, untested, or
  unreadable.
- Stop when a finding lacks source evidence, confidence, a route, or a verification command copied
  from the target repo.
- A move requires explicit authority.
- A delete requires explicit authority.
- An archive requires explicit authority.
- A commit requires explicit authority.
- A push requires explicit authority.
- A dependency change requires explicit authority.
- An external action requires explicit authority.
- Stop after the final fleet report. Do not turn a sweep into unapproved repair work.
