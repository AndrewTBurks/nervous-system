# Common CNS Preflight

Run this before any `/nervous-system` command that inspects or changes project state.

## 1. Locate project root

Use the current working directory if it contains `.cns/`; otherwise walk upward. If no `.cns/` exists, only `bootstrap` is valid unless the user explicitly asks for migration/recovery.

## 2. Git state

Run:

```bash
git status --short --branch
git config user.name
git config user.email
```

Know the branch and dirty state before editing. Before committing, use the configured identity. If identity is missing, ask; do not invent placeholder `-c user.name` or `-c user.email` flags.

## 3. Runtime

Run `python3 --version`. Public scripts support Python 3.9+. Scripts that parse frontmatter need PyYAML:

```bash
python3 - <<'PY'
import yaml
print('PyYAML OK')
PY
```

If missing, install or ask depending on environment constraints.

## 4. CNS shape

Check for:

- `.cns/index.md`
- `.cns/intent.md`
- `.cns/log.md`
- `.cns/graph.json`
- `.cns/plans/`

If graph is missing or stale, run `extract.py`.

## 5. Shared-file write discipline

Before writing `intent.md`, `log.md`, or a shared CNS node:

1. Read the current file immediately before patching.
2. Patch/write.
3. Read it back and verify the intended content landed.
4. If sibling subagents are also writing, serialize writes through the parent.

## 6. Health gate

After CNS writes:

```bash
python3 <skill_dir>/scripts/validate.py <project_root>
python3 <skill_dir>/scripts/graph.py <project_root> --check
```
