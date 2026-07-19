# 0010: The kit is ACK

Date: 2026-07-09. Status: accepted. Extends ADR-0007 (kit identity).

## Context

The GitHub repo was renamed to agi-inc/ACK. The tree still said agi-coding-kit in the plugin
name, the installer state dir, the package name, and the docs. Two names for one thing.

## Decision

One name: ACK (AGI's Coding Kit). The plugin is `plugins/ack/`, so every command surfaces as
`/ack:*`. The installer state dir is `.ack/`; an install over the old `.agi-coding-kit/` dir
migrates the manifest and removes the old dir when it is then empty. The distribution name is `ack`. The Python
package stays `kit`: internal plumbing, invisible to users, and renaming it churns every
import for no reader benefit.

## Consequences

- Docs and templates say ACK; `agi-coding-kit` survives only in CHANGELOG and ADR history and
  in the migration constant.
- Installed projects migrate their state dir on the next install touch; nothing breaks before
  that because reads fall back to the legacy path.
- The old GitHub URL redirects, so existing clones keep working; new clones use agi-inc/ACK.
