# /nervous-system status

## Purpose

Report the current CNS state without changing files. Use this for bare `/nervous-system` invocations when `.cns/` already exists.

## Preflight

Run `preflights/common.md` in read-only mode:

1. Locate project root.
2. Read git branch/status.
3. Detect `.cns/`.
4. Check whether `.cns/graph.json` exists.
5. Run deterministic health checks if they are cheap enough for the current project.

## Procedure

1. Summarize git status.
2. Summarize CNS file presence: `.cns/index.md`, `intent.md`, `log.md`, `graph.json`, `plans/`.
3. Count pending/completed intent items.
4. List open plan files, if any.
5. Run or report last result of:
   - `python3 <skill_dir>/scripts/validate.py <project_root>`
   - `python3 <skill_dir>/scripts/graph.py <project_root> --check`
6. Route the user to the next command if their request implies one.

## Output shape

```text
CNS status for <project>
- Git: <branch/status>
- Graph: fresh/stale/missing
- Intent: N pending, M completed
- Plans: N files
- Health: validate PASS/FAIL, graph PASS/FAIL
- Suggested next command: ...
```
