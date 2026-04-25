# Action: shard

Parse a completed plan and parcel its contents into the appropriate index.md files throughout the codebase. Used when a plan finishes — its insights get distributed into the documents nearest the code they describe.

---

## Behavior

1. Read the plan file at `plan_path`.
2. Extract all **decisions**, **context notes**, and **implementation details** from the plan.
3. For each piece of content:
   - Determine which directory/file it relates to in the codebase
   - Find the nearest index.md (or create one if it doesn't exist)
   - Insert the content into that index.md's appropriate section:
     - Decisions → `decisions[]` array
     - Context notes → agent-authored body (append or synthesize)
     - Design choices → either `decisions[]` or body, depending on type
4. Run `bubble()` on each affected node to propagate summaries upward.
5. Log to `.cns/log.md`.

---

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `plan_path` | string | Path to the completed plan file (e.g. `.hermes/plans/2026-04-25_feature-x.md`) |

---

## Plan Structure Expected

Plans typically contain:

```
## Decisions Made

- DEC-001: Chose Postgres over MongoDB for auth data
- DEC-002: Session tokens expire after 24h

## Context

The auth service needs to handle refresh token rotation...

## Implementation Notes

The token validation logic lives in services/auth/token.ts...
```

Each section maps to a different target in index.md.

---

## Mapping Content to index.md Files

1. Parse the plan to identify which code units it affects.
2. For each code unit, find its directory's index.md. If none exists, create one.
3. Decisions go to `decisions[]` with `author: agent` and a reference to the plan in the summary.
4. Context goes to the agent-authored body — the agent synthesizes a 1-3 sentence summary and appends it.
5. Implementation details that describe a specific file get linked in the body's relevant section.

---

## Example

```
shard(".hermes/plans/2026-04-25_auth-redesign.md")
```

After shard:
- `services/auth/index.md`: DEC-001, DEC-002 added to decisions; body updated with context
- `services/sessions/index.md`: created if needed; body updated with session design notes
- `.cns/architecture.md`: updated with high-level auth architecture summary

---

## What Gets Sharded

Not everything in a plan should be sharded. Guidelines:

| Plan content | Sharded? | Destination |
|-------------|---------|-------------|
| Architecture decision | Yes | Nearest index.md + `.cns/architecture.md` |
| Design choice | Yes | Nearest index.md |
| Implementation detail | Yes | Nearest index.md body |
| Meeting notes / exploration | No | Not sharded |
| TODOs and task breakdown | No | Not sharded |
| Context that explains why | Yes | Body of nearest index.md |

---

## Error Handling

- Plan file not found: error, don't proceed
- Code reference in plan doesn't match any existing directory: create a new index.md in that directory
- Malformed plan: shard what's parseable, log what couldn't be parsed

## CNS Doc-Migration Shard Variant

When migrating content from monolithic .md files into the CNS (e.g., consolidating ResearchPlan.md, EngineeringPlan.md into `.cns/research/index.md`, `.cns/architecture/index.md`, etc.), use this workflow instead of the plan-based shard above:

**Step 1 — Audit source content.** Read all source files, identify which CNS nodes need updates and what content goes where. List parity gaps.

**Step 2 — Commit before sharding.** `git add -A && git commit -m "shard: prepare for CNS migration"` — creates a restore point before any CNS modifications.

**Step 3 — Rewrite target nodes.** For content-rich nodes with duplicate section headers (common in research/architecture docs), prefer full file rewrites over targeted patches to avoid ambiguous match errors. Use write_file for complete replacement.

**Step 4 — Commit after migration.** `git commit -m "shard: migrated X docs to CNS"` — commit the new CNS content.

**Step 5 — Delete source files.** Remove the old monolithic .md files from the project root.

**Step 6 — Clean dangling links immediately.** Any `.cns/*/index.md` file that linked to a now-deleted source file must be patched to remove those links. Run `grep -r "deleted-filename" .cns/` to find all dangling references.

**Step 7 — Commit cleanup.** `git commit -m "fix: remove dangling links to deleted source docs from CNS nodes"` — this is the final commit confirming parity.

**Key pitfalls discovered through trial and error:**
- scripts/extract.py exists — graph.json is maintained via extract.py, not manually
- Full rewrites (write_file) are safer than patches when source docs have duplicate section headers — patch finds multiple matches and errors out
- Deleting source files without immediately cleaning dangling links leaves the CNS in a broken state (orphan detection will catch this when running extract.py)
- Always commit before starting — provides a safe restore point if CNS content gets mangled during migration
