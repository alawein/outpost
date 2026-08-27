---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-08-27
---

# Security policy

Outpost is a personal, standard-library-only kit that installs prompt files and runs local checks.
`install.py`, `validate.py`, and everything under `kit/` make no network calls and have no runtime
dependencies, so the installed kit's attack surface is small: the main risk there is the installer
acting on a crafted `.outpost/manifest.json` in a cloned repo. Two opt-in dev tools under `tools/`
do call out: `sync_labels.py` shells to the `gh` CLI, and `run_evals.py` shells to the `claude`
CLI; neither is installed into a consumer project or runs as part of `validate.py`.

## Reporting a vulnerability

Report privately, not in a public issue. Use GitHub's private vulnerability reporting on this repo
(the "Report a vulnerability" button under the Security tab), which opens a private advisory with
the maintainer.

Please include what you found, the steps to reproduce it, and the platform (the kit runs on Windows
and Linux, and some path-handling differs between them). A proof-of-concept manifest or command line
helps most.

## What to expect

This is a solo-maintained project, so response is best-effort, not contractual. Expect an
acknowledgement within about a week. A confirmed issue is fixed on a short-lived branch with a
regression test, released as a patch, and credited in the changelog under Security unless you prefer
otherwise.

## Supported versions

The latest released minor version receives fixes. Older versions do not; upgrade to pick up a fix.
