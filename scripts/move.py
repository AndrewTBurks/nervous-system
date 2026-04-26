#!/usr/bin/env python3
"""
move.py — Move a CNS node or directory, rebase all affected links.

Always runs in dry-run mode unless --execute is passed.
Shows all planned changes before executing so the LLM can review and approve.

USAGE:
    move.py <project_root> <old_path> <new_path>         # dry-run
    move.py <project_root> <old_path> <new_path> --execute   # actually move

<old_path> and <new_path> are relative to the project root.
Both must be inside .cns/ OR both must be outside .cns/ (e.g. in src/).

EXAMPLES:
    move.py . src/engine src/core/engine      # move a code dir + update CNS links
    move.py . .cns/architecture .cns/sys/architecture  # move a CNS node
    move.py . src/engine src/core/engine --execute
"""

import argparse
import os
import re
import shutil
import sys
import yaml
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).parent))
from shared import section, field, item, kv, header, resolve_link, find_all_docs


# ── Frontmatter helpers ───────────────────────────────────────────────────────

def load_frontmatter(md_path: Path) -> dict[str, Any]:
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
        return yaml.safe_load(parts[1]) or {}
    except Exception:
        return {}


def save_frontmatter(md_path: Path, body: str, fm: dict[str, Any]) -> None:
    fm_text = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True)
    content = f"---\n{fm_text}---\n{body}"
    md_path.write_text(content, encoding="utf-8")


def split_frontmatter(md_path: Path) -> tuple[dict[str, Any], str]:
    content = md_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    fm = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return fm, body


# ── Link resolution ───────────────────────────────────────────────────────────

def resolve_link_path(link_path: str, source_file: Path, project_root: Path) -> Path:
    """
    Resolve a links[] path as stored in frontmatter.

    Convention: links[] paths are relative to the PROJECT ROOT, not the source file.
    E.g. in .cns/architecture/index.md, link "src/engine/index.md" means
    the file at {project_root}/src/engine/index.md.

    Some existing CNS links use .cns/-relative paths (e.g. links to other CNS nodes),
    which also resolve correctly from project root.
    """
    # Treat as relative to project root
    return (project_root / link_path).resolve()


def rebase_link(link_path: str, source_file: Path, project_root: Path,
                old_abs: Path, new_path: str) -> tuple[bool, str]:
    """
    Check if a link needs rebasing when the subtree moved from old_abs to new_path.

    old_abs must be ALREADY RESOLVED. new_path is the relative target path from project root.
    """
    abs_target = resolve_link_path(link_path, source_file, project_root)

    # Check if target is inside the old subtree
    try:
        rel_to_old = abs_target.relative_to(old_abs)
        is_inside = True
    except ValueError:
        is_inside = False

    if not is_inside:
        return False, link_path

    # Rebase: replace old subtree prefix with new subtree prefix (as relative path)
    new_link = str(Path(new_path) / rel_to_old)
    return True, new_link


# ── Path helpers ─────────────────────────────────────────────────────────────

def get_body(md_path: Path) -> str:
    content = md_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content
    return parts[2]


# ── Move planner ─────────────────────────────────────────────────────────────

def plan_move(old_path: str, new_path: str, root: Path) -> dict:
    """
    Compute everything that needs to happen to move old_path to new_path.
    Returns a dict of planned operations.
    """
    project_root = (root / ".cns" / "..").resolve()
    old_abs = (project_root / old_path).resolve()
    new_abs = (project_root / new_path).resolve()
    old_abs_str = str(old_abs)
    new_abs_str = str(new_abs)

    # Find all nervous-system nodes
    all_nodes = find_all_docs(root)

    # Classify nodes: moved_subtree vs external
    moved_nodes: list[Path] = []
    external_nodes: list[Path] = []
    for md in all_nodes:
        try:
            md.relative_to(old_abs)
            moved_nodes.append(md)
        except ValueError:
            external_nodes.append(md)

    operations: dict[str, list[dict]] = {
        "move_files": [],      # CNS files to physically move
        "update_moved": [],    # Updates to frontmatter of moved files
        "update_external": [],  # Updates to frontmatter of external files
        "exec_order": [],       # Ordered list of operation descriptions
    }

    # 1. Plan physical move
    for md in moved_nodes:
        rel = str(md.relative_to(old_abs))
        new_md = new_abs / rel
        operations["move_files"].append({
            "from": str(md.relative_to(root)),
            "to": str(new_md.relative_to(root)),
        })
        operations["exec_order"].append({
            "type": "MOVE",
            "from": str(md.relative_to(root)),
            "to": str(new_md.relative_to(root)),
        })

    # 2. For each moved node: update parent + internal links
    for md in moved_nodes:
        rel = str(md.relative_to(root))
        rel_new = rel.replace(old_path, new_path, 1)

        md_ops: dict[str, Any] = {"file": rel, "updates": []}

        fm, body = split_frontmatter(md)

        # Check parent — does it point upward out of the subtree?
        parent_rel = fm.get("parent")
        if parent_rel:
            parent_abs = (md.parent / parent_rel).resolve()
            try:
                parent_abs.relative_to(old_abs)
                # Parent is inside the old subtree — needs update
                rel_to_old = parent_abs.relative_to(old_abs)
                new_parent_abs = (new_abs / rel_to_old).resolve()
                new_md = new_abs / md.relative_to(old_abs)
                new_parent_rel = os.path.relpath(str(new_parent_abs), str(new_md.parent))
                md_ops["updates"].append({
                    "field": "parent",
                    "old": parent_rel,
                    "new": new_parent_rel,
                    "note": "parent moved with subtree",
                })
            except ValueError:
                # Parent is outside — no change needed
                pass

        # Check links — do any point into the old subtree?
        links = fm.get("links", [])
        if isinstance(links, list):
            for i, entry in enumerate(links):
                link_path = entry if isinstance(entry, str) else entry.get("path", "")
                if not link_path:
                    continue
                needs_change, new_link = rebase_link(
                    link_path, md, project_root, old_abs, new_path
                )
                if needs_change:
                    entry_copy = dict(entry) if isinstance(entry, dict) else {"path": link_path}
                    if isinstance(entry, str):
                        entry_copy = new_link
                    else:
                        entry_copy["path"] = new_link
                    md_ops["updates"].append({
                        "field": "links",
                        "index": i,
                        "old": link_path,
                        "new": new_link,
                    })

        if md_ops["updates"]:
            operations["update_moved"].append(md_ops)
            operations["exec_order"].append({
                "type": "UPDATE_FRONTMATTER",
                "file": rel_new,
                "updates": md_ops["updates"],
            })

    # 3. For each external node: check if any links point into old subtree
    for md in external_nodes:
        rel = str(md.relative_to(root))
        fm, body = split_frontmatter(md)
        links = fm.get("links", [])
        link_updates: list[dict] = []

        if isinstance(links, list):
            for i, entry in enumerate(links):
                link_path = entry if isinstance(entry, str) else entry.get("path", "")
                if not link_path:
                    continue
                needs_change, new_link = rebase_link(
                    link_path, md, project_root, old_abs, new_path
                )
                if needs_change:
                    link_updates.append({
                        "index": i,
                        "old": link_path,
                        "new": new_link,
                    })

        if link_updates:
            operations["update_external"].append({
                "file": rel,
                "updates": link_updates,
            })
            operations["exec_order"].append({
                "type": "UPDATE_EXTERNAL",
                "file": rel,
                "updates": link_updates,
            })

    # 4. Validation step
    operations["exec_order"].append({
        "type": "VALIDATE",
        "note": "python3 ~/.hermes/skills/nervous-system/scripts/validate.py {root}",
    })
    operations["exec_order"].append({
        "type": "GRAPH_CHECK",
        "note": "python3 ~/.hermes/skills/nervous-system/scripts/graph.py {root} --check",
    })

    return operations


def execute_move(operations: dict, root: Path) -> list[str]:
    """
    Execute all operations in order.
    Returns list of log messages.
    """
    log: list[str] = []
    project_root = root / ".cns" / ".."

    for op in operations["exec_order"]:
        if op["type"] == "MOVE":
            src = root / op["from"]
            dst = root / op["to"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            log.append(f"MOVED: {op['from']} -> {op['to']}")

        elif op["type"] == "UPDATE_FRONTMATTER":
            md_path = root / op["file"]
            if not md_path.exists():
                # File was moved, use new path
                pass
            fm, body = split_frontmatter(md_path)
            for upd in op["updates"]:
                if upd["field"] == "parent":
                    fm["parent"] = upd["new"]
                elif upd["field"] == "links":
                    idx = upd["index"]
                    links = fm.get("links", [])
                    if isinstance(links[idx], str):
                        links[idx] = upd["new"]
                    else:
                        links[idx]["path"] = upd["new"]
            save_frontmatter(md_path, body, fm)
            log.append(f"UPDATED: {op['file']} — {len(op['updates'])} change(s)")

        elif op["type"] == "UPDATE_EXTERNAL":
            md_path = root / op["file"]
            fm, body = split_frontmatter(md_path)
            for upd in op["updates"]:
                idx = upd["index"]
                links = fm.get("links", [])
                if isinstance(links[idx], str):
                    links[idx] = upd["new"]
                else:
                    links[idx]["path"] = upd["new"]
            save_frontmatter(md_path, body, fm)
            log.append(f"UPDATED: {op['file']} — {len(op['updates'])} link(s) rebased")

    return log


# ── Output formatters ────────────────────────────────────────────────────────

def format_plan(operations: dict, old_path: str, new_path: str, as_json: bool = False) -> str:
    if as_json:
        import json
        return json.dumps({
            "old": old_path,
            "new": new_path,
            "operations": operations,
        }, indent=2, default=str)

    lines = [section("move", f"{old_path}  ->  {new_path}")]

    lines.append(field("moved_files", str(len(operations["move_files"]))))
    lines.append(field("moved_frontmatter_updates", str(len(operations["update_moved"]))))
    lines.append(field("external_frontmatter_updates", str(len(operations["update_external"]))))
    lines.append("")

    if operations["move_files"]:
        lines.append("move_files:")
        for f in operations["move_files"]:
            lines.append(f"  {f['from']}  ->  {f['to']}")

    if operations["update_moved"]:
        lines.append("")
        lines.append("update_moved_files:")
        for u in operations["update_moved"]:
            lines.append(f"  {u['file']}:")
            for upd in u["updates"]:
                lines.append(f"    {upd['field']}: '{upd['old']}' -> '{upd['new']}'")

    if operations["update_external"]:
        lines.append("")
        lines.append("update_external_files:")
        for u in operations["update_external"]:
            lines.append(f"  {u['file']}:")
            for upd in u["updates"]:
                lines.append(f"    links[{upd['index']}]: '{upd['old']}' -> '{upd['new']}'")

    lines.append("")
    lines.append("exec_order:")
    for i, op in enumerate(operations["exec_order"], 1):
        if op["type"] == "MOVE":
            lines.append(f"  [{i}] MOVE {op['from']} -> {op['to']}")
        elif op["type"] == "UPDATE_FRONTMATTER":
            lines.append(f"  [{i}] UPDATE {op['file']} ({len(op['updates'])} change(s))")
        elif op["type"] == "UPDATE_EXTERNAL":
            lines.append(f"  [{i}] UPDATE_EXTERNAL {op['file']} ({len(op['updates'])} link(s))")
        elif op["type"] == "VALIDATE":
            lines.append(f"  [{i}] VALIDATE")
        elif op["type"] == "GRAPH_CHECK":
            lines.append(f"  [{i}] GRAPH_CHECK")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Move a CNS node or directory with link rebasing.")
    parser.add_argument("project_root", type=Path, default=Path.cwd())
    parser.add_argument("old_path", nargs="?", default=None)
    parser.add_argument("new_path", nargs="?", default=None)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = args.project_root.resolve()
    if not (root / ".cns").is_dir():
        print(f"Error: {root}/.cns/ not found", file=sys.stderr)
        return 1

    if not args.old_path or not args.new_path:
        print("Error: both <old_path> and <new_path> are required", file=sys.stderr)
        return 1

    project_root = root / ".cns" / ".."
    old_abs = project_root / args.old_path
    new_abs = project_root / args.new_path

    if not old_abs.exists():
        print(f"Error: {args.old_path} does not exist", file=sys.stderr)
        return 1
    if new_abs.exists():
        print(f"Error: {args.new_path} already exists", file=sys.stderr)
        return 1

    # Both must be inside .cns/ OR both outside
    old_in_cns = args.old_path.startswith(".cns/")
    new_in_cns = args.new_path.startswith(".cns/")
    if old_in_cns != new_in_cns:
        print("Error: old_path and new_path must both be inside .cns/ or both outside", file=sys.stderr)
        return 1

    operations = plan_move(args.old_path, args.new_path, root)

    if args.json:
        print(format_plan(operations, args.old_path, args.new_path, as_json=True))
        return 0

    print(format_plan(operations, args.old_path, args.new_path, as_json=False))

    if args.execute:
        print("\n[EXECUTING]")
        log = execute_move(operations, root)
        for msg in log:
            print(f"  {msg}")
    else:
        print("\n[Dry-run — pass --execute to perform the move]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
