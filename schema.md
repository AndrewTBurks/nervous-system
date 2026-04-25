# Frontmatter Schema Reference

This is a human-readable reference for the frontmatter fields used in nervous-system index.md files. All fields are optional unless noted.

---

## Required Fields

### `title`

**Type:** string  
**Example:** `Button Component`

Human-readable name of the entity this document describes.

---

### `type`

**Type:** enum  
**Values:** `component` | `service` | `module` | `package` | `project`  
**Example:** `component`

Categorizes the type of code unit this document describes.

---

## Optional Fields

### `parent`

**Type:** string (path)  
**Example:** `ui/button`

Path to the parent index.md file. Used to build the bubble chain. If omitted, this document is treated as a root node (but see `.cns/index.md` for project-level root).

---

### `public`

**Type:** boolean  
**Default:** `false`  
**Example:** `true`

Whether this node participates in the bubble chain. Only `public: true` nodes propagate changes upward to their parent.

---

### `links[]`

**Type:** array of objects  
**Example:**
```yaml
links:
  - id: auth-token-handling
    path: services/auth/index.md
  - id: design-system-button
    path: design-system/components/button.md
```

Stable cross-references to other index.md files or external resources. The `id` is a local identifier used to reference this link elsewhere.

---

### `decisions`

**Type:** array of decision objects  
**Example:**
```yaml
decisions:
  - id: DEC-001
    date: 2025-04-10
    author: human
    summary: Chose JWT over sessions for stateless auth
  - id: DEC-002
    date: 2025-04-15
    author: agent
    summary: Refresh token rotation added to auth service
```

A historical record of decisions made about this part of the codebase. Each entry is pruned during reconcile if its premise no longer holds.

**Decision object fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable identifier, e.g. `DEC-001` |
| `date` | string | ISO 8601 date |
| `author` | `human` \| `agent` | Who made the decision |
| `summary` | string | Plain-text description |

---

### `intents[]`

**Type:** array of intent objects  
**Example:**
```yaml
intents:
  - id: INTENT-001
    category: feature
    summary: Add CSV export to workflow results
    status: in_progress
    author: human
    date: 2026-04-20
    links:
      - path: src/engine/index.md
  - id: INTENT-002
    category: exploration
    summary: Investigate using CRDTs for concurrent stub editing
    status: pending
    author: agent
    date: 2026-04-25
```

In-flight work, planned features, research directions, and open questions. Intents are not code — they are the space between what's done and what's envisioned. Each entry is pruned during reconcile if its premise no longer applies or the work is complete.

**Intent object fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable identifier, e.g. `INTENT-001` |
| `category` | enum | One of the 5 categories (see below) |
| `summary` | string | Plain-text description of the intent |
| `status` | enum | `pending` \| `in_progress` \| `completed` \| `cancelled` |
| `author` | `human` \| `agent` | Who recorded the intent |
| `date` | string | ISO 8601 date when recorded |
| `links[]` | array | Optional paths to related index.md files |

**Intent categories:**

| Category | Description |
|----------|-------------|
| `feature` | Planned new capability or user-facing change |
| `refactor` | Planned code restructuring without behavior change |
| `research` | Investigation, spikes, proof-of-concepts |
| `bug` | Known issue being tracked or planned to fix |
| `exploration` | Open-ended idea being explored, not yet committed |
| `thesis` | Dissertation writing — composing chapters, integrating results |

**Status lifecycle:** `pending` → `in_progress` → `completed`. Any stage can move to `cancelled` if the intent is abandoned or superseded.

---

### `human_notes`

**Type:** string (multiline YAML)  
**Example:**
```yaml
human_notes: |
  The border-radius here is intentional — it's 4px to match the design
  system token. Do not change without checking design.md first.

  This component is scheduled for redesign in Q3.
```

**The human's safe zone.** The agent reads this field to understand human intent but never modifies it. Treat this as opaque prose — the agent does not parse or structure the content inside it.

When this field is updated, set `status: dirty` to trigger reconciliation.

---

### `status`

**Type:** enum  
**Default:** `clean`  
**Values:** `clean` | `dirty` | `reconciling`

The reconciliation state of this document.

- `clean`: Document is consistent with code and human intent
- `dirty`: Human intent has changed; agent needs to reconcile
- `reconciling`: Agent is currently working on this document

---

### `last_reconciled`

**Type:** string (ISO date)  
**Example:** `2025-04-25`

ISO 8601 date of the last time reconciliation completed for this document.

---

## Complete Example

```yaml
---
title: Auth Service
type: service
parent: backend/index.md
public: true
links:
  - id: session-design
    path: services/sessions/index.md
decisions:
  - id: DEC-001
    date: 2025-04-10
    author: human
    summary: Chose JWT over sessions for stateless auth
  - id: DEC-002
    date: 2025-04-15
    author: agent
    summary: Refresh token rotation added
human_notes: |
  We agreed to revisit the token expiry policy after the beta launch.
  Do not extend expiry beyond 24h without checking with the security team.
status: clean
last_reconciled: 2025-04-25
---

This service handles authentication for the application. It exposes a
REST API consumed by the frontend and issues JWTs on successful login.
Token validation is stateless — the service verifies signatures locally
without querying the database.
```

---

## Field Summary Table

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `title` | string | yes | — |
| `type` | enum | yes | — |
| `parent` | string | no | null |
| `public` | boolean | no | false |
| `links` | array | no | [] |
| `decisions` | array | no | [] |
| `intents` | array | no | [] |
| `human_notes` | string | no | "" |
| `status` | enum | no | clean |
| `last_reconciled` | string | no | null |
