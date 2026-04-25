# Action: bubble

After any write to an index.md, ensure the parent layer is consistent with the current layer. Only `public: true` nodes continue bubbling upward. Private nodes update their parent but stop there.

---

## Behavior

1. Read the index.md at `path`.
2. Determine if the current layer changed a public interface or made a significant decision.
3. If yes: synthesize a 1-3 sentence summary of what changed.
4. Find the parent index.md (via `parent` field in frontmatter).
5. Read the parent's agent-authored body.
6. Check: is the parent already consistent with this change?
   - If the parent's body already reflects the change, nothing to do.
   - If not, insert the summary into the parent's agent-authored body.
7. If the current node has `public: true`, recursively call `bubble(parent)`.
8. Stop when reaching `.cns/index.md` or a node with `public: false`.

---

## What Constitutes "Significant"

Not every write triggers a bubble. Only:

- **Public API changes**: exported interfaces, function signatures, component props
- **Significant decisions**: new architectural approach, major refactor, technology choice
- **Status changes**: a node going from `dirty` to `clean` after reconciliation

Minor changes (typo fixes in body, reformatting) do NOT bubble.

---

## Synthesis for the Parent

The summary inserted into the parent is:

- 1-3 sentences
- Written from the parent's perspective
- Attributed to the child document (includes child title and date)

Example synthesized summary for `ui/button/index.md` bubble to `ui/index.md`:

> **Button package** (2026-04-25): Added `variant` prop to Button component, now supports `solid` | `outline` | `ghost`. Changes bubbled from `components/Button/index.md`.

---

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | string | Path to the index.md that was just updated |

---

## Bubble Chain Example

```
components/Button/index.md (public: true)
  → bubbles to ui/button/index.md (public: true)
    → bubbles to ui/index.md (public: true)
      → bubbles to .cns/index.md (project root, always public)
```

If `components/Button/index.md` has `public: false`, it updates its parent but does NOT continue upward.

---

## Stop Conditions

Bubble stops when:
- The current node has `public: false`
- The parent node has `public: false`
- `.cns/index.md` is reached (always final destination)
- The parent is not found (dangling link — log warning, stop)

---

## Usage in the Write Cycle

`bubble` is always called after a write or reconcile:

```
capture("services/auth/index.md", "Added refresh token rotation")
bubble("services/auth/index.md")
```

```
reconcile("services/auth/index.md")
bubble("services/auth/index.md")
```

The agent should call `bubble` as a follow-up to every write that could affect public interfaces.

---

## Error Handling

- Parent not found: log warning, stop bubbling (don't error)
- Parent's frontmatter is malformed: log warning, skip that parent
- Synthesizing summary fails: log warning, skip bubble for this node
