# /nervous-system repair

## Purpose

Fix CNS validation, schema, graph freshness, orphan, cycle, and dangling-link failures.

## Preflight

1. Run `health` and capture exact failures.
2. Read failing files before patching.
3. Determine whether the failure is schema, stale graph, wrong link path, missing parent, orphan node, or invalid YAML.

## Procedure

- Stale graph: run `extract.py`, then `graph.py --check`.
- Invalid YAML: quote strings with `:`, `@`, or other YAML-sensitive characters.
- Dangling link: re-anchor `links[].path` relative to project root.
- Orphan: add/repair parent or nearby code link if the node is valid; delete only with explicit confirmation.
- Oversized node: split along a real conceptual boundary and update `links[]`.

## Verification

Run health again and read back patched files.
