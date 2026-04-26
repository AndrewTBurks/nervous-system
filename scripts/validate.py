#!/usr/bin/env python3
"""
validate.py — CNS frontmatter validator.

Checks every .md file under .cns/ for:
  1. Valid YAML frontmatter (--- delimited)
  2. Required fields: title, type
  3. decisions[] entries: each has id:, date:, author:, summary:
  4. All links[] point to existing files

Run after any CNS write:
    python3 ~/.hermes/skills/nervous-system/scripts/validate.py /path/to/project

Exit code 0 = pass, 1 = fail.
"""

import sys
import yaml
from pathlib import Path

ERRORS: list[str] = []


def fatal(msg: str) -> None:
    ERRORS.append(msg)


def validate_frontmatter(rel_path: Path, content: str, root: Path) -> None:
    """Parse and validate the YAML frontmatter of a single .md file."""

    def fatal(msg: str) -> None:
        ERRORS.append(msg)

    # Parse frontmatter
    if not content.startswith("---"):
        fatal("no YAML frontmatter (missing opening ---)")
        return

    parts = content.split("---", 2)
    if len(parts) < 3:
        fatal("cannot parse frontmatter (missing closing ---)")
        return
    fm_text = parts[1]

    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        fatal(f"YAML error: {e}")
        return

    if not isinstance(fm, dict):
        fatal("frontmatter is not a YAML dict")
        return

    # Required fields
    if "title" not in fm:
        fatal("missing required field 'title'")
    if "type" not in fm:
        fatal("missing required field 'type'")

    # decisions[] entries
    decisions = fm.get("decisions", [])
    if not isinstance(decisions, list):
        fatal("'decisions' must be a list")
    else:
        seen_ids: set[str] = set()
        for i, entry in enumerate(decisions):
            if not isinstance(entry, dict):
                fatal(f"decisions[{i}] is not a dict")
                continue
            for field in ("id", "date", "author", "summary"):
                if field not in entry:
                    fatal(f"decisions[{i}] missing '{field}'")
            if "id" in entry:
                rid = str(entry["id"])
                if rid in seen_ids:
                    fatal(f"duplicate decision id '{rid}'")
                seen_ids.add(rid)

    # links[] — paths are relative to project root (where .cns/ lives)
    links = fm.get("links", [])
    if not isinstance(links, list):
        fatal("'links' must be a list")
    else:
        for i, entry in enumerate(links):
            if isinstance(entry, dict) and "path" in entry:
                link_path = entry["path"]
                # Project root = parent of .cns/
                project_root = root / ".cns" / ".."
                resolved = (project_root / link_path).resolve()
                if not resolved.exists():
                    fatal(f"links[{i}] points to nonexistent file '{link_path}'")


def walk_cns(root: Path) -> int:
    """Walk .cns/ and validate every .md file. Returns 0 on pass, 1 on fail."""
    cns = root / ".cns"
    if not cns.is_dir():
        fatal(f"{root}: .cns/ directory not found")
        return 1

    # Files that intentionally have no frontmatter
    skip_names = {"log.md", "intent.md"}

    md_files = sorted(cns.rglob("*.md"))
    if not md_files:
        print(f"{root}/.cns/: no .md files found")
        return 0

    for md_path in md_files:
        rel = md_path.relative_to(root)
        if rel.name in skip_names:
            continue
        try:
            content = md_path.read_text(encoding="utf-8")
        except Exception as e:
            fatal(f"{rel}: cannot read: {e}")
            continue
        validate_frontmatter(Path(str(rel)), content, root)

    return 1 if ERRORS else 0


def main() -> int:
    if len(sys.argv) < 2:
        project_root = Path.cwd()
    else:
        project_root = Path(sys.argv[1]).resolve()

    print(f"Validating CNS at: {project_root}")

    exit_code = walk_cns(project_root)

    if ERRORS:
        print(f"\n{len(ERRORS)} error(s):")
        for err in ERRORS:
            print(f"  - {err}")
        print(f"\nvalidate.py FAILED")
    else:
        print("validate.py PASSED")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
