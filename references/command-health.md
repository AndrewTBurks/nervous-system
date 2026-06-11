# /nervous-system health

## Purpose

Run deterministic CNS validation. This command should not require LLM judgment except to explain failures.

## Procedure

```bash
python3 <skill_dir>/scripts/extract.py <project_root>
python3 <skill_dir>/scripts/validate.py <project_root>
python3 <skill_dir>/scripts/graph.py <project_root> --check
```

Or through the wrapper:

```bash
python3 <skill_dir>/scripts/cns.py health <project_root>
```

## Output

- extract result
- validate result
- graph result
- exact failing files/links if any
- recommended repair command or patch plan
