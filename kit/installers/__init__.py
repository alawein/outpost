"""Safe, idempotent config merges. The settings merge is the only place the installer touches a
file a user also owns, so it merges instead of overwriting and rejects a malformed file cleanly."""
