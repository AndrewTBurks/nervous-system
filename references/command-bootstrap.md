# /nervous-system bootstrap

## Purpose

Initialize `.cns/` for a project that does not already have one.

## Preflight

1. Locate project root.
2. If `.cns/` exists, stop and run `status` instead. Do not overwrite.
3. Search prior sessions if the user sounds like they are continuing established work, not starting fresh.
4. Check Python and PyYAML availability.
5. Check git status so created files are explicit.

## Procedure

Run:

```bash
python3 <skill_dir>/scripts/bootstrap.py <project_root>   --name "<name>"   --description "<description>"   --stack "<stack>"   --modules "<modules>"
```

Then run health:

```bash
python3 <skill_dir>/scripts/validate.py <project_root>
python3 <skill_dir>/scripts/graph.py <project_root> --check
```

## Stop conditions

- Existing `.cns/` unless the user explicitly asks for repair/migration.
- Missing project root.
- Missing runtime dependency that cannot be installed.

## Output

Report created files, health result, and next recommended command.
