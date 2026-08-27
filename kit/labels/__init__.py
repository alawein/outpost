"""The label registry is the source of truth for GitHub issue and PR labels: one namespaced
family (type, area, priority, status, release), deterministic colors, no deletion
or rename of an existing default. `tools/sync_labels.py` applies it; `kit/checks/label_refs.py`
proves issue forms and labeler config name only registered labels."""
from .loader import LabelRegistry, load_labels

__all__ = ["LabelRegistry", "load_labels"]
