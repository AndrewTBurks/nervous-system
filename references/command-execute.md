# /nervous-system execute

## Purpose

Execute intent tasks through implementation, verification, CNS update, commit, and optional push.

## Preflight

1. Run common preflight.
2. Read `.cns/intent.md` in full.
3. Select the task: `next`, explicit `TASK-ID`, or all pending tasks sequentially.
4. Scan the selected task for `JUDGMENT CALL`, `decision required`, or `ask the user` markers.
5. If a judgment call exists, ask before implementing.
6. Check git identity before any commit.
7. Run current health so pre-existing CNS failures are known.

## Procedure for one task

1. Create or read an ephemeral plan if the task needs one.
2. Implement the code/docs change.
3. Run project-specific tests/build/lint.
4. Run CNS health.
5. Commit code changes.
6. Mark intent task done and append `.cns/log.md` entry.
7. Commit CNS docs update separately when appropriate.
8. Push only when the user requested or repository workflow expects it.

## Execute all

Run the one-task procedure sequentially. Do not parallelize by default. Stop on the first failed test, failed health gate, judgment call, or unclear task boundary.

## Output

For each task: files changed, tests run, CNS health result, commit(s), and next task status.
