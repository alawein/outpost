---
name: converge
description: Use when you want to drive an artifact to clean, where clean means zero blockers and zero majors after a full check run. Fix and re-run until clean or a round cap, then report honestly, confirmed minors included. A fix-until-clean loop over lint, tests, review, and scrutiny.
---

# converge

One review pass finds some issues. `converge` runs the whole check set, fixes what it finds, and re-runs until the work is clean or it hits a hard round cap. Clean means zero blockers and zero majors after a full check run; a confirmed minor is reported, not required to be fixed. Use it before something ships when a single check is not enough: a diff, a design, a release.

The cap is the safety rule. Without it, the loop never ends or weakens the checks until they pass. `converge` stops at the cap and reports what it could not fix. It never declares clean when it is not.

## When to use it

- Before shipping work that needs more than one pass: a diff, a design, or a plan.
- When lint, tests, and review have not all been run together on the same work in one go.
- In Claude Code only. `converge` ships to Claude alone; the other tools' installs do not
  carry it, because the loop needs a host that runs checks and fixes on its own.
- Skip it for a small, reversible change where a single `code-review` is enough.

## Required inputs

- The work to clean: a diff, a design doc, a plan, or a release.
- Which checks apply: lint, tests, `code-review`, `grill`, `self-refute`, and optionally `prove` (when the work carries key numbers) or `premortem` (when it is a plan or a launch).

## Steps

1. Run every applicable check on the work. Collect all findings into one list, each with a severity: blocker, major, or minor. Run the deterministic checks first (lint, tests), so a cheap failure does not waste a reasoning pass.
2. Stop if clean. Zero blockers and zero majors: stop and report clean, with the evidence (which checks ran, what they covered) and the confirmed minors that remain, reported as findings, not fixed.
3. Fix. Make the smallest change that resolves each blocker and major. A finding names where the fix lands: lint errors in the editor, test failures via `debug-failure` or `write-tests`, code issues via the edit that `code-review` pointed to, design flaws via `refactor-safely` or a rebuild once `grill` or `self-refute` has characterized the flaw. The review and scrutiny prompts diagnose; they do not edit.
4. Re-run the full check set on the fixed work.
5. Loop until clean or until the round cap (default 5) is hit.
6. If the cap is hit with findings remaining: stop. Report the unresolved set honestly: what remains, why it resisted, and the cheapest next step. Do not loop past the cap. Do not skip or relax a check to reach clean.

## Output format

- Round count and which checks were active.
- Per round: findings collected, each with a name, severity, and which check flagged it.
- Final state: clean (with the evidence and any confirmed minors, reported) or not clean (with the unresolved set and why).
- If the cap was hit: the cheapest next step for each unresolved finding.

## Stop conditions

- Never narrow or skip a check to reach clean.
- A finding that reappears across rounds is real; report it, do not suppress it.
- Stop at the cap even if findings remain. Report what is left, then stop.
- Do not declare clean unless zero blockers and majors remain after a full check run. A
  confirmed minor does not block clean; it ships in the report, never silently dropped.
