---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-08-27
---

# How this is built

Outpost is a prompt pack held to one rule: a claim about the kit has to trace to something a
check or a benchmark proves.

## The gate

`python validate.py` runs twenty-three checks on every change: the catalog matches the disk
both ways, every prompt has its five sections, the generated copies (plugin skills, doc spans)
match their source, the docs name the tools the adapters ship, no tracked file carries a
secret or a personal trace, and the prose clears the house voice. CI runs it with the tests
on Linux and Windows. A stranger's pull request meets the same gate as the maintainer's.

## Admission

A new prompt needs one sentence in its pull request: the closest existing prompt and the gap
it leaves. If the closest prompt already does the job, the change extends that prompt. No
memo, no record.

## Evals

Nine prompts have a behavioral eval under `evals/`: a seeded fixture, a real agent run, and
mechanical assertions (a file created or left alone, a tool not used, a value named). They are
opt-in and outside CI; `docs/DEBT.md` tracks which prompts still lack one.
