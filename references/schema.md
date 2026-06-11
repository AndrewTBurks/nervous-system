# CNS Schema Reference

A CNS node is a Markdown file with YAML frontmatter and an agent-authored body.

Required frontmatter:

```yaml
---
title: Architecture
type: module
parent: ../index.md
links: []
decisions: []
human_notes: |
status: clean
last_reconciled: 2026-06-11
---
```

## Human zone

`human_notes` is human-owned. Preserve it exactly unless explicitly instructed otherwise.

## Agent zone

The body below frontmatter is agent-authored and may be reconciled.

## Decisions

Durable decisions live in `decisions[]` with:

- `id`
- `date`
- `author`
- `summary`

Do not keep load-bearing decisions only in body prose.

## Links

`links[].path` is project-root-relative, not relative to the current file.
