# Action: read

Read the index.md at the given path and return both its structured frontmatter and its agent-authored body.

**Scripts referenced:** none (pure file read; no script needed)

---

## Behavior

1. Locate the index.md at `path` (relative to project root).
2. Parse the YAML frontmatter (everything between `---` delimiters).
3. Return frontmatter as a structured dict AND the body (everything after the closing `---`).
4. If the file doesn't exist, return `{not_found: true}`.

---

## Return Value

```json
{
  "not_found": false,
  "frontmatter": {
    "title": "Button Component",
    "type": "component",
    "parent": "ui/button",
    "links": [
      { "id": "auth-token-handling", "path": "services/auth/index.md" }
    ],
    "decisions": [
      {
        "id": "DEC-001",
        "date": "2026-04-25",
        "author": "agent",
        "summary": "Chose JWT over sessions for stateless auth"
      }
    ],
    "human_notes": "The border-radius here is intentional...",
    "status": "clean",
    "last_reconciled": "2026-04-25"
  },
  "body": "This service handles authentication..."
}
```

---

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | string | Path to the index.md file |

---

## Usage in Planning

When the agent begins planning, it calls `read()` on the project root and key index.md files to build context. The frontmatter tells the agent what decisions already exist and what the human has noted. The body tells the agent the current state of the code as understood by the document.

---

## Error Handling

- File not found: return `{not_found: true}`. Don't throw.
- Malformed frontmatter: return `{malformed: true, body: "..."}` with whatever could be parsed.
