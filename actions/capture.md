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
public: true
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

---

# Action: capture_intent

Add an intent entry to `.cns/intents/index.md`. This is the single canonical location for all in-flight work across the project.

---

## Behavior

1. Ensure `.cns/intents/index.md` exists. If not, create it with `type: intents_root`.
2. Parse existing frontmatter.
3. Generate a new intent ID: find the highest `INTENT-###` in existing intents, increment.
4. Validate `category` is one of: `feature`, `refactor`, `research`, `bug`, `exploration`.
5. Validate `status` is one of: `pending`, `in_progress`, `completed`, `cancelled`.
6. Create an intent entry:
   ```yaml
   - id: INTENT-003
     category: feature
     summary: Add CSV export to workflow results
     status: in_progress
     author: agent
     date: 2026-04-25
     links:
       - path: src/engine/index.md
   ```
7. Append to the `intents[]` array. Initialize `intents: []` if not present.
8. Log the capture to `.cns/log.md`.

---

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | One of: `feature`, `refactor`, `research`, `bug`, `exploration` |
| `summary` | string | Plain-text description of the intent |
| `status` | string | One of: `pending` (default), `in_progress`, `completed`, `cancelled` |
| `author` | string | `human` or `agent` (default: `agent`) |
| `links` | array | Optional list of paths to related index.md files |

---

## Examples

**Record a planned feature:**
```
capture_intent("feature", "Add CSV export to workflow results", status="pending")
```

**Record an active research spike:**
```
capture_intent("research", "Investigate CRDT approach for concurrent stub editing", status="in_progress", links=["src/engine/index.md"])
```

**Record a known bug:**
```
capture_intent("bug", "Stub lifecycle cleanup missing on session teardown", status="pending", author="human", links=["src/engine/index.md"])
```

**Record an open-ended exploration:**
```
capture_intent("exploration", "Evaluate temporal provenance visualization for large display")
```

---

## Updating Intent Status

When work on an intent starts, moves forward, or completes, call `capture_intent` again with the same `category` and `summary` to update `status`. The agent will locate the existing entry by `id` and update it in place rather than adding a duplicate.
