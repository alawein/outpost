---
type: derived
source: synthetic eval fixture content, not real project documentation
sync: manual
sla: none
last_updated: 2026-08-08
---

# Debt

Deliberate shortcuts and known limitations, tracked here so they are not silently accrued.

## Open

- 2026-01-01, no rate limiting on get_user. Taken because the app has no external callers yet.
  Revisit when an external API consumer is added.
