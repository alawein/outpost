"""Load and parse the catalog. Stdlib only (JSON), so a clean clone runs with just Python."""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

CATALOG_PATH = pathlib.Path(__file__).resolve().parent / "catalog.json"


@dataclass(frozen=True)
class Catalog:
    version: str
    stages: list[dict]
    prompts: list[dict]
    templates: list[dict]
    adapters: list[dict]
    checks: list[dict]

    @property
    def prompt_paths(self) -> set[str]:
        return {p["path"] for p in self.prompts}

    @property
    def template_paths(self) -> set[str]:
        return {t["path"] for t in self.templates}

    def prompts_for(self, tool: str) -> list[dict]:
        """The prompts that ship to one tool. A prompt entry with a `hosts` list ships only to
        those tools (decision 0014 limits `converge` to Claude); an entry without one ships
        everywhere."""
        return [p for p in self.prompts if not p.get("hosts") or tool in p["hosts"]]


def load_catalog(path: pathlib.Path | None = None) -> Catalog:
    """Parse the catalog file. Raises ValueError on a missing or unreadable file, malformed JSON, or
    a missing top-level key, so a broken catalog fails at load with one error type instead of midway
    through a check."""
    p = path or CATALOG_PATH
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise ValueError(f"catalog cannot be read: {e}") from e
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"catalog is not valid JSON: {e}") from e
    if not isinstance(doc, dict):
        raise ValueError("catalog must be a JSON object")
    missing = [k for k in ("version", "stages", "prompts", "templates", "adapters", "checks")
               if k not in doc]
    if missing:
        raise ValueError(f"catalog missing top-level key(s): {missing}")
    return Catalog(
        version=doc["version"],
        stages=doc["stages"],
        prompts=doc["prompts"],
        templates=doc["templates"],
        adapters=doc["adapters"],
        checks=doc["checks"],
    )
