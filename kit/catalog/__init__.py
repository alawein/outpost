"""The catalog is the source of truth for what the kit ships: prompts, templates, adapters, and
checks. The checks validate the repo against it, so drift fails loudly instead of rotting."""
from .loader import Catalog, load_catalog

__all__ = ["Catalog", "load_catalog"]
