---
description: "Audit the whole repo: structure, docs truth, tests, dead code, drift."
---

# /repo-review

Audit the whole repo and return findings shaped for triage.

Run `repo-review` over the current repo. Start from the repo's own gate, then judge
structure, docs truth, test coverage, dead code, and drift. Verdict first, then the findings
table (finding, evidence, severity guess, confidence), then the gaps the review could not
see.

When the findings list is longer than one sitting can fix, run `triage` next (the /triage
command is its front door).
