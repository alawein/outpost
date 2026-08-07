"""Load and parse the label registry. Stdlib only (JSON)."""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

REGISTRY_PATH = pathlib.Path(__file__).resolve().parent / "registry.json"


@dataclass(frozen=True)
class LabelRegistry:
    labels: list[dict]
    migration: dict[str, list[str]]
    retained_defaults: list[str]

    @property
    def names(self) -> set[str]:
        return {label["name"] for label in self.labels}

    @property
    def known_names(self) -> set[str]:
        """Every label a reference is allowed to name: the registry plus the retained
        GitHub defaults this policy does not migrate away."""
        return self.names | set(self.retained_defaults)

    def family(self, name: str) -> str | None:
        return name.split(":", 1)[0] if ":" in name else None


def load_labels(path: pathlib.Path | None = None) -> LabelRegistry:
    """Parse the label registry. Raises ValueError on a missing or unreadable file, malformed
    JSON, or a missing top-level key, so a broken registry fails at load with one error type."""
    p = path or REGISTRY_PATH
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise ValueError(f"label registry cannot be read: {e}") from e
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"label registry is not valid JSON: {e}") from e
    if not isinstance(doc, dict):
        raise ValueError("label registry must be a JSON object")
    missing = [k for k in ("labels", "migration", "retained_defaults") if k not in doc]
    if missing:
        raise ValueError(f"label registry missing top-level key(s): {missing}")
    return LabelRegistry(
        labels=doc["labels"],
        migration=doc["migration"],
        retained_defaults=doc["retained_defaults"],
    )
