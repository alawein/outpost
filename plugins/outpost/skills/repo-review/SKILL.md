---
name: repo-review
description: Use when a whole repo needs a health audit before you trust or own it. Judges structure, docs truth, test coverage, dead code, and drift between docs and code, then emits findings shaped for triage. An opt-in ownership lens hunts single-owner assumptions when a one-person repo becomes a team surface. Distinct from orient-repo, which maps a repo without judging it.
---

# repo-review

`orient-repo` maps a repo so you can work in it. `repo-review` judges it: where the structure
fights the reader, where the docs say things the code does not do, where tests are thin, what
is dead, and what has drifted. The widest review lens in the kit. Its findings feed `triage`.

## When to use it

- You are taking ownership of a repo and need its true state, not its README's claims.
- Before a release, an audit, or a handoff that must survive scrutiny.
- On a schedule, as a health check that catches drift while it is cheap to fix.
- With the ownership lens, when a repo built by one person is gaining a second contributor,
  a team, or a public audience, or before transferring ownership or open-sourcing.
- Skip it when one change needs review; that is `code-review`. Skip it when you only need a
  map; that is `orient-repo`.

## Required inputs

- The repo root, readable.
- What done means for this repo: its stated gate (build, tests, checks), if one exists.
- Optional: focus areas to weight, and areas to skip (generated code, vendored trees).
- For the ownership lens: the allowed homes for personal traces (git history, CODEOWNERS,
  append-only ledgers).
- Where the output goes: the conversation by default, or a file the caller names.
- The review is read-only on the repo; running its stated gate is the only execution.

## Steps

1. Run the repo's own gate first. A red gate is finding number one; note it and continue on
   the tree as it stands.
2. Structure pass. Where does the layout fight the reader: duplicate homes for one fact,
   files that carry unrelated jobs, names that lie about contents.
3. Docs truth pass. Take each load-bearing claim in the README and docs (install steps,
   commands, counts, supported tools) and check it against the code. A claim you cannot
   verify is a finding tagged unknown, not a pass. Start with the README and install claims,
   then the usage docs; name any doc left unread as a gap.
4. Test pass. What behavior matters and is uncovered. Judge coverage of contracts, not line
   percentages. Name the riskiest untested path.
5. Dead and drifted pass. Unreferenced files, commented-out blocks, config for tools no
   longer present, docs describing removed features.
6. Write findings, one line each, numbered (F1, F2, ...) so triage can key on them: what is
   wrong, the evidence (file and line), a severity guess (blocker, major, minor), and a
   confidence tag (verified, proposed, or unknown).

## The ownership lens (opt-in)

Off by default. Turn it on when a repo built by one person is becoming a team surface. It
adds two passes before the findings are written; their hits join the same findings list.

- Mechanical sweep first. Grep for personal emails, usernames, home-dir and machine paths,
  and hosts. Every hit outside an allowed home is a finding.
- Generated-surface pass. Check what generators and manifests stamp into artifacts
  (author fields, contact addresses, homepages). A personal value here ships on every
  install.
- When the lens is off, say so in the gaps line, so a reader knows ownership was not judged.

## Output format

- Verdict first: one sentence on the repo's health and the single most important fix.
- Findings table: id, finding, evidence, severity guess, confidence (verified, proposed, unknown).
- Gaps named as gaps: what this review could not see and why (no device, no CI history,
  no runtime).

## Stop conditions

- Every pass above ran, or the skipped pass is named with the reason.
- Each finding carries evidence a reader can check without re-running the review.
- The findings list is honest about confidence: nothing verified-tagged on assertion alone.
