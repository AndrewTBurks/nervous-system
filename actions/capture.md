# Action: capture

Append a decision to the `decisions[]` array in the index.md at the given path. Used when a decision is made during work that should be recorded.

---

## Behavior

1. Locate the index.md at `path` (relative to project root). If it doesn't exist, create it with a minimal frontmatter scaffold.
2. Parse existing frontmatter.
3. Generate a new decision ID: find the highest `DEC-###` in existing decisions, increment.
4. Create a decision entry:
   ```yaml
   - id: DEC-009
     date: 2026-04-25
     author: agent
     summary: <content>
   ```
5. Append to the `decisions[]` array in frontmatter. Initialize `decisions: []` if not present.
6. Set `status: dirty` briefly, then write. After write completes, set `status: clean`.
7. Log the capture to `.cns/log.md`.

---

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | string | Path to the index.md file (e.g. `services/auth/index.md`) |
| `content` | string | Decision summary text to record |

---

## Examples

**Simple decision capture:**
```
capture("services/auth/index.md", "Chose JWT over sessions for stateless auth")
```

Result in frontmatter:
```yaml
decisions:
  - id: DEC-001
    date: 2026-04-25
    author: agent
    summary: Chose JWT over sessions for stateless auth
```

**Capture with human author:**
```
capture("components/Button/index.md", "Set border-radius to 4px to match design system token", author="human")
```

The `author` field defaults to `agent`. Pass `author="human"` if the human explicitly made or approved the decision.

---

## Creating a New index.md

If no index.md exists at `path`, create one:

```yaml
---
title: Auth Service        # derived from directory name
type: service
decisions: []
status: clean
---
```

Agent-authored body is left empty initially — it gets populated on first reconcile or shard.

---

## Error Handling

- If the parent directory doesn't exist, create it first.
- If the path points outside the project, refuse with an error.
- If frontmatter is malformed, log a warning and attempt to parse what's there; don't fail silently.
