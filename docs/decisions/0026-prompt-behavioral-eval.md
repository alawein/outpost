# 0026: Add a lightweight behavioral eval for core prompts

Status: Accepted
Date: 2026-08-08

## Context

`validate.py` checks structural and consistency invariants: the catalog matches the prompt
files, the generated plugin mirror byte-matches the source, no personal data is tracked. None of
it checks whether a prompt actually produces the behavior its own contract promises. A comparison
against other Claude Code skill-pack repos found this as Outpost's largest gap: `superpowers` has
an eval harness, `NVIDIA/skills` requires a Tier-3 eval dataset per skill before publishing,
`anthropics/skills` ships no eval at all and is explicit that its examples are for demonstration,
not reliance.

## Decision

A new `evals/` directory holds one fixture per piloted prompt: a seeded repo state, a task
description, and a JSON list of mechanical assertions. `tools/run_evals.py` shells out to
`claude -p --output-format stream-json --verbose` against each fixture (after installing the real
generated skill file into it via `install.py`, so the eval exercises the actual shipped artifact),
reconstructs a transcript from the streamed JSONL events (the one-shot `json` output format
carries no per-tool-call data, so `tool_not_used` needs the streamed form to check anything real),
and checks it with a small assertion engine (`tools/eval_assertions.py`): a file was or was not
modified, a file matching a pattern was created, a named tool was not used, the final text
contains a substring.

Five prompts are piloted: `interrogate` and `plan-change` (must not touch any file, per their own
stop conditions), `record-decision` (must create a new decisions file, must never edit an
existing one), `write-tests` (must create or modify a test file), `debt-log` (must modify
`docs/DEBT.md`). The other 21 core prompts are not piloted; `docs/DEBT.md` names this so the
record stays honest about partial coverage.

The harness is opt-in: `python tools/run_evals.py` is a manual command, never wired into
`validate.py` or `.github/workflows/ci.yml`. It costs real Claude usage per run and is
non-deterministic (an LLM's output text varies run to run even when correct), which conflicts
with the CI gate's fast/free/deterministic contract. The assertion engine itself
(`tools/eval_assertions.py`) is pure and stdlib-only, and gets full `pytest -q` coverage with
fixed, fake transcript data, so the mechanical logic is proven without a live call; only the
orchestration layer needs a real `claude` CLI, and only when run by hand.

## Alternatives

- Full 26-prompt coverage from the start. Rejected: several prompts (`panel`, `prove`, `grill`,
  `premortem`) are adversarial or exploratory by design and do not reduce to a mechanically
  checkable stop condition without real design work of their own; starting with the hardest cases
  works against staying lightweight.
- LLM-as-judge grading (a second Claude call grades the transcript against the prompt's own
  contract). Rejected for this round: doubles the per-eval cost, adds a rubric to design and
  maintain, and introduces a second source of non-determinism on top of the first. A plausible
  extension once the mechanical pilot proves the harness itself is sound.
- Golden-transcript diffing (record one run, compare byte-for-byte later). Rejected: LLM output
  text varies run to run even when the behavior is correct, so this would either constantly fail
  on harmless wording drift or need fuzzy-diff machinery worse than the mechanical-assertion
  approach for a weaker signal.
- Wiring evals into CI on every PR. Rejected: costs real usage per push, needs a Claude Code auth
  secret this repo does not currently have, and is non-deterministic in a way that would make CI
  flaky. Nothing rules out a scheduled `workflow_dispatch` later once the pilot proves stable.

## Consequences

Five prompts now have a real behavioral signal beyond structural validity; a future contributor
adding eval #6 has a working pattern to copy. What this does not yet do: the `file_not_modified`/
`file_created` assertion types cannot express "this exact tracked file was modified, and only
this one" (the `debt-log` eval works around this with a broad `file_created: "*"` check rather
than a precise "DEBT.md specifically grew" check); a fifth assertion type
(`file_modified_only`, or similar) would close this, deferred rather than designed here. Watch
for the mechanical assertions producing false negatives on a correct-but-differently-worded
response (e.g. `plan-change`'s exact-heading `text_contains` checks would fail a response that
uses equivalent but different section names); if that happens often, it is the signal to invest
in the LLM-as-judge alternative above. Each fixture also receives the installed `CLAUDE.md` and
`.claude/settings.json` from `install.py`'s normal install, not just the piloted skill file, so a
no-edit eval's pass is attributable to the guide-plus-skill combination, not proof the skill alone
would behave the same way with no guide present.
