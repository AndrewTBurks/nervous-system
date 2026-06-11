# Graph Maintenance

`graph.json` is derived state. Rebuild it after structural CNS changes.

```bash
python3 <skill_dir>/scripts/extract.py <project_root>
python3 <skill_dir>/scripts/graph.py <project_root> --check
```

## Common failures

- Stale node count: run `extract.py`.
- Dangling link: fix `links[].path` relative to project root.
- YAML parse failure: quote values with `:`, `@`, or special characters.
- Orphan: repair parent/link relationship, or document intentional flat-source layout.
