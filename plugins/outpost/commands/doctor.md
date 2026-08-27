---
description: "Check dependencies and validation before a run."
---

# /doctor

Check dependencies and validation before a run. Reports failures; fixes nothing.

In the Outpost kit repo itself, run `python validate.py` from the repo root; it proves the kit source tree. In a repo where Outpost is installed, that gate does not exist; verify the install instead by running `python install.py --tool <tool> --project <path-to-this-repo> --verify` from an Outpost checkout. If any check is red, name it and the cause; do not repair anything.
