#!/usr/bin/env python3
"""The kit gate. A change is done when this is green from the repo root, not when it produces a
diff. CI runs this plus pytest. Stdlib only.

The checks live in `kit/checks/`, driven by the catalog. This file is a thin entry point so the
gate has one obvious command: `python validate.py`.
"""
from __future__ import annotations

import pathlib

from kit.checks.run import main

if __name__ == "__main__":
    raise SystemExit(main(pathlib.Path(__file__).resolve().parent))
