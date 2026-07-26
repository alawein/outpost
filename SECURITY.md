---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-07-26
---

# Security policy

Outpost is a personal, standard-library-only kit that installs prompt files and runs local checks.
It has no network calls and no runtime dependencies, so its attack surface is small: the main risk
is the installer acting on a crafted `.outpost/manifest.json` in a cloned repo.

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
