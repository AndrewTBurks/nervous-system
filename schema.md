# Schema & Reference

Human-readable reference for frontmatter, graph structure, validation, and propagation rules.

---

## Frontmatter Fields

### Required

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Human-readable name |
| `type` | enum | `component` \| `service` \| `module` \| `package` \| `project` |

### Optional

| Field | Type | Description |
|-------|------|-------------|
| `parent` | string (path) | Parent index.md for bubble chain |
| `links[]` | array | Cross-references to other nodes |
| `decisions[]` | array | Decision history (see below) |
|| `human_notes` | string | **Human intent provenance** — agent reads, may append, never rewrites or removes |
| `status` | enum | `clean` \| `dirty` \| `reconciling` |
| `last_reconciled` | string (ISO date) | Last reconcile completion |

### decisions[] format

```yaml
decisions:
  - id: DEC-001
    date: 2025-04-10
    author: human
    summary: Chose JWT over sessions for stateless auth
```

| Field | Description |
|-------|-------------|
| `id` | Stable identifier, e.g. `DEC-001` |
| `date` | ISO 8601 date |
| `author` | `human` or `agent` |
| `summary` | Plain-text description |

### Complete example

```yaml
---
title: Auth Service
type: service
parent: backend/index.md
links:
  - id: session-design
    path: services/sessions/index.md
decisions:
  - id: DEC-001
    date: 2025-04-10
    author: human
    summary: Chose JWT over sessions for stateless auth
human_notes: |
  We agreed to revisit the token expiry policy after the beta launch.
status: clean
last_reconciled: 2025-04-25
---

This service handles authentication for the application.
```

---

## Status Lifecycle

```
clean ─────▶ dirty ─────▶ reconciling ─────▶ clean
     (human edits)    (agent working)    (done)
```

The agent detects when a document's `human_notes` or agent-authored body has changed relative to its last known state. The `status: dirty` field may also be set explicitly if needed.

---

## Propagation Rules

The bubble always proceeds all the way to `.cns/index.md`. What changes at each level depends on external relevance:

| Change type | What happens |
|-------------|--------------|
| Public API change | Bubbles; significant decisions absorbed by parent |
| Significant decision | Bubbles; absorbed by parent |
| Minor detail | Stays local; parent's agent body not updated |

---

## Pruning Rules

During reconcile, each `decisions[]` entry is checked: does the current code still reflect this decision? If not, it is removed. Stale decisions are noise — they are deleted, not archived.

---

## Bubble Consistency Rule

After every write to an index.md, the agent checks: is the parent layer still consistent with this layer? If this layer changed something externally relevant (a public API, a significant decision), the agent synthesizes a 1–3 sentence summary and inserts it into the parent's agent-authored body. This cascades to `.cns/index.md`. Use `bubble.py` to analyze the chain before deciding what to write.

---

## graph.json Format

```json
{
  "generated": "2026-04-25T14:30:00Z",
  "nodes": [
    { "path": "components/Button/index.md", "title": "Button Component", "type": "component" }
  ],
  "edges": [
    { "from": "components/Button/index.md", "to": "ui/button/index.md", "label": "parent" }
  ],
  "orphans": [],
  "cycles": [],
  "dangling_links": []
}
```

Run `scripts/extract.py` to build `.cns/graph.json` from the directory tree. Re-run after any structural change (adding/removing nodes, updating links).

---

## log.md Format

```markdown
## 2026-04-25

### 14:30 — reconcile
- components/Button/index.md: reconciled, status -> clean
- bubbled to ui/button/index.md
- pruned: DEC-003 (feature removed)

### 14:25 — capture
- services/auth/index.md: added DEC-007 (author: agent)

### 14:20 — shard
- plan: task-17-spatial-provenance.md
- sharded into 3 index.md files
```

---

## Validation

After any CNS write, run:

```bash
python3 ~/.hermes/skills/nervous-system/scripts/validate.py /path/to/project
python3 ~/.hermes/skills/nervous-system/scripts/graph.py /path/to/project --check
```

Exit code 0 = pass, 1 = fail.

The validator checks:
1. Valid YAML frontmatter (`---` delimited) in every `.cns/*.md` file
2. Required fields: `title`, `type`
3. Each `decisions[]` entry has `id:`, `date:`, `author:`, `summary:`
4. No duplicate decision IDs within a file
5. All `links[]` paths point to existing files

---

## Field Summary Table

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `title` | string | yes | — |
| `type` | enum | yes | — |
| `parent` | string | no | null |
| `links` | array | no | [] |
| `decisions` | array | no | [] |
| `human_notes` | string | no | "" |
| `status` | enum | no | clean |
| `last_reconciled` | string | no | null |