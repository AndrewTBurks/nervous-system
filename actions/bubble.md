# Action: bubble

After any significant write to an index.md, ensure the parent layer is consistent with the current layer. The bubble always reaches the project root — but what gets written at each level depends on whether the change is externally relevant. The agent makes that judgment.

**Scripts referenced:** `bubble.py` (analysis), then LLM applies writes manually

---

## Behavior

```
1. Read the index.md at path.
2. Run bubble.py to analyze the parent chain.
3. Determine if this layer changed something externally relevant
   (public API, significant decision, new module).
4. If yes: synthesize a 1-3 sentence summary of what changed.
5. Walk the chain upward to the root:
   a. At each parent, check if its body already reflects the change.
   b. If not, insert the summary into the parent's agent-authored body.
   c. Continue to the next parent.
6. Stop when the root is reached or the change is purely local.
```

---

## What Constitutes "Significant"

Not every write triggers a bubble. Only:

- **Public API changes**: exported interfaces, function signatures, component props
- **Significant decisions**: new architectural approach, major refactor, technology choice
- **New module**: a previously undocumented area now has a PNS node

Minor changes (typo fixes, reformatting, internal refactors) do NOT bubble.

---

## Synthesis for the Parent

The summary inserted into a parent is:

- 1-3 sentences
- Written from the parent's perspective
- Attributed to the child (includes child title and date)

Example synthesized summary for `src/engine/index.md` bubble to `.cns/architecture/index.md`:

> **ThreadWeaver Engine** (2026-04-25): Added Orchestrator primitive shape [—,—,P,P] that progressively elaborates stubs as upstream results arrive. Changes bubbled from `src/engine/index.md`.

---

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | string | Path to the index.md that was just updated |

---

## Bubble Chain Example

```
src/engine/index.md
  → .cns/architecture/index.md
    → .cns/index.md (project root)
```

The agent walks the full chain. At `src/engine/index.md` it determines the Orchestrator decision is significant. It inserts a summary into `.cns/architecture/index.md`, then continues to `.cns/index.md`.

A purely internal change (e.g., renaming a private helper) would stop at the first parent and write nothing further up.

---

## Usage in the Write Cycle

`bubble` is called after a write that might affect public interfaces:

```
capture("services/auth/index.md", "Added refresh token rotation")
bubble("services/auth/index.md")
```

```
reconcile("services/auth/index.md")
bubble("services/auth/index.md")
```

---

## Error Handling

- Parent not found: log warning, stop bubbling (don't error)
- Parent's frontmatter is malformed: log warning, skip that parent
- Synthesizing summary fails: log warning, skip bubble for this node
