# Decisions

A record here explains a choice a future maintainer would otherwise have to reverse-engineer:
what was decided, why, and what was given up. Write one only when at least two hold: the
choice crosses a boundary (a tool, a consumer, a repo); reversing it is costly or
security-sensitive; a future maintainer will need the rationale; it sets ownership, a
contract, or a durable exception. A prompt addition never qualifies on its own.

Records are numbered `NNNN-title.md`, written from `0000-template.md`, and append-only:
supersede an old record with a new one, never edit or delete a recorded one. The one exception
is errata: a citation that was wrong when written, or a named check or test that has since
moved, may be corrected in place. The decision itself is never rewritten.

Index bullets are `- NNNN: title`. No other bullet in this file starts with a bare four-digit
number (a year, say); the ledgers check reads any such bullet as an index entry.

- 0001: solo review model
- 0002: installer path safety
