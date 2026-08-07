---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-07-26
---

# Workflow: from idea to PR

Outpost is one path from first repo read to handoff, with the same prompts across every tool. This page is that path: the ordered steps, the Claude Code shortcuts that bundle them, and the full prompt list. In Claude the prompts load by description; in the other tools you point at the matching file.

## The path

Run the step that matches the work in front of you. Skip any step a change does not need.

```mermaid
flowchart LR
    Start --> Plan --> Build --> Check --> Ship --> Record
    Check -.->|iterate| Build
```

1. Start. `orient-repo` maps an unfamiliar repo before you touch it; `interrogate` hardens a vague ask into a defined one before you plan.
2. Plan. `plan-change` scopes a non-trivial change against the real repo. `split-change` breaks an over-scoped change into revertible units. `premortem` assumes a costly plan failed and prevents the top causes.
3. Build. `implement-change` makes the smallest correct edits with the tree runnable. `write-tests` covers the behavior and the contract. `debug-failure` reproduces then root-causes a break. `refactor-safely` changes shape, not behavior. `simplify` folds duplication out of changed code.
4. Check. `self-refute` red-teams your own fresh output; `grill` stress-tests a design, plan, or diff. `check-intent` reconciles the diff against the plan before `code-review` runs. `code-review` is the structured correctness pass. `prove` recomputes a claim that must survive stakeholders; `panel` convenes expert lenses for a wide decision. For a whole repo, `repo-review` audits it and `triage` ranks the findings.
5. Ship. `prepare-pr` drafts the commit and PR and runs the pre-merge checks. `respond-to-review` acts on feedback. `handoff-session` hands off cleanly mid-work. A human opens and merges the PR.
6. Record. `record-decision` captures an architecture decision; `debt-log` records a shortcut with its reason, cost, and revisit trigger. `write-doc` writes a README, findings note, or report.

## Claude Code shortcuts

In Claude Code the common sequences are one typed command. Three bundle several prompts; the rest are one-prompt shortcuts, plus an environment check. Claude only: the other tools run the prompts above directly.

| Command | Runs |
|---|---|
| `/outpost:drive` | plan, implement, test, then hands to ship |
| `/outpost:ship` | self-refute, code-review, prepare-pr, stopping on a blocker |
| `/outpost:stress` | routes to the right scrutiny prompt: interrogate, self-refute, grill, or premortem |
| `/outpost:doctor` | checks the environment: the kit gate here, the installer's verify elsewhere |
| `/outpost:repo-review` | audits a whole repo: a verdict, a findings table, and the gaps |
| `/outpost:code-review` | reviews the working diff, one honest verdict |
| `/outpost:simplify` | cleans the working diff, tests green after each cleanup |
| `/outpost:prove` | tags each claim CONFIRMED, QUALIFIED, REFUTED, or UNKNOWN |
| `/outpost:triage` | ranks a findings list into fix now, defer, or reject |

`converge` runs the fix-until-clean loop over lint, tests, review, and scrutiny; it ships to Claude Code only.

## All the prompts

The kit ships <!-- GENERATED:core-count-digits -->26<!-- /GENERATED:core-count-digits --> prompts, grouped by stage.

<!-- GENERATED:skills-table -->
| Stage | Prompts | Use them to |
|---|---|---|
| Start | `orient-repo` `interrogate` | map an unfamiliar repo; surface hidden assumptions before you build |
| Plan | `plan-change` `split-change` `premortem` | scope the work, split it if it is too big, check it survives failure before you commit |
| Build | `implement-change` `write-tests` `debug-failure` `refactor-safely` `simplify` | edit, test, debug, and reshape without changing behavior |
| Review and ship | `check-intent` `code-review` `prepare-pr` `respond-to-review` `triage` `handoff-session` | review, draft the PR, answer feedback, hand off |
| Converge | `converge` | drive an artifact to clean over lint, tests, review, and scrutiny rounds |
| Scrutiny | `self-refute` `grill` `prove` `panel` `repo-review` `repo-hygiene-sweep` | challenge your own fresh output, a design, plan, or diff, or claims that must survive scrutiny; convene expert lenses for a wide decision |
| Record | `record-decision` `debt-log` | capture an architecture decision, or log a shortcut with its reason, cost, and revisit trigger |
| Write | `write-doc` | write a README, findings note, or report from a supplied template: findings first, plain words, no padding |
<!-- /GENERATED:skills-table -->

## How each tool loads the prompts

- Claude Code: prompts are skills, loaded by description. Describe the task.
- Codex: prompts are files under `.agents/prompts/`, listed in `AGENTS.md`. Apply the matching one.
- Cursor: prompts are rules under `.cursor/rules/`. Reference the matching one.
- GitHub Copilot: repo-wide `.github/copilot-instructions.md` plus prompt files in `.github/prompts/`. Reference the matching one in chat.

See `docs/adapters.md` for what differs between the tools and why.

## Working habits

- Done means checked, not only changed. Run the checks and read the output first.
- Make the smallest change that solves the problem. Flag added complexity.
- One logical change per commit, one concern per PR.
- Findings first in docs, reviews, and PR bodies. Plain words.
