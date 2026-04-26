# Action: reconcile

Run the full reconciliation algorithm on one or more index.md files. Triggered when a document has `status: dirty`. This is the core feedback loop that aligns code with human intent.

**Scripts referenced:** `validate.py`, `graph.py`

---

## Behavior

```
1. Find all index.md with status: dirty
2. If path is provided and is a directory, find all dirty index.md within it
3. Cross-check dirty nodes: if siblings conflict, deepest path wins
4. Read human_notes from each dirty document
5. For each dirty document:
   a. Determine what code changes honor the human intent
   b. Make those code changes
   c. Update the agent-authored body to reflect new state
   d. Preserve human_notes unchanged
   e. Add any new decisions to decisions[]
6. For each updated document:
   a. Run bubble consistency check against parent
   b. If parent is now inconsistent, update parent's agent body
   c. Continue bubbling to the root
7. Prune: remove decisions whose premise no longer holds
8. Set status: clean, update last_reconciled
9. Log action to .cns/log.md
```

---

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | string | Path to an index.md or directory. If directory, reconcile all within it recursively. |

---

## The human_notes Contract

The agent reads `human_notes` and treats it as **intent that must be honored**. The agent does not question it, parse it structurally, or ignore it. It translates human prose intent into code changes.

If the agent cannot determine how to honor a human note (ambiguous, contradictory with other notes), it should:
1. Make the most reasonable interpretation
2. Log a warning describing the ambiguity
3. Continue rather than stall

---

## Code Update Step (5a)

This is the most critical and least automatable step. The agent must:

1. Read the `human_notes` prose
2. Understand what the human wants changed
3. Identify which files in the codebase need to change
4. Make those changes

If the human note says "the border-radius here is intentional — it's 4px to match the design token" and the agent is about to refactor the component:

- The agent reads the note
- The agent understands the constraint
- The agent does NOT change the border-radius during the refactor

The agent should verify the code was actually changed: after making changes, the agent checks whether the code now honors the intent. If not, it tries again or logs a conflict.

---

## Validation Gate

After updating code but before marking `clean`, the agent should verify:

1. **Code honors intent**: Read the changed code. Does it reflect what `human_notes` asked for?
2. **No regression**: Did the change break anything adjacent?

If validation fails, the agent logs the conflict in `.cns/log.md` and sets `status: dirty` again rather than marking `clean`.

---

## Pruning (Step 7)

For each decision in `decisions[]`:

1. Read the code the decision refers to (via `summary` text or linked file)
2. Ask: does the code still reflect this decision?
3. If the premise no longer holds (feature removed, approach changed, file deleted), remove the decision

Pruning is aggressive. Stale decisions are noise. They are deleted, not archived.

---

## Example

```yaml
# services/auth/index.md — dirty state
---
title: Auth Service
status: dirty
human_notes: |
  We agreed to revisit the token expiry policy after beta.
  Do not extend expiry beyond 24h without checking the security team.
decisions:
  - id: DEC-001
    date: 2025-01-10
    author: human
    summary: Chose JWT over sessions
---
```

After reconcile:

```yaml
# services/auth/index.md — clean state
---
title: Auth Service
status: clean
last_reconciled: 2026-04-25
human_notes: |
  We agreed to revisit the token expiry policy after beta.
  Do not extend expiry beyond 24h without checking the security team.
decisions:
  - id: DEC-001
    date: 2025-01-10
    author: human
    summary: Chose JWT over sessions
  - id: DEC-002
    date: 2026-04-25
    author: agent
    summary: Token expiry policy confirmed at 24h per human_notes (2026-04-20)
---
```

The agent authored a new decision noting the confirmation, then bubbled the update upward.

---

## Error Handling

- If the file has malformed frontmatter: attempt to recover, log warning
- If human_notes is empty but status is dirty: this is a system error — log and set status back to clean
- If the agent cannot figure out how to honor human_notes: make best effort, log the ambiguity, proceed
