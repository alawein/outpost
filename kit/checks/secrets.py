"""No tracked private key or AWS access key, no junk. Two rules the kit must hold to itself:

- `.gitignore` excludes `.env`, and no `.env`, private key, or AWS access key is tracked.
- No build cache, log, or generated junk is tracked.

The content scan is a narrow, two-pattern allowlist (a PEM-style private key block, an AWS access
key id), not a general secret scanner: a GitHub token, a Slack token, or a plain `API_KEY=...`
value passes green. Within that scope it reads every text file regardless of extension, so a key
in `key.pem` or an extensionless `id_rsa` is caught, not just one in a known suffix. It prefers
`git ls-files` to judge what is committed; when git is unavailable it walks the working tree
(minus the ignore set) so the scan still runs instead of silently skipping.
"""
from __future__ import annotations

import pathlib
import re

from . import scan_candidates

SECRET_PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
]
JUNK = ("__pycache__/", ".pytest_cache/", ".DS_Store", ".egg-info/", ".superpowers/")
JUNK_SUFFIX = (".pyc", ".log", ".tmp")
SELF = "kit/checks/secrets.py"


def run(root: pathlib.Path) -> tuple[bool, str]:
    errors: list[str] = []

    gi = root / ".gitignore"
    if not gi.is_file() or ".env" not in gi.read_text(encoding="utf-8"):
        errors.append(".gitignore does not exclude .env")

    files, from_git = scan_candidates(root)
    for rel in files:
        if rel == ".env" or rel.startswith(".env."):
            errors.append(f"{rel}: an env file is tracked")
        if any(j in rel for j in JUNK) or rel.endswith(JUNK_SUFFIX):
            errors.append(f"{rel}: junk should not be tracked")
        if rel == SELF:
            continue  # the patterns live here by design
        try:
            raw = (root / rel).read_bytes()
        except OSError as e:
            # fail closed: a file we cannot read is unverifiable, not clean
            errors.append(f"{rel}: unreadable, cannot verify ({e})")
            continue
        # decode latin-1 (1:1, never raises) so a key in a non-UTF-8 file is still scanned
        text = raw.decode("latin-1")
        for label, rx in SECRET_PATTERNS:
            if rx.search(text):
                errors.append(f"{rel}: looks like a {label}")

    if errors:
        return False, "; ".join(errors[:10])
    source = "tracked" if from_git else "working-tree (no git)"
    return True, f"{len(files)} {source} files clean: no private keys or AWS keys, no junk"
