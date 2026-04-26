# Action: traverse

Walk the index.md graph starting at a root node, collecting context from all reachable documents. Used at the start of planning to gather full project context.

**Scripts referenced:** `extract.py`, `graph.py`

---

## Behavior

1. Load `.cns/graph.json` (produced by extract.py). If it doesn't exist, run `extract.py` first.
2. Starting from `root` (typically `.cns/index.md` or a specific subdirectory), walk upward and outward through parent edges.
3. For each reachable node, call `read()` to get frontmatter and body.
4. Assemble a context summary: all decisions, human_notes, links, and a synthesis of each node's body.
5. Additionally load `.cns/intent.md` if it exists and append its contents to the context.
6. Check for cycles in the graph (from graph.json). If found, warn in the context summary but continue.
7. Return the assembled context.

---

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `root` | string | Starting path (e.g. `.cns/index.md` or `components/Button/index.md`) |

---

## Output Structure

```json
{
  "nodes": [
    {
      "path": "services/auth/index.md",
      "title": "Auth Service",
      "type": "service",
      "decisions": [...],
      "human_notes": "...",
      "body_summary": "Handles JWT issuance and validation..."
    }
  ],
  "intent_md": "## Upcoming\n- Add OAuth2 refresh token rotation\n- Investigate CRDT approach for concurrent stub editing",
  "edges": [
    { "from": "services/auth/index.md", "to": "backend/index.md", "label": "parent" }
  ],
  "cycles": [],
  "warnings": []
}
```

---

## Cycle Handling

If the graph has a cycle, the agent must avoid infinite loops. During traversal:

1. Track visited node paths in a set.
2. Before following any edge, check if the target is already visited.
3. If a cycle is detected, record it in `warnings` and stop following that branch.

---

## Usage in Planning

`traverse` is called at the start of a planning session. The agent gathers all context before reading any code:

```
traverse(".cns/index.md")
```

This gives the agent:
- Project-level decisions and human notes
- A map of all document nodes and their relationships
- **All planned work** from `.cns/intent.md` — so the agent knows what is already planned or underway before proposing new work
- Any warnings about cycles or orphans

From this, the agent knows where to look for relevant context when planning a feature.

---

## Graph Freshness

`extract.py` runs at agent startup. If new index.md files were created during the session, they won't appear in the current graph until the next startup or next explicit `extract.py` run. The traverse action should note if the graph is stale (>1 hour since `generated` timestamp).
