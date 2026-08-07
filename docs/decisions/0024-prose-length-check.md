# 0024: Mechanical paragraph-length ceiling

Status: Accepted
Date: 2026-08-07

## Context

`docs/writing-standard.md` asks for extreme concision, and the `voice` check enforces plain
ASCII and a banned register, but nothing mechanically bounds a paragraph's length: sprawl was
editorial judgment only. The ACK capability comparison
(`.superpowers/outpost-refinement/ack-capability-matrix.md`) named a mechanical paragraph-length
gate as a capability worth considering (a common lint pattern, GENERAL-PRACTICE: the same idea
appears in Vale, proselint, and other prose linters; not something specific to ACK).

Before adding a fixed threshold, the tracked markdown was measured directly with the check's own
paragraph splitter (431 paragraphs across every tracked `.md` file; a paragraph excludes a list
item and its wrapped continuation lines, so a long bulleted list does not inflate the count).
Outside four append-only historical paths (`docs/decisions/`, `docs/DEBT.md`,
`docs/dogfooding.md`, `docs/audit/`), 264 paragraphs remain: the longest is 84 words and the 99th
percentile is 78. Inside those four paths, several ADR Context sections and debt entries run
well past 100 words, because they were written to record a real decision or incident once and
are not meant to be rewritten later.

## Decision

Add `kit/checks/prose_length.py`: a paragraph over 100 words in tracked markdown fails the gate,
except inside `docs/decisions/`, `docs/DEBT.md`, `docs/dogfooding.md`, and `docs/audit/`, whose
own append-only rule (`docs/decisions/README.md`: "append only... never edit or delete a
recorded one") means an old entry cannot be shortened to comply without breaking the record.
100 words was picked from the measurement above: comfortably above every current non-exempt
paragraph (max 84), so the check ships clean with zero grandfathered exceptions, while still
bounding future sprawl. Documented in `docs/writing-standard.md`.

## Alternatives

- A lower ceiling closer to the p95-p99 range (62-78 words). Rejected: would fail several
  existing, already-accepted paragraphs on day one, forcing either an editorial rewrite pass
  unrelated to this change's scope or a temporary grandfather list; 100 admits the real corpus
  cleanly.
- Copy ACK's specific threshold value. Rejected: not evaluated, since no ACK prompt or config
  text was read while designing this check, only the abstract idea that such a gate exists; the
  number here comes from measuring this repo's own tracked markdown.
- Exempt no paths, and edit the historical records to fit. Rejected: `docs/decisions/`'s own rule
  forbids editing a recorded entry, and rewriting the debt or dogfooding ledgers would falsify
  their history.
- A temporary, shrinking exemption list for any paragraph over the ceiling today. Rejected: the
  measurement showed no such list is needed; the four structurally-exempt paths cover every
  outlier.

## Consequences

Sprawl in new or edited prose now fails `python validate.py`, not just a reviewer's read. Nothing
in the current tree needed a rewrite to adopt this. What to watch: the four exempt paths could
become a place to dump prose meant to dodge the ceiling; the check does not distinguish a
genuine append-only entry from an evasive one, so that stays a review-time judgment call.
