# 0019: Installer path-safety and the v0.2 refinement

Status: Accepted
Date: 2026-07-23

## Context

Before Outpost got wider visibility, a red-team pass (three review lanes over the code, docs, and
prompt pack, plus adversarial grills) checked the kit for correctness, security, and coherence. It
found the kit fundamentally healthy but surfaced a set of issues that shipped as v0.2.0 and v0.2.1.
This record captures the decisions worth keeping, especially a security invariant and one rejected
fix, so later work does not relitigate them. It does not restate the changelog; see `[0.2.0]` and
`[0.2.1]` in `CHANGELOG.md` for the full list.

The working design spec lived in local scratch (`docs/superpowers/`, gitignored); this ADR is its
permanent form.

## Decision

1. **Manifest keys are project-relative POSIX paths, enforced at parse time.** `parse_manifest`
   rejects any `files` key that is absolute, contains parent traversal, or carries a Windows anchor:
   a backslash, a colon (a drive letter anywhere in the path, or an NTFS alternate-data-stream), or
   a null byte. The installer joins these keys to the project root and unlinks them in `--prune` and
   `--remove`, so a crafted `.outpost/manifest.json` in a cloned repo could otherwise delete a file
   outside the project. The escape is Windows-specific: `pathlib` re-anchors on a backslash or an
   embedded drive letter that a POSIX-only check treats as an ordinary character.

2. **The guard is validation, not the last line of defense.** The current delete sites gate on
   `(project_root / key).is_file()`, which incidentally rejects the malformed joined path today. If
   a sink is ever changed to `resolve()` the target before the existence check, it must also assert
   the resolved path is within the project root. This is the standing follow-up, not yet needed.

3. **Three gate checks added** (`plugin_orphans`, `banned_sync`, and a wider `doc_truth` that
   resolves prompt references across the instruction docs). `doc_truth` derives the valid non-prompt
   names (a plugin agent, an output style) from the plugin tree rather than a hardcoded allowlist,
   so a new component never needs a guard edit.

4. **`split-change` and the `/outpost:ship` command are draft-only.** The agent drafts the split or
   the PR; staging, committing, and opening the PR stay human actions, extending the prior
   draft-only hardening (#114) across the whole pack.

The solo review model is recorded separately in ADR-0018 and is not restated here.

## Alternatives

Kept in the record so no one re-proposes them.

- **Byte-match ownership on a partial install (rejected).** A crashed install leaves kit files on
  disk with no manifest; a proposed fix byte-compared them to the kit's output and claimed kit
  ownership on a match, so a later `--remove` would reclaim them. Rejected: it breaks the tested
  invariant that matching bytes alone never prove kit ownership (`test_remove_keeps_a_preexisting_*`),
  which deliberately preserves a user's byte-identical file. With no manifest there is no proof of
  authorship, so preserving the user's data is correct; the "freeze" (crashed-install files treated
  as user-owned) is the safe side of that ambiguity. Implementing the fix would trade a benign
  freeze for real data loss.

- **Validating the manifest hash fields (dropped).** Checking that `kit_hash`/`pre_hash` are
  well-formed was considered and dropped: the field is a forensic trace, not a decision input, and
  the path-key check alone closes the traversal vector.

- **Widening `doc_truth` to every doc with an allowlist (rejected).** Live docs (the ROADMAP
  backlog, the append-only ledgers) legitimately name retired prompts in prose, so a blanket scan
  needs an allowlist, the maintenance burden the earlier single-word-ref work rejected. Scoping the
  scan to the instruction docs with tree-derived component names avoids it.

## Consequences

- Easier: the traversal class is closed at the parse boundary and confirmed by three grill passes;
  the new checks catch drift the gate previously missed; the pack's git-safety rule holds
  everywhere.
- Harder: nothing; the path-safety guard has no effect on legitimate `/`-joined kit keys.
- Watch: if a delete sink starts resolving targets before the existence check, add the
  resolve-within-root assertion (decision 2). Reverse the draft-only prompt stance only with a new
  decision, since it is a prompt-contract change callers may rely on.
