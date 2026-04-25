# Action: audit

Audit a CNS node and its adjacent nodes against the actual codebase. Detects stale docs, broken links, undocumented code, and decisions that have drifted from implementation.

---

## Behavior

Audit runs in three phases:

### Phase 1 — Gather

1. Load `.cns/graph.json`.
2. Load the starting node's frontmatter and body.
3. Find all adjacent nodes:
   - **Parent** (via `parent` field in frontmatter)
   - **Children** (nodes that list this node as their parent)
   - **Linked nodes** (via `links[]` field in frontmatter)
4. For each adjacent node, load its frontmatter and body.

### Phase 2 — Audit

For the starting node and each adjacent node, run these checks:

**Code existence checks:**
- Each `links[]` path → does the file actually exist at that path?
- Each `decisions[].implemented` field → is the implementation present in the code?
- Are there code files/functions/classes in the filesystem that are not mentioned in any linked doc?

**Semantic drift checks:**
- If the doc describes a function/class/module name, does it still exist in code?
- If a `status: deprecated` decision is listed, is the deprecated code actually still there?
- If a `decisions[]` item says "implemented: true", does the code compile/run?

**Coverage checks:**
- For each subdirectory or module represented by a child node, is there a corresponding code directory?
- Are there code directories with no CNS node at all?

### Phase 3 — Report

Return a structured audit report:

```json
{
  "node": ".cns/architecture/index.md",
  "adjoining_nodes": [".cns/index.md", ".cns/design/index.md"],
  "findings": [
    {
      "severity": "broken_link",
      "node": ".cns/architecture/index.md",
      "detail": "links[] references 'src/auth/token.ts' but file does not exist",
      "link": "src/auth/token.ts"
    },
    {
      "severity": "stale",
      "node": ".cns/architecture/index.md",
      "detail": "describes 'AuthService.refresh()' but method no longer exists in src/auth/Service.ts"
    },
    {
      "severity": "unimplemented",
      "node": ".cns/design/index.md",
      "detail": "DEC-003 says 'implemented: true' but src/billing/ is empty"
    },
    {
      "severity": "undocumented",
      "node": ".cns/architecture/index.md",
      "detail": "src/scheduler/ exists but has no linked CNS node"
    }
  ],
  "summary": {
    "total": 4,
    "broken_link": 1,
    "stale": 1,
    "unimplemented": 1,
    "undocumented": 1
  }
}
```

**Severity levels:**
- `broken_link` — a path in `links[]` does not resolve to an existing file
- `stale` — the doc describes something that no longer matches the code
- `unimplemented` — a decision claims implementation but code is missing
- `undocumented` — code exists with no corresponding CNS node

---

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | string | Path to the starting CNS index.md node |
| `depth` | int | How many parent/child levels to traverse (default: 1, max: 3) |

---

## Usage

```
audit(".cns/architecture/index.md")
audit("components/Button/index.md", depth=2)
```

**When to run audit:**
- Before a major release to verify docs match code
- When investigating a bug and suspect docs may be misleading
- During reconciliation if the agent detects a mismatch
- When adopting an unfamiliar part of the codebase

---

## What Audit Is Not

- Audit does NOT modify files — it only reads and reports.
- Audit does NOT check frontmatter schema (use `validate` for that).
- Audit does NOT reconcile human edits (use `reconcile` for that).
- Audit does NOT check graph integrity (use `graph --check` for that).

Audit is purely a doc-to-reality consistency checker.

---

## Error Handling

- Node not found: error, abort
- Adjacent node not found: log as `broken_link` finding, continue
- File read error: log warning, skip that artifact
- Code parse error: log warning, skip that check
