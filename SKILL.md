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

**Warning:** The "lazily on demand" policy means deeper subdirectories (e.g., `src/server/pipelines/`) often never get their own nodes if the parent node (`src/server/index.md`) stays under the ~350 line limit. Over time, decisions that belong to the subdirectory accumulate in the parent, making it harder to shard accurately. Run a full-project structural audit periodically to detect these gaps and create child nodes before the parent bloats.

---

## Verification

- `scripts/extract.py` produces valid `.cns/graph.json` with correct edges
- 3-level bubble: change at level 3 → level 2 and `.cns/index.md` updated
- `human_notes` preserved unchanged after reconcile
- Decision about deleted feature removed after reconcile
- `status: dirty` → reconcile → `status: clean`
- `execute-task` pipeline: intent → plan → implement → test → commit → shard → bubble → validate → log → push → all green

---

## Project Conformity Audit

A full-project audit verifies that the CNS structure adheres to current conventions, removes stale artifacts accumulated over time, and ensures tooling scripts correctly handle edge cases. Run this when `validate.py` or `graph.py --check` report unexpected counts, when stale plan files accumulate, or before major releases.

### Stale Artifact Detection

1. **Survey `.cns/plans/`** — Check for completed task plans that were never deleted after sharding. Each plan should have been distributed into module `index.md` files via `shard()`. If decisions from a plan are already recorded in the target nodes, the plan file is stale and should be deleted.
2. **Survey `.cns/pns/`** — The centralized `pns/` directory is deprecated. Peripheral nodes should live directly within the source tree (e.g., `src/engine/index.md`) using the `parent` field to link upward. If `.cns/pns/` exists, verify its content is duplicated elsewhere, then delete it.
3. **Verify atomic sharding** — Before deleting any plan, confirm that its unique content (especially `decisions[]`) has been synthesized into the appropriate `index.md` node body. Do not delete plans that contain unsharded decisions.

### Script Fixes

- **extract.py must skip non-node files** — Files without valid YAML frontmatter (plain-text logs, ephemeral plans, old pns files) must not be counted as graph nodes. Add a frontmatter validity check before including a file in the node count. This prevents `graph.py --check` from reporting stale counts after cleanup.
- **validate.py must skip plain-text files** — `.cns/intent.md`, `.cns/log.md`, and plan files lack frontmatter and should be excluded from schema validation.

### Missing PNS Node Detection

4. **Survey for undocumented subdirectories** — Use the helper scripts to find directories with meaningful code boundaries but no `index.md`:
   ```bash
   python3 scripts/query.py <project_root> --fields path,title,type,status,decision_count
   python3 scripts/graph.py <project_root> --orphans
   ```
   Compare against the actual directory tree. Any subdirectory that represents a conceptual boundary (e.g., `src/server/pipelines/`, `src/wall/layout/`) should have a PNS node. **Do not** create nodes for leaf utility files or internal helpers — only for architectural boundaries that will receive sharded decisions.

5. **Line count audit** — All `index.md` files should stay under ~350 lines for optimal LLM context management. If a file approaches or exceeds this limit, split it by creating a child node for a subdirectory and moving appropriate decisions/content down. Use `query.py` to list all nodes with line counts or inspect files directly.

6. **Link new nodes into parents** — When creating a new PNS node, always add a `links[]` entry in the parent node's frontmatter pointing to the new child. This keeps the graph traversable in both directions (parent field goes up, links[] goes down).

### Node Splitting (when a file exceeds ~350 lines)

When an `index.md` approaches or exceeds the line limit:

1. **Identify topical boundaries** — Read the file and find natural break points where decisions, concepts, or content group into distinct themes (e.g., "Primitives" vs "Stubs" vs "Branching" in architecture).
2. **Create sub-files** — For each theme, create a new `.md` file in the same directory with `parent: index.md`. Move the relevant body content and any theme-specific decisions into the sub-file's frontmatter.
3. **Preserve high-level context in index.md** — The index.md must remain a comprehensive entry point. Rewrite it as an overview that: summarizes all core concepts, links to each sub-file, includes a system diagram or structural map if applicable, and aligns with research questions or product goals. A reader should understand the subsystem without opening sub-files.
4. **Update links[]** — Add `links[]` entries in the parent index.md pointing to each new sub-file. Ensure sub-files also link back to related code modules where appropriate.
5. **Rebuild and validate** — Run `extract.py`, `validate.py`, and `graph.py --check`.
6. **Commit atomically** — Include all new files + modified index.md in a single commit.

### Cleanup Pipeline

After removing stale artifacts and fixing scripts:

1. Run `python3 scripts/extract.py` to rebuild `.cns/graph.json`
2. Run `python3 scripts/validate.py` — must report PASSED
3. Run `python3 scripts/graph.py --check` — must report OK (no orphans, no cycles, no dangling links)
4. Commit all changes atomically with a message describing the cleanup