# Action: execute-task

Run the full intent-to-ship pipeline for a single task from `.cns/intent.md`. This is **Mode C** — autonomous execution with CNS maintenance as a mandatory final phase.

## Pipeline

```
intent.md → plan → implement → test → commit → shard → bubble → validate → log → push
```

**11 steps total** (0 pre-flight + 10 execution steps).

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | string | The task number from `.cns/intent.md` (e.g., `"16"`, `"17"`) |
| `delegate` | boolean | If true, dispatch a subagent for implementation. If false (default), implement directly. |

## Steps

**0. Pre-flight — ensure graph is current**
```bash
python3 ~/.hermes/skills/nervous-system/scripts/extract.py <project_root>
```
A stale `graph.json` produces stale traversal context. Run this before every session.

**1. Read intent**
Read `.cns/intent.md`. Find the first uncompleted task matching `task_id` or the next uncompleted task if `task_id` is omitted. Do not skip ahead.

**2. Write the task plan**
Create `.cns/plans/task-NN-slug.md` with exactly these 7 sections:

| Section | Purpose | Shard target |
|---------|---------|-------------|
| **Goal** | One sentence describing the task | — |
| **Plan** | Numbered steps, exact file paths, schema/type changes | — |
| **Verification** | How to know it's done (tests, build, manual check) | — |
| **Decisions Made** | Architecture/design choices made during implementation | `decisions[]` of nearest index.md |
| **Context** | Why this approach was chosen, tradeoffs considered | Body of nearest index.md |
| **Implementation Notes** | Technical details, gotchas, exact API usage | Body of nearest index.md |
| **Files Changed** | List of files created or modified with brief rationale | `links[]` of nearest index.md |

Keep it short — 30–60 lines total. The first 3 sections guide execution; the last 4 feed the shard.

**3. Implement**
Patch existing files with `patch`, create new files with `write_file`.

Before coding, read the target module's `index.md` to respect existing `decisions[]`.

**If `delegate=true`:**
1. Dispatch a `delegate_task` with:
   - The full plan text in `context`
   - The module's `index.md` decisions in `context`
   - `.cns/design/index.md` and `.cns/architecture/index.md` excerpts if relevant
   - Explicit instruction: "Implement, test, and commit the code. Do NOT shard or modify CNS files."
2. **Parent agent waits for subagent return**, then:
   - Run tests to validate subagent work
   - Run build to validate subagent work
   - If tests fail, fix or re-delegate; do not proceed to CNS maintenance
   - If tests pass, proceed to Step 6 (shard)
   - The subagent's commit is the code commit; parent skips Step 5

**If `delegate=false` (default):**
Implement directly, then continue to Step 4.

**4. Verify (direct mode only)**
Run the project's test command (e.g., `bun test`, `pytest`). Run the build command. Both must pass.

**5. Commit code and CNS atomically (direct mode only)**
Stage all changes — code, plans, sharded index.md files, intent.md, log.md — in a single commit:
```bash
git add -A
git commit -m "type(scope): task-NN description"
```
Use conventional commits. Code changes and CNS maintenance (shard + bubble + validate + log) must never be split into separate commits. They are one logical unit.

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

**11. Push**
```bash
git push
```

## When to Delegate

| Scenario | Direct | Delegate |
|----------|--------|----------|
| Task touches 1–2 files you understand | ✓ | — |
| Task is in a module you've been working in | ✓ | — |
| Task is large (≥3 files, complex logic) | — | ✓ |
| Task is UI-heavy (React components, styling) | — | ✓ |
| Task is in an unfamiliar module | — | ✓ |
| User explicitly asked to delegate | — | ✓ |
| Multiple independent tasks can run in parallel | — | ✓ (batch) |

## Delegation Context Template

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

## Anti-Patterns

- **Skipping tests.** A red test means the task is not done.
- **Forgetting the CNS health gate.** validate.py + graph.py --check must pass before push.
- **Delegating by default.** Use direct implementation for small, familiar tasks to avoid coordination overhead.
- **Not reading module index.md before coding.** Violating existing decisions is expensive to fix.
- **Skipping the shard step.** Decisions that live only in commit messages are lost to the graph.
- **Writing giant plans.** One plan per task. The intent file is the umbrella; plan files are execution units.

## Pitfalls

- **HTML entity encoding.** Subagents or previous sessions may write `&lt;`, `&gt;`, `&amp;gt;` instead of literal characters. If tests fail with syntax errors in new files, check for entity encoding.
- **Subagent interruption.** If a `delegate_task` subagent is interrupted, verify state with `git status`, check files, and run tests before deciding to resume or re-implement.
- **Stale graph.json.** After shard/bubble, always re-run `extract.py` and `graph.py --check`. A stale graph breaks downstream queries.
- **Dirty working tree.** If `git status` shows uncommitted changes before starting a task, commit or stash them first.

---

## Appendix: Sub-Procedure Quick Reference

An agent running this pipeline should not need to hunt through separate action files. The condensed versions of the sub-procedures are inlined here.

### shard(source_path)

1. Read the plan file at `source_path`.
2. Extract the 4 shardable sections: **Decisions Made**, **Context**, **Implementation Notes**, **Files Changed**.
3. For each section, determine the nearest module `index.md`:
   - Use the file paths listed in **Files Changed** to map to directories.
   - If no `index.md` exists in that directory, create one with basic frontmatter (`title`, `type: module`).
4. Route content:
   - **Decisions Made** → append to `decisions[]` with `author: agent`, `date: today`, `id: DEC-NNN`.
   - **Context** → synthesize 1–3 sentences, append to agent-authored body.
   - **Implementation Notes** → synthesize 1–3 sentences, append to agent-authored body.
   - **Files Changed** → append to `links[]` with `id` and `path`.
5. Delete the plan file — its content now lives in the graph.

### bubble(path)

1. Read the `index.md` at `path`.
2. Run `bubble.py` to analyze the parent chain: `python3 ~/.hermes/skills/nervous-system/scripts/bubble.py <project_root> <path>`.
3. Determine if the change is externally relevant (public API, significant decision, new module).
4. If yes: synthesize a 1–3 sentence summary written from the parent's perspective.
5. Walk the parent chain upward. At each parent, insert the summary into the agent-authored body if not already present.
6. Stop at `.cns/index.md` or when the change is purely local.

### validate

```bash
python3 ~/.hermes/skills/nervous-system/scripts/validate.py <project_root>
python3 ~/.hermes/skills/nervous-system/scripts/graph.py <project_root> --check
```
Both must pass (exit code 0). If either fails, fix CNS issues before proceeding.

### log

Append to `.cns/log.md`:
```markdown
## YYYY-MM-DD

### HH:MM — Task NN completed
- Decision DEC-XXX added to src/.../index.md
- File src/.../foo.ts implemented and tested
- Tests: X pass, 0 fail
```