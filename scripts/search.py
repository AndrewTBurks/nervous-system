#!/usr/bin/env python3
"""
search.py — Grep-like search across CNS markdown content.

USAGE:
    search.py <project_root> [options] [pattern]

OPTIONS:
    -i          Case-insensitive
    --json      Machine-readable JSON output
    -n          Show line numbers (default: shown)
    -C N        Show N lines of context before/after match
    --path-only Only show matching file paths (like grep -l)
    --frontmatter  Search only frontmatter
    --body      Search only body content

EXAMPLES:
    search.py /path/to/project warp
    search.py /path/to/project -i "draft"
    search.py /path/to/project --json "stub"
    search.py /path/to/project -C 2 "DES-001"
    search.py /path/to/project --path-only "threadweaver"
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grep-like search across CNS markdown content.")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("pattern", nargs="?", default=None)
    parser.add_argument("-i", "--insensitive", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-n", "--linenos", action="store_true", default=True)
    parser.add_argument("-C", "--context", type=int, default=0)
    parser.add_argument("--path-only", action="store_true")
    parser.add_argument("--frontmatter", action="store_true")
    parser.add_argument("--body", action="store_true")
    # Explicit flags after options, use -- to terminate option parsing
    args, rest = parser.parse_known_args()
    if rest:
        # Positional pattern given after -- known_args separator
        if args.pattern is None:
            args.pattern = " ".join(rest)
        else:
            args.pattern = " ".join([args.pattern] + rest)
    return args


def split_frontmatter(content: str) -> tuple[Optional[str], Optional[str]]:
    """Return (frontmatter_text, body_text) from a markdown file."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[1], parts[2]
    return None, content


def search_file(
    path: Path,
    pattern: str,
    flags: re.RegexFlag,
    context: int,
    path_only: bool,
    search_fm: bool,
    search_body: bool,
    show_lnos: bool,
) -> list[dict]:
    """Search a single file. Returns list of match dicts."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return []

    fm_text, body_text = split_frontmatter(content)

    # Determine which sections to search
    if search_fm and not search_body:
        search_in = fm_text or ""
    elif search_body and not search_fm:
        search_in = body_text or ""
    else:
        search_in = content

    if not search_in:
        return []

    matches = []
    regex = re.compile(pattern, flags)

    for lineno, line in enumerate(search_in.splitlines(), 1):
        for m in regex.finditer(line):
            match_info = {
                "path": str(path),
                "lineno": lineno,
                "line": line.rstrip(),
                "match_start": m.start(),
                "match_end": m.end(),
                "context_before": [],
                "context_after": [],
            }

            # Collect context lines
            lines = search_in.splitlines()
            for i in range(max(0, lineno - 1 - context), lineno - 1):
                match_info["context_before"].append(lines[i].rstrip())
            for i in range(lineno, min(len(lines), lineno + context)):
                match_info["context_after"].append(lines[i].rstrip())

            matches.append(match_info)

    return matches


def format_human(matches: list[dict], show_lnos: bool) -> str:
    """Human-readable output, grep-style."""
    if not matches:
        return ""

    lines = []
    for m in matches:
        if show_lnos:
            lines.append(f"{m['path']}:{m['lineno']}:{m['line']}")
        else:
            lines.append(f"{m['path']}:{m['line']}")

    return "\n".join(lines)


def format_json(matches: list[dict]) -> str:
    """Machine-readable JSON output."""
    return json.dumps(matches, indent=2)


def main() -> int:
    args = parse_args()

    if not args.pattern:
        print("Usage: search.py <project_root> [options] [pattern]", file=sys.stderr)
        return 1

    cns = args.project_root / ".cns"
    if not cns.is_dir():
        print(f"Error: {cns} not found", file=sys.stderr)
        return 1

    flags = re.IGNORECASE if args.insensitive else 0
    search_fm = args.frontmatter or not args.body  # default: search everything
    search_body = args.body or not args.frontmatter

    all_matches: list[dict] = []
    for md_path in sorted(cns.rglob("*.md")):
        # Skip log.md — it's activity log, not content
        if md_path.name == "log.md":
            continue
        matches = search_file(
            md_path,
            args.pattern,
            flags,
            args.context,
            args.path_only,
            search_fm,
            search_body,
            args.linenos,
        )
        all_matches.extend(matches)

    if not all_matches:
        return 0

    if args.json:
        print(format_json(all_matches))
    elif args.path_only:
        seen = set()
        for m in all_matches:
            if m["path"] not in seen:
                print(m["path"])
                seen.add(m["path"])
    else:
        print(format_human(all_matches, args.linenos), end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
