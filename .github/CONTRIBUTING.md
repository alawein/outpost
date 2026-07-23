# Contributing

Thanks for looking at Outpost. The full guide (how the kit is laid out, how to add a prompt,
adapter, or check, and the house voice) lives in [docs/contributing.md](../docs/contributing.md).
This file is the short version GitHub links from issues and pull requests.

## The short version

- A change is done when `python validate.py` and `python -m pytest -q` both pass. CI runs both on
  Linux and Windows.
- The whole kit is standard library only. No third-party imports in the core, the installer, or the
  checks.
- One concern per pull request. Keep the tree runnable at each step, and add a test for a behavior
  change.
- Stage exact paths; do not use a blanket `git add`. Keep secrets and `.env` out of the tree.
- This is a solo repo (see [ADR-0018](../docs/decisions/0018-solo-review-model.md)): an outside pull
  request gets the owner's review before merge.

For security issues, do not open a public issue; see [SECURITY.md](../SECURITY.md).
