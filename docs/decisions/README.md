# Decisions

Architecture decision records for the kit. Each one records a decision, why it was made, and the options considered. They are numbered `NNNN-title.md` and append only. Supersede an old record with a new one; never edit or delete a recorded one.

Start from `0000-template.md` when adding a record.

- 0001: repo architecture and the first release scope.
- 0002: scrutiny prompts, a third prompt group.
- 0003: team tailoring by prompt subset (`--only`/`--exclude` and an install manifest).
- 0004: package the kit as an added Claude Code plugin channel, generated from the catalog.
- 0005: domain-group engine, Claude-only prompt packs (eval, guides, ops, device), opt-in with `--with-domain`.
- 0006: require a maintainer review on the kit's own repo (CODEOWNERS and branch protection), reversing the no-CODEOWNERS rule for this repo only. Superseded by 0018.
- 0007: kit identity, lead with the tool-neutral core and wall off the Claude-only domain packs as a team extension (Option C).
- 0008: eval front door, `kit.eval` as a quarantined leaf that reverses ADR-0001's "No eval, no judge" scope.
- 0009: distill to a pure coding kit, remove the eval, guides, device, and ops domains and return the core to 21 cross-tool skills (supersedes 0005 and 0008).
- 0010: the kit is ACK, one name for the plugin, the installer state dir, and the distribution (extends 0007).
- 0011: the review suite, three new core prompts and a five-command review suite under `/ack:*` (widens 0002).
- 0012: no personal trace in the tracked tree, enforced by the `traces` check; the allowed homes are CODEOWNERS, the append-only records, and the check's own pattern list.
- 0013: prompt admission, an entry test for prompt 26 and beyond (distinct job, nearest sibling, unsafe default, binding mechanism, dogfood case, deletion condition). Accepted 2026-08-07 (originally proposed 2026-07-11), on the evidence of two admissions (0020, 0023) already following it. Superseded by 0025.
- 0014: pack consolidation after the Phase 1 audit; seven owner rulings, two kept-pair negatives, `deassume` folded into `repo-review`, `converge` made Claude-only, `prove`, `panel`, and `write-doc` rewritten.
- 0015: keep the prompt and plugin-skill copies; the plugin format mandates the nested skills tree, so the flat authored `prompts/core` stays the source and the mirror stays generated.
- 0016: retire two dead installer paths (the `.agi-coding-kit` manifest migration and the v0.24 Cursor rename sweep); keep the records-less ownership fallback, which review showed is load-bearing for correctness.
- 0017: the kit is Outpost, forking the internal ACK kit into a personal MIT-licensed open source
  project (supersedes 0010).
- 0018: solo review model, the owner reviews outside PRs and merges own PRs on green CI without a
  second approval (supersedes 0006).
- 0019: installer path-safety (manifest keys must be project-relative) and the v0.2 refinement
  decisions, including the rejected byte-match ownership fix kept as a negative.
- 0020: admit `repo-hygiene-sweep` for ordered fleet review and gated cleanup.
- 0021: `docs/adr/` is a compliance stub for the alawein doctrine gate; `docs/decisions/` stays
  the one real ADR ledger.
- 0022: namespaced label governance (`type`, `area`, `priority`, `status`, `release`,
  `provenance`), migrating from the GitHub defaults without deleting them.
- 0023: admit `check-intent`, a structured plan-to-diff reconciliation before `code-review`.
- 0024: a mechanical 100-word paragraph-length ceiling (`prose_length`), exempt for the
  append-only historical records.
- 0025: relax prompt admission to three required fields (distinct job, nearest sibling, unsafe
  default) and three recommended, non-blocking ones (binding mechanism, dogfood case, deletion
  condition). Supersedes 0013.
- 0026: a lightweight behavioral eval for core prompts, mechanical assertions via `claude -p`,
  opt-in and not CI-gated. Piloted 5 at admission (interrogate, plan-change, record-decision,
  write-tests, debt-log); `docs/DEBT.md`'s open entry names the current pilot count and list, so
  this index is not itself a second place that count can drift.
- 0027: admit `risk-review`, a second-gear review composing `code-review`'s structural pass with
  `grill`'s claim-attack, gated to install/adapter write paths or anything named hard to reverse.
- 0028: fix a manifest-driven symlink escape in `prune`/`remove` (a crafted manifest plus a
  pre-planted symlink could delete a file outside the project root); `unmerge_kit_settings` gets
  the same never-installed-tool guard `remove_for_tools` already proved.
- 0029: cross-doc-check, comparing two named docs that are each supposed to state the same policy
  and flagging a real contradiction or unexplained scope gap, never a wording difference.
- 0030: fix a dangling-symlink install-time write (a pre-planted symlink at a plan-derived write
  path could crash install.py or write kit content outside the project); closes a related delete-
  side question ADR-0028 left open, with reasoning rather than code.
