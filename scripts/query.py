#!/usr/bin/env python3
"""
query.py — List and filter CNS nodes by type, status, author, date range.

USAGE:
    query.py <project_root> [options]

OPTIONS:
    --type TYPE         Filter by type (project, component, service, module, package)
    --status STATUS     Filter by status (clean, dirty, reconciling)
    --author AUTHOR     Show only decisions by this author
    --after DATE        ISO date string — show decisions after this date
    --before DATE       ISO date string — show decisions before this date
    --category CAT      Filter intents by category (feature, bug, refactor, research, exploration)
    --intent-status S   Filter intents by status (pending, in_progress, completed, cancelled)
    --no-parent         Show nodes with no parent field
    --with-intents      Show only nodes that have intents[]
    --with-decisions    Show only nodes that have decisions[]
    --json              Machine-readable JSON output
    --fields F1,F2      Comma-separated fields to include in output (default: path,title,type,status)

    --list-types        Show all unique type values found
    --list-statuses     Show all unique status values found
    --list-authors      Show all unique decision authors found

EXAMPLES:
    query.py /path/to/project
    query.py /path/to/project --type project
    query.py /path/to/project --status dirty
    query.py /path/to/project --author agent
    query.py /path/to/project --category feature --intent-status pending
    query.py /path/to/project --no-parent
    query.py /path/to/project --json
    query.py /path/to/project --list-authors
"""

import sys
import json
import argparse
import yaml
from pathlib import Path
from datetime import datetime
from typing import Any, Optional


DEFAULT_FIELDS = ["path", "title", "type", "status"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query CNS nodes.")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--type")
    parser.add_argument("--status")
    parser.add_argument("--author")
    parser.add_argument("--after")
    parser.add_argument("--before")
    parser.add_argument("--category")
    parser.add_argument("--intent-status")
    parser.add_argument("--no-parent", action="store_true")
    parser.add_argument("--with-intents", action="store_true")
    parser.add_argument("--with-decisions", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fields", default=",".join(DEFAULT_FIELDS))
    parser.add_argument("--list-types", action="store_true")
    parser.add_argument("--list-statuses", action="store_true")
    parser.add_argument("--list-authors", action="store_true")
    return parser.parse_args()


def load_node(md_path: Path) -> dict[str, Any]:
    """Load frontmatter + minimal info from a .md file."""
    try:
        content = md_path.read_text(encoding="utf-8")
    except Exception:
        return {}

    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    try:
        fm = yaml.safe_load(parts[1])
    except Exception:
        return {}

    if not isinstance(fm, dict):
        return {}

    fm["_path"] = str(md_path)
    return fm


def decision_matches(d: dict, author: str, after: datetime, before: datetime) -> bool:
    if author and d.get("author") != author:
        return False
    date_str = d.get("date", "")
    try:
        d_date = datetime.fromisoformat(date_str)
    except Exception:
        return False
    if after and d_date < after:
        return False
    if before and d_date > before:
        return False
    return True


def intent_matches(i: dict, category: str, istatus: str) -> bool:
    if category and i.get("category") != category:
        return False
    if istatus and i.get("status") != istatus:
        return False
    return True


def node_matches(
    fm: dict,
    opts: argparse.Namespace,
    after_dt: Optional[datetime], before_dt: Optional[datetime]
) -> bool:
    if opts.type and fm.get("type") != opts.type:
        return False
    if opts.status and fm.get("status") != opts.status:
        return False
    if opts.no_parent and "parent" in fm:
        return False
    if opts.with_intents and not fm.get("intents"):
        return False
    if opts.with_decisions and not fm.get("decisions"):
        return False

    # Author / date filters apply to decisions in this node
    if (opts.author or opts.after or opts.before) and fm.get("decisions"):
        if not any(
            decision_matches(d, opts.author or "", after_dt, before_dt)
            for d in fm["decisions"]
        ):
            return False

    # Intent filters
    if (opts.category or opts.intent_status) and fm.get("intents"):
        if not any(
            intent_matches(i, opts.category or "", opts.intent_status or "")
            for i in fm["intents"]
        ):
            return False

    return True


def extract_values(nodes: list[dict], field: str) -> set[str]:
    """Extract unique values for a field across all nodes."""
    vals = set()
    for n in nodes:
        if field == "type":
            vals.add(n.get("type", ""))
        elif field == "status":
            vals.add(n.get("status", ""))
        elif field == "author":
            for d in n.get("decisions", []):
                if a := d.get("author"):
                    vals.add(a)
        elif field == "decision_count":
            vals.add(str(len(n.get("decisions", []))))
        elif field == "intent_count":
            vals.add(str(len(n.get("intents", []))))
    return {v for v in vals if v}


def format_human(nodes: list[dict], fields: list[str]) -> str:
    """Tab-separated table, one node per line."""
    lines = []
    for n in nodes:
        row = []
        for f in fields:
            if f == "path":
                row.append(n.get("_path", ""))
            elif f == "title":
                row.append(n.get("title", ""))
            elif f == "type":
                row.append(n.get("type", ""))
            elif f == "status":
                row.append(n.get("status", ""))
            elif f == "decision_count":
                row.append(str(len(n.get("decisions", []))))
            elif f == "intent_count":
                row.append(str(len(n.get("intents", []))))
            elif f == "last_reconciled":
                row.append(str(n.get("last_reconciled", "")))
            elif f == "parent":
                row.append(n.get("parent", ""))
            else:
                row.append("")
        lines.append("\t".join(row))
    return "\n".join(lines)


def format_json(nodes: list[dict], fields: list[str]) -> str:
    """JSON array of node objects with requested fields."""
    out = []
    for n in nodes:
        obj = {}
        for f in fields:
            if f == "path":
                obj["path"] = n.get("_path", "")
            elif f == "title":
                obj["title"] = n.get("title", "")
            elif f == "type":
                obj["type"] = n.get("type", "")
            elif f == "status":
                obj["status"] = n.get("status", "")
            elif f == "decision_count":
                obj["decision_count"] = len(n.get("decisions", []))
            elif f == "intent_count":
                obj["intent_count"] = len(n.get("intents", []))
            elif f == "last_reconciled":
                obj["last_reconciled"] = n.get("last_reconciled", "")
            elif f == "parent":
                obj["parent"] = n.get("parent", "")
            elif f == "decisions":
                obj["decisions"] = n.get("decisions", [])
            elif f == "intents":
                obj["intents"] = n.get("intents", [])
        out.append(obj)
    return json.dumps(out, indent=2)


def main() -> int:
    args = parse_args()

    cns = args.project_root / ".cns"
    if not cns.is_dir():
        print(f"Error: {cns} not found", file=sys.stderr)
        return 1

    after_dt = datetime.fromisoformat(args.after) if args.after else None
    before_dt = datetime.fromisoformat(args.before) if args.before else None

    # Collect all nodes
    all_nodes: list[dict] = []
    for md_path in sorted(cns.rglob("*.md")):
        if md_path.name == "log.md":
            continue
        fm = load_node(md_path)
        if fm:
            all_nodes.append(fm)

    # List-* modes — operate on all nodes, no filtering
    if args.list_types:
        print(", ".join(sorted(extract_values(all_nodes, "type"))))
        return 0
    if args.list_statuses:
        print(", ".join(sorted(extract_values(all_nodes, "status"))))
        return 0
    if args.list_authors:
        print(", ".join(sorted(extract_values(all_nodes, "author"))))
        return 0

    # Filter
    filtered = [n for n in all_nodes if node_matches(n, args, after_dt, before_dt)]

    if not filtered:
        return 0

    fields = [f.strip() for f in args.fields.split(",")]

    if args.json:
        print(format_json(filtered, fields))
    else:
        print(format_human(filtered, fields))

    return 0


if __name__ == "__main__":
    sys.exit(main())
