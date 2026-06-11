#!/usr/bin/env python3
"""
validate.py — CNS frontmatter validator.

Checks nervous-system Markdown nodes for:
  1. Valid YAML frontmatter.
  2. Required fields: title, type.
  3. decisions[] entries with id/date/author/summary.
  4. links[] entries that point to existing project-root-relative files.

Exit code 0 = pass, 1 = fail.
"""

import argparse
import sys
from pathlib import Path
from typing import List

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by runtime environments
    print("PyYAML is required. Install with: python3 -m pip install PyYAML", file=sys.stderr)
    sys.exit(2)

sys.path.insert(0, str(Path(__file__).parent))
from shared import find_all_docs

ERRORS: List[str] = []


def fatal(msg: str) -> None:
    ERRORS.append(msg)


def validate_frontmatter(rel_path: Path, content: str, root: Path) -> None:
    """Parse and validate the YAML frontmatter of a single .md file."""
    if not content.startswith("---"):
        fatal(f"{rel_path}: no YAML frontmatter (missing opening ---)")
        return

    parts = content.split("---", 2)
    if len(parts) < 3:
        fatal(f"{rel_path}: cannot parse frontmatter (missing closing ---)")
        return
    fm_text = parts[1]

    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        fatal(f"{rel_path}: YAML error: {e}")
        return

    if not isinstance(fm, dict):
        fatal(f"{rel_path}: frontmatter is not a YAML dict")
        return

    if "title" not in fm:
        fatal(f"{rel_path}: missing required field 'title'")
    if "type" not in fm:
        fatal(f"{rel_path}: missing required field 'type'")

    decisions = fm.get("decisions", [])
    if decisions is None:
        decisions = []
    if not isinstance(decisions, list):
        fatal(f"{rel_path}: 'decisions' must be a list")
    else:
        seen_ids = set()
        for i, entry in enumerate(decisions):
            if not isinstance(entry, dict):
                fatal(f"{rel_path}: decisions[{i}] is not a dict")
                continue
            for field_name in ("id", "date", "author", "summary"):
                if field_name not in entry:
                    fatal(f"{rel_path}: decisions[{i}] missing '{field_name}'")
            if "id" in entry:
                rid = str(entry["id"])
                if rid in seen_ids:
                    fatal(f"{rel_path}: duplicate decision id '{rid}'")
                seen_ids.add(rid)

    links = fm.get("links", [])
    if links is None:
        links = []
    if not isinstance(links, list):
        fatal(f"{rel_path}: 'links' must be a list")
    else:
        project_root = root
        for i, entry in enumerate(links):
            if not isinstance(entry, dict):
                fatal(f"{rel_path}: links[{i}] is not a dict")
                continue
            if "path" not in entry:
                fatal(f"{rel_path}: links[{i}] missing 'path'")
                continue
            link_path = entry["path"]
            resolved = (project_root / str(link_path)).resolve()
            if not resolved.exists():
                fatal(f"{rel_path}: links[{i}] points to nonexistent file '{link_path}'")


def walk_cns(root: Path) -> int:
    """Walk CNS and PNS and validate every nervous-system document."""
    cns = root / ".cns"
    if not cns.is_dir():
        fatal(f"{root}: .cns/ directory not found")
        return 1

    skip_names = {"log.md", "intent.md"}
    md_files = find_all_docs(root)
    if not md_files:
        print(f"{root}: no nervous-system documents found")
        return 0

    for md_path in md_files:
        rel = md_path.relative_to(root)
        if rel.name in skip_names:
            continue
        if ".cns" in rel.parts and "plans" in rel.parts:
            continue
        try:
            content = md_path.read_text(encoding="utf-8")
        except Exception as e:
            fatal(f"{rel}: cannot read: {e}")
            continue
        validate_frontmatter(rel, content, root)

    return 1 if ERRORS else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate CNS frontmatter and project-root-relative links.")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root containing .cns/ (default: current directory)")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    print(f"Validating CNS at: {project_root}")

    exit_code = walk_cns(project_root)

    if ERRORS:
        print(f"\n{len(ERRORS)} error(s):")
        for err in ERRORS:
            print(f"  - {err}")
        print("\nvalidate.py FAILED")
    else:
        print("validate.py PASSED")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
