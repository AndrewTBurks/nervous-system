# Action: execute-task

Run the full intent-to-ship pipeline for a single task from `.cns/intent.md`. This is **Mode C** — autonomous execution with CNS maintenance as a mandatory final phase.

## Pipeline

```
intent.md → plan → implement → test → commit → shard → bubble → validate → log → push
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | string | The task number from `.cns/intent.md` (e.g., `"16"`, `"17"`) |
| `delegate` | boolean | If true, dispatch a subagent for implementation. If false (default), implement directly. |

## Steps

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

**5. Commit code (direct mode only)**
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

- **Batching multiple tasks into one commit.** Each task gets its own commit. Code commit first, CNS commit second.
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