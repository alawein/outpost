---
name: write-doc
description: Use when writing a named coding artifact (a README, a findings note, a report) in the house voice from a supplied template. Produces a findings-first document with the right structure for its kind, plain words, and no padding.
---

# write-doc

This writes a named coding artifact (a README, a findings note, a report) in the house voice from
a supplied template. Findings first, the right structure for its kind, plain words, no padding.
Does not invent results; it writes up what is verified.

## When to use it

- Writing a README, a findings note, or a report. Those three types are the scope; there is
  no other-document mode.
- The work is verified and needs to be written up, not condensed from an existing source.
- Skip it when the goal is to shorten an existing document; that is a summarize task, not a
  write task.

The neighboring jobs route elsewhere:

- A decision that needs a durable record goes to `record-decision`, not here.
- A deliberate shortcut goes to `debt-log`, not here.
- Commit and PR text goes to `prepare-pr`, not here.
- Session state for the next session goes to `handoff-session`, not here.

## Required inputs

- What the deliverable is: README, findings note, or report.
- The template for that type. Required: without a template to check against, stop and ask for
  one rather than inventing a structure.
- The facts, decisions, or results to write up, with their basis.
- The audience and the level of detail they need.

## Steps

1. Take the structure from the template. A README opens with what it is and the one bar that
   proves it works. A findings note puts the conclusion first, then support. A report states the
   question, the finding, and the evidence, in that order.
2. Write findings first. The conclusion or recommendation goes in the first sentence or two.
3. Fill in support: evidence, context, and caveats. Keep each claim tagged with its basis (verified,
   proposed, or unknown).
4. Cut the rest. Drop openers, hedges, and wind-up phrases. Every sentence must change the reader's decision or go.
5. Check against the template. Confirm the structure matches the type, claims are tagged, and the
   prose is in the house voice.

## Output format

The deliverable itself, formatted for its type. No wrapper or commentary around it; if the
deliverable is a markdown file, produce only the file content. Every claim carries its basis; a
rejected idea stays with its reason.

## Stop conditions

- A reader unfamiliar with the work could use the document alone.
- No claim rests on assertion. If a fact is unverified, tag it as proposed or unknown.
- The document does not invent results. Write what is known; name gaps as gaps.
- The document matches its template. If no template was supplied, the run stopped at the
  inputs instead of shipping an untested structure.
