---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-07-26
---

# Writing standard

How the kit writes prose: prompts, docs, comments, commits, PRs. Write so a reader sees the point first and never has to trust assertion alone.

## The rules

- Lead with the answer. State the conclusion, then the support. Cut preamble and restatement.
- Short, declarative sentences. One idea each. American spelling.
- No em-dashes or en-dashes. Use a comma, a period, a colon, or parentheses.
- Plain ASCII. Use `-` for lists. No emoji, no unicode glyphs.
- Concrete nouns and verbs. Cut slogans, vague claims, and internal shorthand.
- Hedge real uncertainty in a short clause. Do not hedge settled facts.
- Tables for state, prose for reasoning.

## Preserve when you trim

Concision cuts words, never relationships. When you shorten or condense, keep the grammar that carries the meaning, not just the nouns:

- Polarity and modality: "never run", "must not", "may". Keep the negation and the strength.
- Scope and binding: which command, which environment, which case a claim attaches to.
- Conditions and exceptions: the "if", the "unless", the "except".
- Order and units: sequence when it matters, and every number with its unit.
- Attribution and evidence: who said it, and what proves it.
- Table cells: a value keeps its row and column. Do not flatten a grid into a list that loses which value belongs to which key.

If a passage is operational, conditional, tabular, or a safety or verification instruction, do not compress its structure. Merge filler, not the grammar. When in doubt, keep the longer form.

## Paragraph length

Lead with the answer (above) keeps most paragraphs well under this on its own. The
`prose_length` check enforces a mechanical ceiling of 100 words on a narrative paragraph in the
kit's markdown, so sprawl fails the gate instead of resting on editorial judgment alone. It
measures prose only: a heading, a list item (wrapped or not), a table row, a blockquote, and a
fenced code block are not paragraphs and stay unmeasured. Exempt entirely: the append-only
historical records (`docs/decisions/`, `docs/DEBT.md`, `docs/dogfooding.md`, `docs/audit/`),
where an old entry cannot be rewritten to comply without breaking the record's own append-only
rule.

## Banned register

Do not use these words. If one is the first word that comes, rewrite the sentence, do not swap the word: comprehensive, robust, leverage, streamline, seamless, delve, holistic, cutting-edge, powerful, moreover, furthermore, utilize.

The `voice` check enforces this list across the kit's markdown (this file is exempt, since it names the words to ban them), and enforces plain ASCII everywhere, with em and en-dashes called out by name.

## For public docs

- Open with one sentence saying what the thing is and who it helps.
- Put install and a short working example before architecture or theory.
- Write for the next reader action: install, run, inspect, extend, debug, or release.
- Show the next useful layer first. Link to deeper detail instead of front-loading it.
- Preserve real content when simplifying: merge before deleting.
- Cite evidence a reader can actually check. A gitignored scratch path (`.superpowers/`,
  `docs/superpowers/`) is not a source; state the finding directly instead of pointing at
  something unreachable. Naming the scratch convention itself (what it is, that a design lived
  there before this record) is fine; citing its content as proof of a claim is not.

## Sources

GitHub README guidance, the Diataxis documentation framework, the Nielsen Norman Group on progressive disclosure, and the plain-language guidelines at plainlanguage.gov.
