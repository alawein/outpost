---
name: orient-repo
description: Use on first contact with an unfamiliar repo, before planning a change. Builds a read-only map of how the project is built, tested, and laid out, so the first plan rests on facts, not guesses.
---

# orient-repo

Use this when you first land in a repo you do not know. Build a read-only map of what the project
is, how it builds and tests, where the code lives, and which conventions matter. Hand that map
to `plan-change`.

## When to use it

- The first task in a repo you have not worked in, or after a long gap.
- Before plan-change when the layout, build, or test commands are unknown.
- Not on a repo you already know well; skip straight to planning.

## Required inputs

- Read access to the repo.
- The task or goal, so the map can note which areas it touches.

## Steps

1. Read the entry docs: `README`, `CONTRIBUTING`, and any agent guide such as `CLAUDE.md`, `AGENTS.md`, or `.cursor/rules`.
2. Find the build, test, and lint commands in the package manifest, CI config, and any `Makefile` or task runner. Note the language and version floor.
3. Map the layout: source directories, test directories, config, and where a change like this belongs.
4. Note the conventions: commit and branch model, formatter, and any voice or structure rules.
5. Locate the area the task touches and name the files a change would likely involve. Do not edit them.

## Output format

- What it is: one or two sentences.
- Build and test: the exact commands, copied from the source that defines them.
- Layout: the directories that matter, one line each.
- Conventions: the commit, branch, and style rules to follow.
- For this task: the area and the likely files.

## Stop conditions

- Stop when a newcomer could build, test, and place a change from the map alone.
- Report a command only if you found where the repo defines it. Do not invent one.
- Do not edit any file. This is a read-only map; the change is plan-change's job.
