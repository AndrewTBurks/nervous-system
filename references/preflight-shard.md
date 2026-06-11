# Shard Preflight

- Read source plan or intent section in full.
- Identify durable target nodes.
- Read every target immediately before writing.
- Check target line counts; split around 350 lines when needed.
- Confirm source plan deletion before deleting. Completed intent entries are never deleted.
