# Action: explore

The human reads or updates the central knowledge nodes through conversation with the agent. This is the default mode — it requires no explicit invocation, just ask about the system.

**Central nodes:** `.cns/architecture/index.md`, `.cns/design/index.md`, `.cns/product/index.md`, `.cns/research/index.md`, `.cns/index.md`

## When to use

- Human asks "what is our current architecture?"
- Human asks "what are our design conventions?"
- Human asks "why did we choose X over Y?"
- Human proposes a change to architecture, design, product goals, or research context
- Human says "update the design doc to reflect..."

## Steps

**1. Read relevant nodes**
Agent reads the central node(s) the human is asking about.

**2. Summarize**
Agent presents current state, decisions, and open questions in conversational form.

**3. Discuss**
Human and agent iterate on changes.

**4. Record provenance**
Agent **appends the human's specific direction to `human_notes`** as immutable provenance. The human never needs to say "record this" — their direction is always preserved.

**5. Synthesize**
Agent integrates the direction into the agent-authored body of the relevant central node(s).

**6. Bubble**
Agent pushes summaries up the parent chain to `.cns/index.md`.

**7. Commit (if modified)**
```bash
git add -A
git commit -m "docs(cns): update {architecture|design|product|research} from discussion"
```

## Notes

- This mode is **conversational and ambient**. It does not require `/nervous-system` or any explicit trigger.
- The agent detects when central nodes have changed relative to its last known state. No manual `status: dirty` is required.
- If the human edits `human_notes` directly, the agent detects this on next read and reconciles around it.