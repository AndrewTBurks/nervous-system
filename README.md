# Nervous System Skill

[![skills.sh](https://skills.sh/b/AndrewTBurks/nervous-system)](https://skills.sh/AndrewTBurks/nervous-system)

A command-driven agent skill for maintaining a persistent project knowledge layer in `.cns/`.

The nervous system stores architecture, design, product context, research notes, implementation intent, decisions, graph links, and activity logs alongside the codebase. Agents use it to plan, execute, audit, reconcile, and preserve project context across sessions.

## Install

Install globally through the Skills CLI:

```bash
npx skills add AndrewTBurks/nervous-system -g -y
```

Inspect available skills in the repo without installing:

```bash
npx skills add AndrewTBurks/nervous-system --list --full-depth
```

## Commands

```text
/nervous-system
/nervous-system status
/nervous-system bootstrap
/nervous-system explore [topic]
/nervous-system plan
/nervous-system execute next
/nervous-system execute TASK-ID
/nervous-system execute all
/nervous-system shard <source>
/nervous-system audit [path]
/nervous-system health
/nervous-system repair
```

## Direct script use

Scripts are under `scripts/`. Prefer resolving them relative to the installed skill directory rather than hardcoding `~/.hermes`:

```bash
python3 <skill_dir>/scripts/cns.py health /path/to/project
python3 <skill_dir>/scripts/cns.py status /path/to/project
python3 <skill_dir>/scripts/cns.py bootstrap /path/to/project
```

## Runtime requirements

- Python 3.9+
- PyYAML for scripts that parse YAML frontmatter
- Git for commit/status workflows

Install PyYAML if missing:

```bash
python3 -m pip install PyYAML
```

## Public package shape

The default `SKILL.md` is intentionally short and command-oriented. Deeper procedures live in:

- `references/command-` — user-facing command procedures
- `references/preflight-` — deterministic checks before each command
- `actions/` — internal CNS primitives
- `references/` — schema notes, lifecycle rules, and case studies
- `scripts/` — deterministic validation and graph tooling

## Safety defaults

- Completed tasks stay visible in `.cns/intent.md`.
- Human-owned `human_notes` are preserved.
- Durable decisions live in frontmatter `decisions[]`.
- Plan files are scratch, but deletion requires explicit same-session confirmation.
- CNS health (`validate.py` + `graph.py --check`) must pass after CNS writes.
