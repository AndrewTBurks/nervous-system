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

## Intent-Driven Development Workflow

When the user says something like *"work through the tasks in intent.md"* or *"complete phases X–Y"*, use the **`execute-task`** action (see above). The section below is the detailed reference for each phase.

### Principles

1. **One task at a time.** Never implement multiple tasks in a single commit. Each task gets its own plan, its own test cycle, and its own commit.
2. **Plan before implementing.** For each task, write a short plan in `.cns/plans/task-NN-slug.md`. The plan is the spec; the code is the implementation.
3. **Test after implementing.** Run the project's test command and build command before committing. A red test means the task is not done.
4. **Commit after each task.** `git add -A && git commit -m "feat(scope): ..."`. This keeps history clean, bisectable, and revertible.
5. **CNS maintenance is part of the task.** shard, bubble, validate, and log are not optional — they are the last steps of every task.

### Workflow Steps

**Step 1 — Read the backlog.**
Read `.cns/intent.md`. Identify the next uncompleted task and its phase. Do not skip ahead.

**Step 2 — Write the task plan.**
Create `.cns/plans/task-NN-description.md` with:
- Goal (one sentence)
- Plan (numbered steps, exact file paths, any schema or type changes)
- Verification (how to know it's done: tests pass, build succeeds, behavior observed)

Keep it short. A task plan is 10–30 lines, not a design doc. For detailed plan-writing guidance (DRY, YAGNI, TDD, bite-sized tasks), see the `writing-plans` skill.

**Step 3 — Implement.**
Follow the plan. Before coding, read the target module's `index.md` to respect existing `decisions[]`.

Patch existing files with `patch`, create new files with `write_file`. Read files as needed to locate exact strings for patching. If a plan step turns out to be wrong, update the plan file, then continue.

Use `delegate_task` when the task is large (≥3 files), UI-heavy, in an unfamiliar module, or when the user explicitly requests delegation. Otherwise implement directly to avoid coordination overhead.

**Step 4 — Verify.**
Run tests and build. Both must pass. If they fail, fix before committing. Do not defer fixes to "later."

**Step 5 — Commit (code only).**
```bash
git add -A
git commit -m "type(scope): description"
```
Use conventional commits. The commit message should make sense in `git log` without reading the plan.

If the user asked to "push after each task" or the project has an active remote, run `git push` immediately after the commit.

**Step 6 — Shard the plan into the graph.**
Read the completed plan. Distribute its content to the relevant `index.md` nodes throughout the codebase:
- Route decisions to the nearest module `index.md` `decisions[]`
- Route context to the module `index.md` body
- Route architecture-level decisions to `.cns/architecture/index.md`

Then delete the plan file — its content now lives in the graph.

**Step 7 — Bubble affected nodes.**
For every `index.md` modified by shard, push summaries up the parent chain to `.cns/index.md`.

**Step 8 — CNS health gate.**
```bash
python3 ~/.hermes/skills/nervous-system/scripts/validate.py /path/to/project
python3 ~/.hermes/skills/nervous-system/scripts/graph.py /path/to/project --check
```
If either fails, fix CNS issues before proceeding.

**Step 9 — Remove from intent.**
Delete the completed task from `.cns/intent.md`. `intent.md` is only for forward-looking work; completed tasks live in the log.

**Step 10 — Log completion.**
Append to `.cns/log.md`:
```markdown
### HH:MM — Task NN completed
- Decision DEC-XXX added to src/.../index.md
- File src/.../foo.ts implemented and tested
- Tests: X pass, 0 fail
```

**Step 11 — Commit (CNS updates).**
```bash
git add -A
git commit -m "docs(cns): shard task-NN decisions into graph, update intent.md + log.md"
```

**Step 12 — Push.**
```bash
git push
```

### Anti-Patterns

- **Batching multiple tasks into one commit.** This destroys bisectability.
- **Skipping tests because "it's just a small change."** Small changes break things constantly.
- **Skipping the CNS health gate.** validate.py + graph.py --check must pass before push.
- **Delegating by default.** Use direct implementation for small, familiar tasks.
- **Not reading module index.md before coding.** Violating existing decisions is expensive to fix.
- **Skipping the shard step.** Decisions that live only in commit messages are lost to the graph.
- **Writing one giant plan for 10 tasks.** Plans should be per-task. The intent file is the umbrella; plan files are execution units.

### Pitfalls

- **HTML entity encoding.** Subagents may write `&lt;`, `&gt;`, `&amp;gt;` instead of literal characters. If tests fail with syntax errors, check for entity encoding.
- **Subagent interruption.** If a `delegate_task` subagent is interrupted, verify state with `git status`, check files, and run tests before deciding to resume or re-implement.
- **Stale graph.json.** After shard/bubble, always re-run `extract.py` and `graph.py --check`.
- **Dirty working tree.** If `git status` shows uncommitted changes before starting a task, commit or stash them first.

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
| `execute-task(task_id)` | (inline) | Full pipeline: plan → implement → shard → bubble → commit/push | see below |
| `extract(project_root)` | `scripts/extract.py` | Build .cns/graph.json from directory tree | — |
| `validate(project_root)` | `scripts/validate.py` | Frontmatter validator — run after every CNS write | — |
| `search(project_root, pattern, ...)` | `scripts/search.py` | Grep-like search across CNS content | — |
| `query(project_root, ...)` | `scripts/query.py` | List/filter nodes by type, status, author, date | — |
| `graph(project_root, ...)` | `scripts/graph.py` | Build, check, or dump graph structure | — |
| `link(project_root, node?, ...)` | `scripts/link.py` | Show outgoing links + incoming backlinks | — |
| `move(project_root, old, new)` | `scripts/move.py` | Dry-run move with link rebasing — `--execute` to run | — |

---

## Action: execute-task (inline)

The `execute-task` action runs the full intent-to-ship pipeline for a single task from `.cns/intent.md`. It combines code implementation with CNS maintenance in one atomic flow.

### Pipeline

```
intent.md → plan → implement → test → commit → shard → bubble → validate → log → push
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | string | The task number from `.cns/intent.md` (e.g., `"16"`, `"17"`) |
| `delegate` | boolean | If true, dispatch a subagent for implementation. If false (default), implement directly. |

### Steps

**1. Read intent**
Read `.cns/intent.md`. Find the first uncompleted task matching `task_id` or the next uncompleted task if `task_id` is omitted. Do not skip ahead.

**2. Write the task plan**
Create `.cns/plans/task-NN-slug.md` with:
- Goal (one sentence)
- Plan (numbered steps, exact file paths, schema/type changes)
- Verification (how to know it's done)

Keep it short — 10–30 lines.

**3. Implement**
Patch existing files with `patch`, create new files with `write_file`.

Before coding, read the target module's `index.md` to respect existing `decisions[]`.

If `delegate=true`, dispatch a `delegate_task` with:
- The full plan text in `context`
- The module's `index.md` decisions in `context`
- `.cns/design/index.md` and `.cns/architecture/index.md` excerpts if relevant

**4. Verify**
Run the project's test command (e.g., `bun test`, `pytest`). Run the build command. Both must pass.

**5. Commit (code only)**
```bash
git add -A
git commit -m "type(scope): description"
```
Use conventional commits.

**6. Shard the plan into the graph**
Read the completed plan. For each decision, context note, or implementation detail:
- Route decisions to the nearest module `index.md` `decisions[]`
- Route context to the module `index.md` body
- Route architecture-level decisions to `.cns/architecture/index.md`

Then delete the plan file — its content now lives in the graph.

**7. Bubble affected nodes**
For every `index.md` modified by shard, push summaries up the parent chain to `.cns/index.md`.

**8. CNS health gate**
```bash
python3 ~/.hermes/skills/nervous-system/scripts/validate.py /path/to/project
python3 ~/.hermes/skills/nervous-system/scripts/graph.py /path/to/project --check
```
If either fails, fix CNS issues before proceeding.

**9. Remove from intent**
Delete the completed task from `.cns/intent.md`. `intent.md` is only for forward-looking work; completed tasks live in the log.

**10. Log completion**
Append to `.cns/log.md`:
```markdown
### HH:MM — Task NN completed
- Decision DEC-XXX added to src/.../index.md
- File src/.../foo.ts implemented and tested
- Tests: X pass, 0 fail
```

**11. Commit (CNS updates)**
```bash
git add -A
git commit -m "docs(cns): shard task-NN decisions into graph, update intent.md + log.md"
```

**12. Push**
```bash
git push
```

### When to Delegate

| Scenario | Direct | Delegate |
|----------|--------|----------|
| Task touches 1–2 files you understand | ✓ | — |
| Task is in a module you've been working in | ✓ | — |
| Task is large (≥3 files, complex logic) | — | ✓ |
| Task is UI-heavy (React components, styling) | — | ✓ |
| Task is in an unfamiliar module | — | ✓ |
| User explicitly asked to delegate | — | ✓ |
| Multiple independent tasks can run in parallel | — | ✓ (batch) |

### Delegation Context Template

When dispatching an implementer subagent, always include:

```markdown
TASK PLAN:
[paste full .cns/plans/task-NN-slug.md content]

MODULE CONVENTIONS (from src/MODULE/index.md):
[paste decisions[] from the target module's index.md]

DESIGN CONSTRAINTS (from .cns/design/index.md):
[paste relevant excerpts]

VERIFICATION REQUIREMENTS:
- Run: [test command]
- Run: [build command]
- Both must pass before returning
- Commit with: git add -A && git commit -m "type(scope): description"
```

### Anti-Patterns

- **Batching multiple tasks into one commit.** Each task gets its own commit. Code commit first, CNS commit second.
- **Skipping tests.** A red test means the task is not done.
- **Forgetting the CNS health gate.** validate.py + graph.py --check must pass before push.
- **Delegating by default.** Use direct implementation for small, familiar tasks to avoid coordination overhead.
- **Not reading module index.md before coding.** Violating existing decisions is expensive to fix.
- **Skipping the shard step.** Decisions that live only in commit messages are lost to the graph.
- **Writing giant plans.** One plan per task. The intent file is the umbrella; plan files are execution units.

### Pitfalls

- **HTML entity encoding.** Subagents or previous sessions may write `&lt;`, `&gt;`, `&amp;gt;` instead of literal characters. If tests fail with syntax errors in new files, check for entity encoding.
- **Subagent interruption.** If a `delegate_task` subagent is interrupted, verify state with `git status`, check files, and run tests before deciding to resume or re-implement.
- **Stale graph.json.** After shard/bubble, always re-run `extract.py` and `graph.py --check`. A stale graph breaks downstream queries.
- **Dirty working tree.** If `git status` shows uncommitted changes before starting a task, commit or stash them first.

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
5. All `links[]` paths point to existing files

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
- `execute-task` pipeline: intent → plan → implement → test → commit → shard → bubble → validate → log → push → all green
