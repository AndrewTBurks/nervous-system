# Action: plan

Collaboratively populate `.cns/intent.md` with the next phase of work. This is **Mode B** — the human and agent decide what to build before anything is implemented.

## When to use

- Human says *"what should we do next?"*
- Human says *"let's plan phase 5"*
- Human says *"add these items to the backlog"*
- After `explore` or `reconcile` surfaces new work that needs scheduling

## Steps

**1. Traverse current state**
Run `traverse(root)` to build context: read `.cns/index.md`, key module `index.md` files, and `.cns/log.md` to understand what has been done.

**2. Read intent.md**
Check existing planned work to avoid duplication and understand current priorities.

**3. Propose tasks**
Present a prioritized list of suggested tasks to the human:
```markdown
## Proposed tasks for Phase X

- [ ] TASK-21: Implement foo bar (src/engine/foo.ts)
- [ ] TASK-22: Add baz validation (src/types/baz.ts)
- [ ] TASK-23: Wire up UI component (components/Baz/Baz.tsx)
```

For each task, include:
- One-line description
- Estimated scope (files touched)
- Any known dependencies on prior tasks

**4. Human reviews**
Human approves, rejects, reorders, or modifies tasks. Iterate until agreement.

**5. Write to intent.md**
Append approved tasks to `.cns/intent.md` using the format:
```markdown
## Phase X: Name

- [ ] TASK-NN: description
```

**Rules for intent.md format:**
- Group by phase or area (e.g., `## Phase 5: Productionization`)
- Each task is a bullet with an ID: `- [ ] TASK-NN: description`
- Tasks should be small enough for one plan file (1–3 files preferred, max 5)
- `intent.md` is **only forward-looking** — never mark tasks done, delete them when completed

**6. Bubble if needed**
If planning surfaces new architectural or design decisions, update the relevant central node via `explore` and bubble.

**7. Commit**
```bash
git add -A
git commit -m "docs(cns): plan Phase X tasks in intent.md"
```

## Notes

- Planning is a collaborative loop, not a single-shot generation. The human has final say on priorities and scope.
- Tasks in `intent.md` are the input to `execute-task`. A task should be concrete enough to write a 10–30 line plan for.
- If the human wants to skip planning and go straight to execution, read `intent.md` and proceed with `execute-task` on the next available task.