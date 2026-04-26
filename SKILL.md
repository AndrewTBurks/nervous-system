# Nervous System Skill

A persistent, living knowledge layer for software projects — a distributed natural language context graph connected to the codebase it describes. Documents live alongside code, maintained by the agent as a side effect of normal work, with human-editable zones, automatic reconciliation, and upward bubbling of public-facing decisions.

---

## Trigger Condition

**This skill triggers in two ways:**

### 1. Ambient (`.cns/` detected)

When a `.cns/` directory exists at the project root, the agent:
1. Loads this skill
2. Loads or creates `.cns/graph.json` (via scripts/extract.py)
3. Is ready to call any action on request

The skill never needs to be explicitly invoked — it is ambient.

### 2. Explicit invocation — `/nervous-system`

When the user types `/nervous-system` at the prompt, the agent:
1. Loads this skill
2. If `.cns/` does NOT exist → runs the **bootstrap** flow (see below)
3. If `.cns/` EXISTS → prompts the user to choose an action

**Action choices on explicit invocation:**

| # | Action | When to use |
|---|--------|-------------|
| 1 | **bootstrap** | No `.cns/` exists yet — initialize the nervous system |
| 2 | **capture** | Log a decision, record an intent, or note context |
| 3 | **traverse** | Review project structure and current state before planning |
| 4 | **reconcile** | Bring a dirty document back in sync with code and human intent |
| 5 | **shard** | Break a plan into index.md files |
| 6 | **bubble** | Manually push changes up the parent chain |

---

## Bootstrap Flow (when `.cns/` is absent)

Run this when initializing the nervous system for a new project.

**Step 1 — Gather context.** Ask the user:
```
No `.cns/` found. Let's bootstrap the nervous system.

Please share what you know:
1. What is this project called and what does it do?
2. What is the tech stack / key modules?
3. Do you have any existing design, architecture, or context docs?
4. Any key decisions already made? (auth strategy, data model, etc.)
5. What does "done" look like for this project?
```

**Step 2 — Create `.cns/` structure.** Create:
- `.cns/index.md` — project-level context, parent of all nodes
- `.cns/log.md` — activity log, starts with bootstrap entry
- `.cns/graph.json` — populated by scripts/extract.py
- `.cns/architecture/index.md` — system architecture
- `.cns/design/index.md` — design language, conventions
- `.cns/product/index.md` — audience, goals, roadmap direction
- `.cns/intent.md` — planned work (plain text, starts empty or with initial items)

**Step 3 — Link architecture/design/product** to `.cns/index.md` via `parent` fields.

**Step 4 — Run `scripts/extract.py`** to build the initial `graph.json`.

**Step 5 — Log** the bootstrap action in `.cns/log.md`.

---

## Empty Project with `.cns/` but No Code

If `.cns/` exists but the codebase is empty or nearly empty:
- Report the graph status (node count, orphan count)
- Prompt: "The graph has N nodes but no meaningful code structure yet. Would you like to scaffold modules, or continue without?"
- Never auto-create index.md files for empty directories

---

## Concepts

**index.md** — A document living in a directory. Contains context about the code: current state, historical decisions, references to related files.

**Distributed graph** — Each index.md is a node. Edges are defined by the `parent` field in frontmatter. The graph is traversed upward during planning.

**Central nervous system (.cns/)** — A folder at the project root that holds project-level knowledge. This is the root of the bubble chain. Contains cross-cutting concerns: architecture, design language, product goals, research background.

**Peripheral nervous system** — index.md files interleaved throughout the codebase (e.g. `src/engine/index.md`, `src/auth/index.md`). These document specific modules and components. They bubble upward through their `parent` chain, eventually reaching `.cns/index.md`. The PNS is the sensory layer — it captures what each part of the codebase actually does and why.

**Human zone** — The `human_notes` field in frontmatter is human-owned. The agent never modifies this field.

**Agent zone** — The body below the frontmatter `---` delimiter is agent-authored. The agent may rewrite this during reconcile.

**Dirty state** — When `human_notes` is updated, set `status: dirty`. The agent detects this and triggers reconciliation.

**Reconciliation** — The agent reads dirty documents, updates code to honor human intent, shards understanding back into documents, bubbles summaries upward, prunes stale decisions, marks `clean`.

**Bubbling** — After any write, the agent ensures the parent is consistent with the current layer. Significant changes propagate upward through the parent chain to `.cns/index.md`.

---

## Directory Structure

The nervous system has two parts:

**.cns/ — Central nervous system** (project root): cross-cutting knowledge, architecture, design, product goals.

**PNS — Peripheral nervous system** (interleaved with code): module-level documents that bubble upward.

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
  services/
    auth/
      index.md
      auth.ts
```

## Intents

Planned work lives in `.cns/intent.md` — a plain text file at the project level. Recent work is in `.cns/log.md`. No frontmatter, no schema.

```
.cns/
  index.md      # project context
  intent.md     # upcoming planned work
  log.md        # recent work done
  graph.json
  architecture/
  design/
  ...
```

**Why plain files?**

- No schema to maintain — just prose
- Immediately readable in a new session without running any scripts
- `intent.md` shows what needs doing; `log.md` shows what was done
- No ID tracking overhead — just sections and bullets

**`intent.md`** is the single source of truth for all planned work. Organize by area or priority. Keep it accurate — stale items should be removed or moved to log.

**`log.md`** records completed work with timestamps. After each session, append what was done. Easy to reconstruct context when resuming.

---

## Frontmatter Schema

See `schema.md` for full field reference.

Key fields:
- `title` (required): Human-readable name
- `type`: component | service | module | package | project
- `parent`: path to parent index.md (relative to project root)
- `links[]`: stable cross-references
- `decisions[]`: decision history — id, date, author, summary
- `human_notes`: **human's safe zone** — agent never modifies this
- `status`: clean | dirty | reconciling
- `last_reconciled`: ISO date

---

## Status Lifecycle

```
clean ──────► dirty ──────► reconciling ──────► clean
     (human edits)    (agent working)    (done)
```

---

## When Is an index.md Created?

**Lazily on demand.** When the agent identifies a gap requiring synthesis or research — during planning, implementation, or reconcile. extract.py does not auto-generate index.md files.

---

## Propagation Rules

The bubble always proceeds all the way to `.cns/index.md`. What changes at each level depends on whether the content is externally relevant:

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

After every write to an index.md, the agent checks: is the parent layer still consistent with this layer? If this layer changed something externally relevant (a public API, a significant decision), the agent synthesizes a 1-3 sentence summary and inserts it into the parent's agent-authored body. This cascades to `.cns/index.md`. Use `bubble.py` to analyze the chain before deciding what to write.

---

## Actions

Each action is defined in its own file under `actions/`.

| Action | File | Description | Scripts |
|--------|------|-------------|---------|
| `capture(path, content)` | `actions/capture.md` | Append decision to decisions[] | none |
| `read(path)` | `actions/read.md` | Read index.md, return frontmatter + body | none |
| `traverse(root)` | `actions/traverse.md` | Walk graph, build planning context | `extract.py`, `graph.py` |
| `shard(source_path)` | `actions/shard.md` | Parcel source file content into index.md files | `bubble.py`, `validate.py`, `graph.py` |
| `reconcile(path)` | `actions/reconcile.md` | Full reconcile algorithm | `validate.py`, `graph.py` |
| `bubble(path)` | `actions/bubble.md` | Show bubble chain — LLM decides what to write | `bubble.py` |
| `audit(path, depth?)` | `actions/audit.md` | Audit node + adjacent nodes against actual code | `graph.py`, `link.py` |
| `extract(project_root)` | `scripts/extract.py` | Build .cns/graph.json from directory tree | — |
| `validate(project_root)` | `scripts/validate.py` | Frontmatter validator — run after every CNS write | — |
| `search(project_root, pattern, ...)` | `scripts/search.py` | Grep-like search across CNS content | — |
| `query(project_root, ...)` | `scripts/query.py` | List/filter nodes by type, status, author, date | — |
| `graph(project_root, ...)` | `scripts/graph.py` | Build, check, or dump graph structure | — |
| `link(project_root, node?, ...)` | `scripts/link.py` | Show outgoing links + incoming backlinks | — |
| `move(project_root, old, new)` | `scripts/move.py` | Dry-run move with link rebasing — `--execute` to run | — |

---

## Validate After Every Write

After any CNS write, run the full validation suite:

```bash
# Validate frontmatter
python3 ~/.hermes/skills/nervous-system/scripts/validate.py /path/to/project

# Check graph integrity (orphans, cycles)
python3 ~/.hermes/skills/nervous-system/scripts/graph.py /path/to/project --check
```

Exit code 0 = pass, 1 = fail.

The validator checks:
1. Valid YAML frontmatter (--- delimited) in every `.cns/*.md` file
2. Required fields: `title`, `type`
3. Each `decisions[]` entry has `id:`, `date:`, `author:`, `summary:`
4. No duplicate decision IDs within a file
6. All `links[]` paths point to existing files

---

## Graph Extraction

Run `scripts/extract.py` to build `.cns/graph.json`:

```bash
python3 ~/.hermes/skills/nervous-system/scripts/extract.py /path/to/project
```

The script:
1. Walks project directory tree
2. Finds all index.md files
3. Parses frontmatter
4. Builds adjacency graph via `parent` field
5. Detects cycles, orphans, dangling links
6. Outputs `.cns/graph.json`

Exit code 1 if cycles or dangling links exist (actionable signal).

**Manual graph.json creation** — create the file at `.cns/graph.json` with this structure:

```json
{
  "generated": "2026-04-25T14:30:00Z",
  "nodes": [
    { "path": ".cns/research/index.md", "title": "Research", "type": "project" },
    { "path": ".cns/architecture/index.md", "title": "Architecture", "type": "project" }
  ],
  "edges": [
    { "from": ".cns/research/index.md", "to": ".cns/index.md", "label": "parent" },
    { "from": ".cns/architecture/index.md", "to": ".cns/index.md", "label": "parent" }
  ],
  "orphans": [],
  "cycles": [],
  "dangling_links": []
}
```

Validate manually: no cycles, no orphans, no dangling links. After any CNS structural change (adding/removing nodes, updating links), re-validate the graph.

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

---

## log.md Format

```
## 2026-04-25

### 14:30 — reconcile
- components/Button/index.md: reconciled, status -> clean
- bubbled to ui/button/index.md
- pruned: DEC-003 (feature removed)

### 14:25 — capture
- services/auth/index.md: added DEC-007 (author: agent)

### 14:20 — shard
- plan: 2026-04-25_feature-x.md
- sharded into 3 index.md files
```

---

## Verification

- `scripts/extract.py` produces valid `.cns/graph.json` with correct edges
- 3-level bubble: change at level 3 → level 2 and `.cns/index.md` updated
- `human_notes` preserved unchanged after reconcile
- Decision about deleted feature removed after reconcile
- `status: dirty` → reconcile → `status: clean`
