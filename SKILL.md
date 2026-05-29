---
name: nervous-system
description: A persistent, living knowledge layer for software projects — a distributed natural language context graph connected to the codebase it describes. Documents live alongside code, maintained by the agent as a side effect of normal work, with human-editable zones, automatic reconciliation, and upward bubbling of public-facing decisions. Use when a project has a .cns/ directory at its root, or when the user invokes /nervous-system.
---

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

| Script | File | Description |
|--------|------|-------------|
| `bootstrap(project_root, ...)` | `scripts/bootstrap.py` | Initialize .cns/ structure for a new project |
| `extract(project_root)` | `scripts/extract.py` | Build .cns/graph.json from directory tree |
| `validate(project_root)` | `scripts/validate.py` | Frontmatter validator — run after every CNS write. Skips plain-text files (intent.md, log.md, plans/). |
| `search(project_root, pattern, ...)` | `scripts/search.py` | Grep-like search across CNS content |
| `query(project_root, ...)` | `scripts/query.py` | List/filter nodes by type, status, author, date |
| `graph(project_root, ...)` | `scripts/graph.py` | Build, check, or dump graph structure |
| `bubble(project_root, node_path)` | `scripts/bubble.py` | Show bubble chain — LLM decides what to write. **Arg order: project_root FIRST, node_path SECOND.** Wrong order produces a misleading error ("path/.cns not found"). |
| `move(project_root, old, new)` | `scripts/move.py` | Dry-run move with link rebasing |

`find_all_docs()` in `shared.py` skips `node_modules/` — required for pnpm/pnpm-lock environments where nested `docs/` directories appear inside `node_modules/.pnpm/`. Without this guard, `validate.py` crashes on frontmatter-less files inside locked packages.

## Standard Shard Pipeline

After distributing content into target CNS nodes:

1. **bubble each modified node** — `python3 scripts/bubble.py <project_root> <node_path>` (project_root first, node_path second)
2. **rebuild graph.json** — `python3 scripts/extract.py <project_root>`
3. **validate** — `python3 scripts/validate.py <project_root>`
4. **graph check** — `python3 scripts/graph.py <project_root> --check`
5. **delete the source plan file** — a completed plan that has been distributed into CNS nodes is stale; delete it
6. **commit** — `git add -A && git commit -m "shard: distribute <task> decisions into CNS nodes"`

**bubble.py argument order trap:** The script takes `project_root` first and `node_path` second. Reversing them produces an obscure error (`"node_path/.cns not found"`) that looks like a path resolution bug but is actually a bad argument order. Always verify the order when bubble fails.

---

## Bootstrap Flow (when `.cns/` is absent)

### Step 0 — Session Recovery (do this first if intent.md might be sparse)

Run `scripts/bootstrap.py` to initialize the nervous system for a new project. However, before running it, check whether the human said "bootstrap this project" as a continuation of prior work rather than a fresh start.

**Recovery procedure:**
1. Try broad session_search queries first (project name, keywords from the project) before narrow ones:
   ```
   session_search(query="site-astro", limit=5, sort="newest")
   ```
2. If results are sparse, browse recent sessions chronologically and scroll the most active one to find planning context:
   ```
   session_search(limit=5, sort="newest")  # browse recent
   session_search(session_id=<id>, around_message_id=<anchor>, window=20)  # scroll
   ```
3. Once the session is identified, scroll to messages around the audit/critique/planning portion — that's where tasks were defined.

## Legacy Feature Deletion (Shortcut)

When the user says "kill X" or "remove all legacy code related to X" with no ambiguity about the decision:

1. Delete the relevant code immediately — no plan file needed
2. Update the CNS decision array to reflect the removal
3. Commit in one pass: "kill: remove X" with TASK reference
4. Run CNS health gate (validate.py + graph.py --check)
5. Continue with the session

This shortcut applies only when: the deletion is unambiguous, the user said "kill" or "remove all", and the affected decision is already captured in CNS. For ambiguous scope or partial removals, use the full execute-task pipeline.

## Interview-First Task Collection

When the user says "add tasks to intent" or invokes `/nervous-system` with the intent to plan:

1. Ask for the full list — let Andrew dump everything at once
2. Clarify ambiguities in batch (routing: flat vs segmented? watermark: what does "doesn't work" mean exactly? project images: static visual effect vs not loading?)
3. Surface the consolidated task list for Andrew to confirm or correct
4. Write tasks to intent only after Andrew says "done"
5. Then execute tasks **one-by-one**, not in parallel

Andrew's words: *"keep asking me for additional feedback until I say done, then we will work through and build one-by-one."* This is the canonical pattern for this project.

## Plan Iteration Workflow (existing plan already has answers)

When the nervous-system skill is invoked and the user says to "shape the plan" or "iterate on the plan" and an existing `.cns/plans/<name>.md` already contains Q&A from a prior session:

1. **Read the full plan** — do not assume what is or isn't answered; read the entire document
2. **Identify which Open Qs are genuinely still open** — many plans mark questions as "open" even after they were answered in the same session; patch stale markers immediately (e.g., remove "(pending)" from an approved item, remove answered Qs from the Open Qs list, consolidate duplicate statements)
3. **Ask only about the remaining pivots** — do not re-ask answered questions; present the design brief focusing only on what is genuinely unresolved
4. **Update the plan atomically** — after the brief is confirmed, patch all changes in one batch: resolved decisions, stale markers removed, duplicate statements consolidated; then run validate.py + graph.py --check

**Pattern for pivots:** A pivot is a spec decision where two or more implementation approaches are equally plausible and the choice materially affects the output. Not every "open question" is a pivot — many can be decided by the agent with a reasonable default. Ask only about the pivots; assert the non-pivots with a recommendation and move on.

Example from site-astro garden redesign: the grid layout mechanism (CSS columns vs CSS Grid dense vs JS masonry) was a pivot — three equally plausible approaches, materially different outputs. The year watermark position was also a pivot — section header vs card overlay. Everything else (card image aspect ratio, tagline text, taxonomy structure) was not a pivot — it could be decided and asserted.

This avoids the failure mode of presenting a full 20-question brief when 18 of those questions are already answered. The user gets a short brief focused only on what actually blocks progress.

**Andrew's planning preference**: Andrew uses iterative Q&A: "keep asking me questions until I say done." Do not present a full checklist upfront. Surface what you have, ask what else is needed, continue until he says stop, then finalize. This overrides the standard "identify pivots and assert non-pivots" approach when Andrew invokes the nervous-system skill for planning.

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

## Session Reference Library

| File | Purpose |
|------|---------|
| `references/site-astro-bio-workflow.md` | Landing page multi-role bio text workflow: research statement extraction from thesis codebase, proprietary work Q&A protocol, Andrew's ordering preferences (Epsilon before PhD), build verification pattern |
| `references/site-astro.md` | site-astro project notes: CNS structure, bootstrap recovery rule, overdrive timeout rule, image performance debugging (feDisplacementMap compositor breakage, box-shadow repaint, Astro class prop forwarding, dark screenshot visibility) |
| `references/displayframe-filters.md` | Current DisplayFrame filter chain: barrel (GPU-cached blur+colorMatrix+composite, no displacement), crt-noise (static feTurbulence). Why feDisplacementMap was removed (June 2026), class-forwarding requirement, where CRT stays vs. where it is killed |
| `references/site-astro-essay-interview.md` | REMOVED — interview Q&A lives in `.cns/intent` in the project, not in the skill. When mining transcript for essay content, parse `~/.hermes/all-user-messages-last48h.txt` using SESSION markers + `====` separator. See message extraction pitfall under execute-mode + subagent-driven-development. |
| `references/site-astro-taxonomy.md` | Taxonomy vs folder structure mismatch for site-astro: product spec defines 6 content types (essay, project, publication, note, update, milestone); actual `src/data/` has 6 folders but `essays/` and `publications/` had no Astro collections registered, `notes` collection was registered but `src/data/notes/` did not exist; how to detect and fix silent collection exclusions |

---

## Essay restructure proposal format (what works)

When presenting a proposed essay restructure for Andrew to approve before writing tasks to intent:

- Give **exact placement**: before paragraph N, after sentence M, or replace X with Y
- Show the **blockquotes in context**: which quote goes where and what it replaces or anchors
- Keep the proposal **short and scannable**: this is Andrew's review pass, not the final prose
- **Do not** offer weak A/B options when neither is compelling — present the analysis and the recommended structure directly
- Wait for Andrew's confirmation before patching intent.md

Andrew's approval pattern: he reads the proposed restructure, flags anything off, and says "go ahead" or "yes" or "that looks right." If he skips a section, ask specifically.

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

## CNS Audit Checklist (run after any session that modified the codebase or CNS)

After a session that made changes, always run:

```bash
cd <project_root>
python3 ~/.hermes/skills/nervous-system/scripts/validate.py .
python3 ~/.hermes/skills/nervous-system/scripts/graph.py . --check
```

Both must pass with exit 0 before the session is considered complete.

**If validate.py fails with "no YAML frontmatter" errors**, check whether `shared.py`'s `find_all_docs()` is skipping `node_modules`. If a CNS-free project has `node_modules/.pnpm/.../index.md`, the PNS glob will pick it up and the validator will crash on it. Fix: add `if "node_modules" in p.parts: continue` to the `root.rglob("index.md")` loop in `shared.py`.

**If graph.py reports a stale node count**, run `extract.py` to rebuild `graph.json`.

**If graph.py reports orphan/dangling links**, the `links[]` array in a PNS node has a broken path. Remember: links resolve from the project root, not from the `.cns/` directory.
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

### Script Fixes (applied)

- **shared.py `find_all_docs()` must skip `node_modules`** — `rglob("index.md")` can match documentation inside pnpm bundled deps (e.g. `@vercel/functions/docs/modules/index.md`) which has no frontmatter and causes validate.py to crash. Add `if "node_modules" in p.parts: continue` inside the loop. Applied 2026-05-28.
- **extract.py must skip non-node files** — Files without valid YAML frontmatter (plain-text logs, ephemeral plans, old pns files) must not be counted as graph nodes. Add a frontmatter validity check before including a file in the node count. This prevents `graph.py --check` from reporting stale counts after cleanup.
- `validate.py` must skip plain-text files — `.cns/intent.md`, `.cns/log.md`, and plan files lack frontmatter and should be excluded from schema validation.
- **Intent task retention:** Andrew keeps completed tasks visible (marked `[x]`) in `intent.md` as a record. Do NOT delete checked-off tasks — only mark them done. Only delete tasks that were never started or are being abandoned.
- **shared.py: always skip node_modules** — `find_all_docs()` uses `root.rglob("index.md")` which descends into `node_modules/`. Any Astro project with Vercel Functions or similar packages will have `node_modules/.pnpm/.../index.md` files. Always add `if "node_modules" in p.parts: continue` to the PNS loop in `find_all_docs()`. Without this, `validate.py` crashes when it tries to read those files as CNS nodes.

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

4. Run `python3 scripts/extract.py` to rebuild `.cns/graph.json`
5. Run `python3 scripts/validate.py` — must report PASSED
6. Run `python3 scripts/graph.py --check` — must report OK (no orphans, no cycles, no dangling links)
7. Commit all changes atomically with a message describing the cleanup

---

## Schema Reference

### links[] Path Resolution

All paths in `links[]` entries resolve relative to the **project root** (the directory containing `.cns/`), not relative to the `.cns/` directory. This means a PNS node at `src/components/index.md` must use paths like `src/components/DisplayFrame.astro`, not `DisplayFrame.astro`. The validator enforces this. If a link fails validation, check whether the path is relative to the wrong directory.

## Practical Notes

### Intent write conflicts with concurrent subagents
When multiple agents patch `intent.md` simultaneously (parent + sibling subagents), the sibling's prior modification can invalidate the parent's patch target string. Always `read_file` immediately before patching. If both agents must write to the same section, serialize: parent reads, patches, and commits before the subagent writes.

### `impeccable` integration
When a `$impeccable` critique produces findings that map to intent tasks, write those tasks to `.cns/intent.md` immediately after the critique session. Do not let critique findings sit untracked.

For site-astro: `$impeccable critique` findings about CSS defects (date off-by-one, milestone label wrapping, year watermark) map directly to intent tasks. Write the task list to intent before ending the critique session.

### Intent task numbering pitfall
When adding tasks to `intent.md`, append new tasks at the END of the list with the next sequential number. Do not insert new tasks between existing task numbers — this creates numbering gaps that confuse the user (e.g., TASK-040 added between TASK-038 and TASK-039 causes the user to ask "where did task 39 go"). If you must insert between existing numbers, explicitly warn the user about the renumbering and confirm before patching.

### Graph drift during long sessions
`graph.json` is the traversal context for traverse, plan, and execute-task. If new CNS nodes are created or moved during a session, `graph.json` becomes stale. `graph.py --check` detects this but does not auto-repair. After any structural CNS change, re-run `extract.py` before the next graph-dependent operation. See `references/validate-py-skip-list.md` for maintenance notes on the validate.py skip list.

### Plan files left after failed shard
If shard fails mid-write, the plan file stays in `.cns/plans/`. The next execute-task targeting that task ID will pick it up. Orphaned plans (created but never executed) accumulate — clean them up periodically by listing `.cns/plans/`.

### Taxonomy-to-folder alignment (Astro projects)
For Astro projects using `src/content.config.ts` with folder-based collections:
1. Check `src/data/` directory — each subdirectory is a potential collection
2. Check `src/content.config.ts` — which collections are actually registered
3. Compare against the product spec's content type taxonomy (6 types: essay, project, publication, note, update, milestone)
4. A missing collection registration means that folder's content is silently excluded from the site — a concrete bug, not just a consistency issue
### Bootstrap recovery before `bootstrap.py`

Before running `bootstrap.py` on an established project, always search for prior session context first:

```
session_search(query="<project-name>", limit=5, sort="newest")
session_search(limit=5, sort="newest")
```

Scroll the most relevant session to find planning context before bootstrapping. Only run `bootstrap.py` if no useful session context exists.

**Recovery shortcut:** When `.cns/plans/` already has plan files and the user says "bootstrap this project" as a continuation of prior work (not a fresh start), skip bootstrap.py and instead scroll the most recent session to recover the prior planning context. Bootstrap is for truly new projects.

### execute-mode + subagent-driven-development integration

### Interview verification before writing from prior intent

When `execute-mode` is invoked and `.cns/intent` already contains interview Q&A from a prior session:

1. **Read the full intent** — do not assume a prior interview is complete or uncorrected. Andrew may have amended answers (e.g., "that was wrong, it was actually X") or marked specific topics "not compelling" in the prior session.
2. **Check for Andrew corrections** — scan the interview record for phrases like "was wrong", "actually", "not compelling", "don't include". These override whatever the original interview recorded.
3. **Do not skip re-interviewing** if the prior interview lacked specificity or if the essay still has structural gaps after writing. Andrew said "interview me to write a new article from scratch" — even with a prior intent record, surface the key questions again and confirm the answers are still current.
4. **Use the interview answers as the writing input** — do not substitute a read of the existing essay for Andrew's own words.

This prevents the failure mode where: (1) a prior session mines pivotal messages and captures them in intent; (2) a subsequent session uses that intent as a substitute for re-interviewing; (3) Andrew's corrections from the original session are not carried forward, and new pivots from the rewrite session are missed.

### execute-mode + subagent-driven-development integration

1. **Sequential execution is the default** — Andrew prefers tasks executed one at a time in sequence, not parallelized, even when tasks are independent. Each task completes: build passes → intent updated → push → next task.
2. **Load `subagent-driven-development` skill** — the skill defines the two-stage review pattern but Andrew's preference overrides the parallel batching default. Use sequential per-task dispatch with parent-level verification between tasks.
3. **Parent verifies and updates intent** — after subagent completes its run, the controller (not the subagent) marks tasks complete in intent.md. The controller runs `bun run build`, validate.py, graph.py --check, then updates intent.md.
4. **CNS health gate is mandatory after any write** — after every session that modified the codebase or CNS, run validate.py + graph.py --check. Both must pass before marking the session complete.
5. **Large structural tasks** — tasks that touch multiple collections, move files between directories, or modify content.config.ts take ~4-5 minutes as a single subagent session. Budget time accordingly. Smaller targeted patches (image height, date format, leading) are faster direct-patched by the controller.

**Message extraction pitfall during execute-mode content rewrite:** When Andrew says "mine my chat logs for pivotal prompts," or similar, and you query `state.db` for user messages — skill command invocations embed Andrew's actual prompt text inside the skill header block (e.g. `/impeccable craft new idea: ...`). These messages get stripped from the pivotal-extraction output because the skill header parser discards them as metadata noise.

**How to recover them:** Read `~/.hermes/all-user-messages-last48h.txt` (or the raw `state.db` query output) and search for Andrew-specific phrases rather than relying on the pivotal list alone. Specific phrases to look for: "maggie appleton", "CRT dies", "some projects are also publications", "date ordering is an absolute need". When you find the match, context-expand around it to get the surrounding messages (which are the ones that preceded and followed the pivot). The pivotal-extraction script skips skill command blocks as noise; the raw content is where the real messages live.

### execute-mode all (full pipeline)

When Andrew says "execute-mode all tasks in intent" (not one-at-a-time):

1. Read `intent.md` in full — identify all uncompleted tasks
2. For each task, execute one-by-one in sequence:
   - create ephemeral plan in `.cns/plans/`
   - implement → test → commit → shard → bubble → validate → log → push
3. After ALL tasks complete:
   - Run CNS health gate: `validate.py` + `graph.py --check`
   - Run `$impeccable critique` on the live dev server
   - Map critique findings to intent tasks
   - Add new tasks to `intent.md` (append at end, next sequential number)
   - Mark original tasks `[x]` done
   - Commit and push
4. The CNS health gate runs after the critique pass as well, not just after implementation

## execute-mode: full content rewrite (essay/article from scratch)

When Andrew says "completely remade" or "write from scratch" for a piece of content (essay, article, bio, description):

**This is NOT execute-task.** The standard execute-task pipeline is for implementing defined tasks from intent.md. A content rewrite from scratch requires an interview-first approach:

1. **Interview to clarify** — Ask open-ended questions to surface the core idea, the specific angle, what the piece should convey that the current version does not. Andrew wants iterative Q&A: keep asking until he says done. Do NOT present a full checklist upfront. Do not ask all questions at once.
2. **Write from interview answers** — Using the clarified direction, write the piece directly. Do not go through plan → shard → bubble. The deliverable is the content file itself.
3. **Validate and push** — Run CNS health gate, commit.

**Key questions that reliably surface pivot points for a workflow essay:**
- Before any chat: what was the site at the start? Blank project or had history?
- First bad reaction: what specifically made you say "it looks pretty miserable"?
- Design decisions: which ones felt like your actual judgment vs. agent default?
- The taxonomy moment: did you come in knowing "digital garden," or did it emerge?
- CRT removal: what tipped it — perf, broken visual, or a specific moment?
- The micro-corrections (24.75px, nav margin, year label): would you point to those as what you personally decided?
- Final instruction: what did you actually tell the agent to make it a portfolio piece vs. a tutorial?

**What this mode handles:**
- "the essay needs to be completely remade" → interview-first, then write
- "write a new piece about X" → interview to clarify direction, then write
- "help me articulate what this project does" → interview to extract, then write

**What this mode does NOT handle:**
- Adding tasks to intent.md (use plan mode)
- Implementing feature tasks (use execute-task)
- Multi-page content restructuring (use figure-it-out)

### CNS health gate after every write

After a session that made changes, always run:

```bash
cd <project_root>
python3 ~/.hermes/skills/nervous-system/scripts/validate.py .
python3 ~/.hermes/skills/nervous-system/scripts/graph.py . --check
```

Both must pass with exit 0 before the session is considered complete. If validate.py fails with "no YAML frontmatter" errors, check whether `shared.py`'s `find_all_docs()` is skipping `node_modules`. If graph.py reports a stale node count, run `extract.py` to rebuild `graph.json`. If graph.py reports orphan/dangling links, fix the `links[]` array in the affected PNS node.
Every skill directory that Hermes should discover must contain a `SKILL.md` with valid YAML frontmatter:

```yaml
---
name: <skill-name>
description: <natural-language trigger description>
---
```

Without these fields the skill directory exists but Hermes treats it as inactive. This is a common failure mode when restoring a skill from a remote source (GitHub) without local frontmatter. To verify loadability: `hermes skills list` (forces rescan) then `skill_view(name=<name>)`.
