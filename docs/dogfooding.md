---
type: canonical
source: none
sync: none
sla: none
last_updated: 2026-07-26
---

# Dogfooding ledger

Findings from using the kit's own prompts on real work in this repo. Append-only: one row per
finding, gaps and keeps both, so the record stays honest. A finding becomes a prompt revision, a
new check, or a deliberate non-change with a reason.

Note, 2026-07-10: some rows below name prompts that no longer ship. `sync-slack`, `serve-guides`,
`heal-guides`, `guides-watch`, and `export-training-data` left in the v0.23.0 distill (ADR-0009);
`review-change` became `code-review` in v0.25.0 (ADR-0011). Their rows stay verbatim; the ledger
is append-only.

| Date | Prompt | Finding | Revision |
|---|---|---|---|
| 2026-06-30 | implement-change | Produced a CRLF (platform-dependent) build write and nearly used an above-floor API; both caught in review, not at implementation. | Added a portability-and-floors step. |
| 2026-06-30 | plan-change, review-change | A requested change conflicted with the repo's own gate; caught only by repo knowledge. | Added a check against the repo's own gates and rules. |
| 2026-06-30 | review-change | The multi-lens review caught the portability and floor issues; the scrutiny layer works. | Keep, recorded as evidence. |
| 2026-06-30 | implement-change | Live: rebuilding the plugin for the revisions above, `tools/build_plugin.py` wrote CRLF on Windows (`write_text`), the platform-dependent write the new step names. | Fixed: switched it to `write_bytes`, matching `tools/build_templates.py`. |
| 2026-06-30 | sync-slack | Confirmed in chat then sent via `slack_send_message` (immediate send) instead of leaving a `slack_send_message_draft` for the user to send from Slack. Surfaced sending an announcement straight to a self-DM. | Made a Slack draft the default; direct send only on an explicit post-now. |
| 2026-06-30 | serve-guides, heal-guides, guides-watch | Audit: the guides serve path pushed to the live runtime with no confirm-or-draft gate, and the cron watcher acted unattended with no explicit consent model. | Gated the live push (confirm the env and spec count); made scheduling the standing consent, with cross-run issue dedupe and escalate-out-of-scope. |
| 2026-06-30 | export-training-data | Audit: wrote the dataset with no confirm and no overwrite guard, and could pull a held-out run into training. | Confirm the destination and counts; refuse to overwrite a batch; warn and gate on a held-out run. |
| 2026-07-09 | repo-review | First run on this repo: verdict healthy, six minors, all later confirmed. Prompt gaps found: the unknown tag had no home in the output table, no finding ids for triage to key on, the docs-truth pass was unbounded, read-only and output destination were unstated. | Three-value confidence, numbered findings, a docs-truth priority line, read-only and destination named in the inputs. |
| 2026-07-09 | triage | Run on repo-review's six minors: a literal read of step 3 defers every minor, which makes the skill inert on a healthy repo, and the severity breakdown had no named output slot. | The caller's bar decides fix now (severity orders, not gates); the counts line carries the severity breakdown. |
| 2026-07-09 | repo-review, triage | The pair composes: triage confirmed six of six findings and produced a work list that became the next PR. | Keep, recorded as evidence. |
| 2026-07-12 | plan-change | Planning against the real repo ran the kit's own gate and found main already red: the README prompt-pack table carried a header the generator did not emit, so docs_sync drifted. A pre-existing break the spec never saw. | Fixed at the root: the generator now emits the header, matching the committed README byte for byte. Keep, evidence that grounding a plan in the live gate pays for itself. |
| 2026-07-12 | plan-change | The plan assumed the README command table was free to drop, but the command_lists check enforced it (and read when-to-use.md). Repo knowledge, not the spec, surfaced two extra edits before any code. | Widened the plan: retarget command_lists at the workflow hub and drop when-to-use from every check. Keep, recorded as evidence. |
| 2026-07-12 | code-review | The review pass caught doc-truth staleness the plan's file list missed: two catalog check summaries and a contributing.md sentence still named the old doc homes. | Folded the fixes into the retirement step. Keep, the review layer earned its place. |
| 2026-08-06 | repo-hygiene-sweep | A local workspace run reconciled a registry of 53 entries, 38 required, against 41 `.git` directories: 38 canonical active roots, two archived roots, and one nested no-origin invalid candidate. Thirteen required registered paths were absent: 12 origin-matched moves and `mercor`, which was truly absent. Twelve canonical active paths were absent from the catalog's `local_path` set but matched catalog GitHub identities; `workspace-control` was one optional path mismatch. The gate blocked mutation of the dirty catalog authority and every dirty, archived, frozen, or unreadable target. SimCore's unsafe deploy shortcut was verified as a high-severity workflow finding, but unreadable Git state blocked mutation. External editable metadata at `qaplibria.egg-info` broke pytest plugin discovery; disabling third-party plugin autoload produced 260 passing baseline tests. | Keep. Fleet topology reconciliation and mutation gates found work that a one-repo review would not safely route. |
| 2026-08-07 | check-intent | Ran the prompt's own steps against this admitting change's diff, plan: independent prompt contract, independence verification, catalog entry, regenerated docs and plugin spans, admission ADR, dogfood row, contract tests, changelog entry. First pass: every planned item traced Done, but `pytest` then failed three tests (`test_load_prompts_none_returns_all`, `test_converge_ships_to_claude_only`, `test_docs_sync_catches_a_hand_edited_generated_span`) with hardcoded 25/24-prompt counts the plan never named, because the plan listed "contract tests" as one item at too coarse a grain to check the count-bump fallout against. Fixed the tests, then fixed the prompt itself (step 1 now names the grain failure directly: do not fold a downstream fixup into the change's own line); re-ran, second pass clean. | Keep. The gap it found is in its own admitting run, and the fix landed in this same PR rather than deferred: step 1 now says not to fold "and tests for it" or a downstream fixup into one line with the change itself. |
