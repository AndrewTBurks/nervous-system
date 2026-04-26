# Nervous System Skill

A persistent, living knowledge layer for software projects — a distributed natural language context graph connected to the codebase it describes. Documents live alongside code, maintained by the agent as a side effect of normal work, with human-editable zones, automatic reconciliation, and upward bubbling of public-facing decisions.

---

## Trigger Condition

**This skill triggers in two ways:**

### 1. Ambient (`.cns/` detected)

When a `.cns/` directory exists at the project root, the agent:
1. Loads this skill
2. Loads or creates `.cns/graph.json` (via `scripts/extract.py`)
3. Is ready to call any action on request

When the user asks about architecture, design, or product goals → use **explore**.
When the user wants to plan upcoming work → use **plan**.
When the user wants autonomous execution through intent.md → use **execute-task**.

### 2. Explicit invocation — `/nervous-system`

When the user types `/nervous-system` at the prompt, the agent:
1. Loads this skill
2. If `.cns/` does NOT exist → runs the **bootstrap** flow (see below)
3. If `.cns/` EXISTS → prompts the user to choose an action

**Action choices on explicit invocation:**

| # | Action | When to use |
|---|--------|-------------|
| 1 | **bootstrap** | No `.cns/` exists yet — initialize the nervous system |
| 2 | **explore** | Ask about or update architecture/design/product/research |
| 3 | **plan** | Populate intent.md with upcoming tasks |
| 4 | **execute-task** | Run full intent-to-ship pipeline for one task |

The remaining actions (capture, read, traverse, shard, reconcile, bubble, audit) are invoked automatically by the three modes above. See the Action Index for details.

---

## The 3 Modes

The nervous system is organized around three human interaction patterns. The agent recognizes which mode the human is in and responds accordingly.

### explore — Inspect/Update Central Descriptions

The human reads or updates central knowledge nodes conversationally. The agent records human direction in `human_notes` as immutable provenance, synthesizes it into the agent-authored body, and bubbles upward.

See `actions/explore.md` for full procedure.

### plan — Plan Upcoming Work

The human and agent collaboratively populate `.cns/intent.md` with the next phase of work. The agent traverses current state, proposes tasks, the human approves/modifies, and the agent writes the approved tasks.

See `actions/plan.md` for full procedure.

### execute-task — Hands-Off Execution

The human delegates implementation to the agent (or subagents) and expects autonomous progress through intent.md. For each task: plan → implement → test → commit → shard → bubble → validate → log → push.

See `actions/execute-task.md` for full procedure.

**Mode switching:**
- Human asks "what is our current architecture?" → explore
- Human asks "what should we work on next?" → plan
- Human says "execute the next 3 tasks" → execute-task

---

## Core Concepts

**index.md** — A document living in a directory. Contains context about the code: current state, historical decisions, references to related files.

**Distributed graph** — Each index.md is a node. Edges are defined by the `parent` field in frontmatter. The graph is traversed upward during planning.

**Central nervous system (.cns/)** — Project-level knowledge at the root: architecture, design language, product goals, research background. This is the root of the bubble chain.

**Peripheral nervous system** — index.md files interleaved throughout the codebase (e.g. `src/engine/index.md`). These document specific modules and bubble upward through their `parent` chain to `.cns/index.md`.

**Human zone** — The `human_notes` field in frontmatter is human-owned. The agent never modifies this field.

**Agent zone** — The body below the frontmatter `---` delimiter is agent-authored. The agent may rewrite this during reconcile.

**Reconciliation** — The agent reads dirty documents, updates code to honor human intent, shards understanding back into documents, bubbles summaries upward, prunes stale decisions, marks `clean`.

**Bubbling** — After any write, the agent ensures the parent is consistent with the current layer. Significant changes propagate upward through the parent chain to `.cns/index.md`.

For full schema, status lifecycle, propagation rules, and pruning rules, see `schema.md`.

---

## Directory Structure

```
project/
  .cns/                    # central nervous system
    index.md               # project-level context
    intent.md              # upcoming planned work (plain text)
    log.md                 # activity log (plain text)
    graph.json             # extracted adjacency graph
    architecture/          # system architecture, key tradeoffs
      index.md
    design/                # design language, conventions
      index.md
    product/               # audience, users, goals
      index.md
    research/              # background research, related work
      index.md
    plans/                 # ephemeral task plans (created per task, deleted after shard)
  src/
    engine/
      index.md             # peripheral: engine module
      engine.ts
    auth/
      index.md             # peripheral: auth module
      auth.ts
  components/
    Button/
      index.md             # peripheral: component
      button.tsx
```

`.cns/` — Central nervous system: cross-cutting knowledge.

PNS — Peripheral nervous system: module-level documents interleaved with code that bubble upward.

---

## Action Index

Each action is defined in its own file under `actions/`.

| Action | File | Description |
|--------|------|-------------|
| `explore` | `actions/explore.md` | Inspect/update central descriptions (Mode A) |
| `plan` | `actions/plan.md` | Collaborative planning into intent.md (Mode B) |
| `execute-task(task_id, delegate?)` | `actions/execute-task.md` | Full intent-to-ship pipeline (Mode C) |
| `capture(path, content)` | `actions/capture.md` | Append decision to decisions[] |
| `read(path)` | `actions/read.md` | Read index.md, return frontmatter + body |
| `traverse(root)` | `actions/traverse.md` | Walk graph, build planning context |
| `shard(source_path)` | `actions/shard.md` | Distribute plan content into index.md files |
| `reconcile(path)` | `actions/reconcile.md` | Full reconcile algorithm |
| `bubble(path)` | `actions/bubble.md` | Show bubble chain — LLM decides what to write |
| `audit(path, depth?)` | `actions/audit.md` | Audit node + adjacent nodes against actual code |

---

## Script Index

|| Script | File | Description |
||--------|------|-------------|
|| `bootstrap(project_root, ...)` | `scripts/bootstrap.py` | Initialize .cns/ structure for a new project |
|| `extract(project_root)` | `scripts/extract.py` | Build .cns/graph.json from directory tree |
|| `validate(project_root)` | `scripts/validate.py` | Frontmatter validator — run after every CNS write |
|| `search(project_root, pattern, ...)` | `scripts/search.py` | Grep-like search across CNS content |
|| `query(project_root, ...)` | `scripts/query.py` | List/filter nodes by type, status, author, date |
|| `graph(project_root, ...)` | `scripts/graph.py` | Build, check, or dump graph structure |
|| `link(project_root, node?, ...)` | `scripts/link.py` | Show outgoing links + incoming backlinks |
|| `move(project_root, old, new)` | `scripts/move.py` | Dry-run move with link rebasing |

---

## Bootstrap Flow (when `.cns/` is absent)

Run `scripts/bootstrap.py` to initialize the nervous system for a new project.

```bash
python3 ~/.hermes/skills/nervous-system/scripts/bootstrap.py <project_root> [options]
```

**Options:**
- `--name`: Project name
- `--description`: One-line description
- `--stack`: Tech stack (comma-separated)
- `--modules`: Key modules (comma-separated)
- `--decisions`: Existing decisions in `ID|date|author|summary` format, one per line

**Without options**, it creates skeleton files with placeholder content.

**What it creates:**
- `.cns/index.md` — project-level context, parent of all nodes
- `.cns/log.md` — activity log with bootstrap entry
- `.cns/graph.json` — populated by calling `extract.py`
- `.cns/architecture/index.md` — system architecture
- `.cns/design/index.md` — design language, conventions
- `.cns/product/index.md` — audience, goals, roadmap direction
- `.cns/research/index.md` — background research, related work
- `.cns/intent.md` — planned work (plain text, starts with Phase 1 placeholder)
- `.cns/plans/` — directory for ephemeral task plans

All central nodes are linked to `.cns/index.md` via `parent` fields.

---

## Empty Project with `.cns/` but No Code

If `.cns/` exists but the codebase is empty or nearly empty:
- Report the graph status (node count, orphan count)
- Prompt: "The graph has N nodes but no meaningful code structure yet. Would you like to scaffold modules, or continue without?"
- Never auto-create index.md files for empty directories

---

## When Is an index.md Created?

**Lazily on demand.** When the agent identifies a gap requiring synthesis or research — during planning, implementation, or reconcile. `extract.py` does not auto-generate index.md files.

---

## Verification

- `scripts/extract.py` produces valid `.cns/graph.json` with correct edges
- 3-level bubble: change at level 3 → level 2 and `.cns/index.md` updated
- `human_notes` preserved unchanged after reconcile
- Decision about deleted feature removed after reconcile
- `status: dirty` → reconcile → `status: clean`
- `execute-task` pipeline: intent → plan → implement → test → commit → shard → bubble → validate → log → push → all green