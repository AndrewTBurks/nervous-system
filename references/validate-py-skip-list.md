# validate.py — skip list maintenance

The `validate.py` script skips `.cns/plans/` directory entirely (line: `if "plans" in rel.parts and ".cns" in rel.parts`). This is correct — plan files are plain-text, not CNS nodes.

A previous version hardcoded three orphan plan filenames to skip:
```
skip_orphan_plans = {
    "task-21-fs-context.md",
    "task-23-data-io-primitives.md",
    "task-24-transform-primitives.md",
}
```
This was removed. The directory-level skip is sufficient — per-file allowlists require manual maintenance and become stale.

**Rule:** If a plan file lacks frontmatter and lives in `.cns/plans/`, it is already skipped. Do not add to a per-file allowlist.