# Agent guide for this repo

The core prompts live in `.agents/prompts/` as plain files. Open the one that fits the step. Read
this guide at the start of a session. Replace the bracketed text for your project, then delete it.

## What this project is

[One or two sentences on what the project is and who it helps.]

## Prompts

Use the one that fits the step you are on.

- `plan-change` before a non-trivial edit.
- `implement-change` to make the change in small steps.
- `write-tests` for behavior and expected contracts.
- `debug-failure` when a check fails.
- `refactor-safely` to change structure without changing behavior.
- `code-review` for a structured review.
- `prepare-pr` to draft the commit and PR and run checks.
- `handoff-session` to leave a short handoff for the next session.

## Working agreement

- Plan before a non-trivial edit.
- Make the smallest change that solves the problem.
- Add or update a test when behavior changes.
- Run the required checks before you call the work done. [Name the required check.]
- Stage explicit paths. Keep `.env` and secrets out of git.
- Imperative commit subject, one concern per commit or PR.

## Final report

End with what changed, what you ran, and the results. Say what is verified and what is still open. Do not claim work you did not run.
