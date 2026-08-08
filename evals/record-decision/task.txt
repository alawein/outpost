Use the record-decision skill to record this decision: we chose to cache get_user results in
memory with no TTL, instead of adding a Redis dependency, because the app runs single-process and
memory pressure has never been an issue. Alternative considered: Redis, rejected because it adds
an external service dependency for a problem the app does not have yet.
