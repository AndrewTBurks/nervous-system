---
name: nervous-system
description: "Use when a project has a .cns/ directory or when the user invokes /nervous-system. Provides a command-driven workflow for a persistent project knowledge layer: bootstrap, status, plan, execute, shard, audit, health, and repair, with deterministic preflights and CNS validation gates."
version: "2.0.0"
author: Andrew Burks
license: MIT
metadata:
  hermes:
    tags: [project-context, knowledge-graph, planning, execution, documentation]
    related_skills: [impeccable, subagent-driven-development, systematic-debugging]
---

# Nervous System

A persistent, living knowledge layer for software projects. A CNS project stores human-editable intent, architecture, design, product, research, module notes, decisions, and activity logs alongside the codebase. The agent maintains that layer as part of normal work.

This skill is command-driven. Treat `/nervous-system <command>` like `/impeccable <command>`: run the command preflight first, use deterministic scripts where possible, then perform the LLM judgment step only after the project state is grounded.

## Command grammar

| Command | Purpose | Procedure |
|---|---|---|
| `/nervous-system` | Detect CNS state and route the user to the right command. | `references/command-status.md` |
| `/nervous-system status` | Summarize project CNS health, git state, pending intent, plans, and graph state. | `references/command-status.md` |
| `/nervous-system bootstrap` | Initialize `.cns/` for a project that does not already have one. | `references/command-bootstrap.md` |
| `/nervous-system explore [topic]` | Read or update central architecture/design/product/research knowledge. | `references/command-explore.md` |
| `/nervous-system plan` | Interview the user and write approved future work into `.cns/intent.md`. | `references/command-plan.md` |
| `/nervous-system execute next` | Execute the next pending intent task, one task at a time. | `references/command-execute.md` |
| `/nervous-system execute TASK-ID` | Execute a specific task from `.cns/intent.md`. | `references/command-execute.md` |
| `/nervous-system execute all` | Sequentially execute pending tasks. Never parallelize unless the user explicitly asks. | `references/command-execute.md` |
| `/nervous-system shard <source>` | Distribute resolved plan/intent decisions into CNS nodes and module `index.md` files. | `references/command-shard.md` |
| `/nervous-system audit [path]` | Compare CNS claims and decisions against the actual code. | `references/command-audit.md` |
| `/nervous-system health` | Run deterministic CNS validation and graph checks. | `references/command-health.md` |
| `/nervous-system repair` | Diagnose and fix CNS validation, graph, or schema failures. | `references/command-repair.md` |

If the user invokes `/nervous-system` without a command:

1. Run the common preflight in `references/preflight-common.md`.
2. If `.cns/` is absent, offer or run `bootstrap` depending on the user's wording.
3. If `.cns/` exists, run `status` and route based on intent:
   - architecture/design/product question → `explore`
   - upcoming work/task intake → `plan`
   - implementation request → `execute`
   - validation/graph issue → `health` or `repair`
   - decision/code conformance question → `audit`

## Universal preflight

Before any command that reads or writes CNS state:

1. Locate the project root: current directory if it contains `.cns/`, otherwise walk upward.
2. Check git state: `git status --short --branch`.
3. Check git identity before any commit: `git config user.name` and `git config user.email`. If either is unset, ask; never invent a placeholder identity.
4. Check runtime if scripts will run: `python3 --version`; verify PyYAML for scripts that import `yaml`.
5. Detect `.cns/`: if absent, only `bootstrap` is valid.
6. Ensure `.cns/graph.json` exists. If missing or stale, run `scripts/extract.py <project_root>` before graph-dependent work.
7. Before writing `intent.md`, `log.md`, or any shared CNS file: read the current file immediately before patching, write, then read it back to verify. Serialize writes when sibling subagents are active.

Full details: `references/preflight-common.md`.

## Non-negotiable CNS rules

- Preserve human-owned zones. Never rewrite `human_notes` except at explicit user direction.
- Completed intent tasks stay visible in `.cns/intent.md` with done markers. Do not delete them as cleanup.
- Durable design decisions belong in frontmatter `decisions[]`, not only in body prose.
- `links[]` paths are project-root-relative, not file-relative.
- Run the CNS health gate after CNS writes: `validate.py` and `graph.py --check` must pass before declaring CNS work complete.
- Do not delete plan files without explicit confirmation in the same session, even when they appear stale.
- Execute tasks sequentially by default. One task finishes, validates, commits, and logs before the next begins.
- Surface `JUDGMENT CALL`, `decision required`, and `ask the user` markers before implementation, not in the recap.

## Deterministic script surface

Prefer the wrapper when available:

```bash
python3 <skill_dir>/scripts/cns.py health <project_root>
python3 <skill_dir>/scripts/cns.py status <project_root>
python3 <skill_dir>/scripts/cns.py bootstrap <project_root>
```

Direct scripts remain available:

| Script | Purpose |
|---|---|
| `scripts/bootstrap.py` | Initialize `.cns/` skeleton. |
| `scripts/extract.py` | Build `.cns/graph.json`. |
| `scripts/validate.py` | Validate CNS frontmatter and links. |
| `scripts/graph.py` | Check graph freshness, orphans, cycles, dangling links. |
| `scripts/query.py` | List/filter CNS nodes. |
| `scripts/search.py` | Search CNS content. |
| `scripts/bubble.py` | Show bubble chain for a node. Argument order is project root first, node second. |
| `scripts/link.py` | Show outgoing and incoming links. |
| `scripts/move.py` | Move CNS nodes and rebase links. |

Resolve `<skill_dir>` to this skill's installed directory. Do not assume a hardcoded `~/.hermes` path in public instructions.

## Supporting docs

| Area | File |
|---|---|
| Common command preflight | `references/preflight-common.md` |
| Command procedures | `references/command-*.md` |
| Internal CNS actions | `actions/*.md` |
| Schema and node rules | `references/schema.md` and `schema.md` |
| Plan lifecycle | `references/plan-lifecycle.md` |
| Intent retention and task writing | `references/intent-retention.md` |
| PNS node creation/splitting | `references/pns-node-rules.md` |
| Graph maintenance | `references/graph-maintenance.md` |

Load supporting docs only when the command requires them. The default skill payload should stay small enough to act as a clear router.

## Verification checklist

Before reporting completion of CNS work:

- [ ] Project root identified.
- [ ] Git state known.
- [ ] Git identity checked before commits.
- [ ] Command-specific preflight completed.
- [ ] All CNS writes read back and verified.
- [ ] `python3 <skill_dir>/scripts/validate.py <project_root>` passed.
- [ ] `python3 <skill_dir>/scripts/graph.py <project_root> --check` passed.
- [ ] Intent/log updated when task work was completed.
- [ ] Changes committed with the configured git identity when the user asked for committed work.
