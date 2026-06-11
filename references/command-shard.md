# /nervous-system shard

## Purpose

Distribute resolved decisions from a plan file or completed intent section into the durable CNS graph and module-level `index.md` files.

## Preflight

1. Run common preflight.
2. Read the source file in full.
3. Identify target CNS nodes and read each immediately before writing.
4. Check target line counts. Split nodes that approach roughly 350 lines.
5. Confirm whether deleting the source plan file is allowed in this session.

## Procedure

1. Map each resolved decision to its owning node.
2. Write durable decisions into frontmatter `decisions[]`.
3. Keep body prose focused on current state, boundaries, and implementation notes.
4. Remove stale pre-shard or plan-only wording from target nodes.
5. Bubble each modified node upward.
6. Rebuild graph with `extract.py`.
7. Run `validate.py` and `graph.py --check`.
8. If confirmed, delete source plan files that are fully sharded. Never delete completed intent entries.
9. Append a compact log entry.

## Verification

- Source decisions are represented in target nodes.
- No duplicate source of truth remains in body prose.
- Health passes.
