---
name: panel
description: Use when a decision or design benefits from several independent expert perspectives. Convenes distinct expert lenses that each judge the decision on its own, then synthesizes agreements, disagreements, and one recommendation. Distinct from prove and grill.
---

# panel

`prove` checks numbers by recomputing each from the source of truth. `grill` sends a single attacker after a claim. `panel` runs several expert views, each judging the same decision independently. It then states what they agree on, where they truly conflict, and one recommendation.

Use it when no single perspective sees the full picture.

## When to use it

- A design, architecture, or risky call that needs several disciplines.
- A decision where a conflict between views (security vs. speed, user need vs. maintainability) is the real finding, not noise to smooth over.
- Skip it when a single correctness check or an adversarial test covers the question.

## Required inputs

- The decision, design, or artifact to assess.
- Optional: preferred views; otherwise this prompt selects 3 to 5 that fit. Common choices: correctness, security, performance, maintainability, user, skeptic.
- Any spec, constraints, or context a view needs to judge fairly.

## Steps

1. Name the views before assessing. Commit to 3 to 5 that match the decision.
2. Run the views. Each judges from its own perspective only: what it accepts, what concerns it,
   and what would change its verdict. On a host that can run subagents, run the views in
   parallel so no view can see another. Otherwise run them in sequence and write each view's
   full take before reading the previous ones back; that states the independence intent
   honestly, but a later view may still anchor on an earlier one, so the report says which mode
   ran.
3. Map agreements and conflicts. Where views align, note it. Where they truly conflict, name the trade-off. A real conflict is the signal, not noise to average away.
4. Synthesize. Write one recommendation that names the trade-off it accepts, which view it overrides, and why. Do not split the difference to paper over a conflict.
5. Report. One line per view, then the conflict map, then the recommendation.

## Output format

- Views: the set chosen, one line each naming the perspective, and the mode the views ran in
  (parallel or sequential), so the reader knows how independent they were.
- Takes: per view, one line covering what it accepts, what concerns it, and its verdict.
- Conflicts: the genuine disagreements, one per line, naming the two views and the trade-off.
- Recommendation: one line. Names the decision, the trade-off accepted, and the view overridden.

## Stop conditions

- Keep the views independent. Parallel where the host supports it; in sequence, write each view
  before reading the others back, and name the mode in the report. Independence is the point,
  and the sequential form is an intent, not a proof.
- A conflict is a finding, not a problem to resolve by averaging. Name it.
- This is read-only. Do not implement the decision; hand it to the relevant build prompt.
- Stop at one recommendation. Do not hedge by listing alternatives as equals.
