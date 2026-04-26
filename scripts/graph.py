#!/usr/bin/env python3
"""
graph.py — Build or validate .cns/graph.json from current CNS state.

US output (default): prints a text representation of the graph.
--build:         Overwrites .cns/graph.json with the current state.
--check:         Exit 1 if graph.json is stale or missing.
--orphans:       List nodes not reachable from root (.cns/index.md).
--cycles:        List nodes involved in parent-reference cycles.
--json:          Machine-readable output for all checks.

USAGE:
    graph.py <project_root> --build
    graph.py <project_root> --check
    graph.py <project_root> --orphans
    graph.py <project_root> --cycles
    graph.py <project_root> --json
    graph.py <project_root>                    # default: text summary
"""

import sys
import json
import argparse
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).parent))
from shared import find_all_docs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Graph traversal and validation for CNS.")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--orphans", action="store_true")
    parser.add_argument("--cycles", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


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


def _resolve_parent_path(parent: str, child_path: str, root: Path, abs_path_to_node: dict[Path, str]) -> Optional[str]:
    """
    Resolve a parent field to a canonical node path string.
    Tries three forms (same logic as extract.py):
      1. child_dir / parent
      2. child_dir / parent.md
      3. child_dir / parent / index.md
    Returns the canonical node path (e.g. 'src/engine/index.md') or None if not found.
    """
    child_dir = (root / child_path).parent.resolve()
    candidates = [
        (child_dir / parent).resolve(),
    ]
    if not Path(parent).suffix:
        candidates.append((child_dir / (parent + ".md")).resolve())
        candidates.append((child_dir / parent / "index.md").resolve())
    for cand in candidates:
        if cand in abs_path_to_node:
            return abs_path_to_node[cand]
    return None


def build_graph(root: Path) -> dict:
    """Walk entire project directory tree, parse all index.md files, build adjacency list."""
    root = root.resolve()  # normalize to absolute — relative_to() requires it
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    orphans: list[str] = []
    cycles: list[list[str]] = []

    # Load all nodes — walk entire project tree, not just .cns/
    for md_path in find_all_docs(root):
        rel = str(md_path.relative_to(root))
        fm = load_frontmatter(md_path)
        if not fm:
            continue
        nodes[rel] = {
            "path": rel,
            "file": str(md_path.resolve()),
            "title": fm.get("title", ""),
            "type": fm.get("type", ""),
            "parent": fm.get("parent"),
            "status": fm.get("status", ""),
            "decision_count": len(fm.get("decisions", [])),
        }

    # Build a lookup: absolute path -> canonical node path
    abs_path_to_node: dict[Path, str] = {
        (root / n["path"]).resolve(): n["path"] for n in nodes.values()
    }

    # Build a reverse index: parent_path -> [child_paths]
    children_of: dict[str, list[str]] = {}
    for path, node in nodes.items():
        parent = node.get("parent")
        if parent:
            parent_resolved = _resolve_parent_path(parent, path, root, abs_path_to_node)
            if parent_resolved:
                children_of.setdefault(parent_resolved, []).append(path)

    # BFS from root following children_of (DOWN the tree)
    root_node = ".cns/index.md"
    if root_node not in nodes:
        orphans = list(nodes.keys())
    else:
        visited: set[str] = set()
        queue = [root_node]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for child in children_of.get(current, []):
                edges.append({"from": current, "to": child, "label": "parent"})
                if child not in visited:
                    queue.append(child)

        # Any node never visited is orphan
        for n in nodes:
            if n not in visited:
                orphans.append(n)

    # Detect cycles (nodes whose parent chain eventually points back to them)
    for node_path, node in nodes.items():
        chain = []
        current = node_path
        visited_chain: set[str] = set()
        while current:
            if current in visited_chain:
                # Found cycle
                cycle_start = chain.index(current)
                cycles.append(chain[cycle_start:] + [current])
                break
            visited_chain.add(current)
            chain.append(current)
            parent = nodes.get(current, {}).get("parent")
            if not parent:
                break
            parent_resolved = _resolve_parent_path(parent, current, root, abs_path_to_node)
            if not parent_resolved:
                break
            current = parent_resolved

    # Detect dangling parent links
    dangling_links: list[dict] = []
    for path, node in nodes.items():
        parent = node.get("parent")
        if parent:
            parent_resolved = _resolve_parent_path(parent, path, root, abs_path_to_node)
            if not parent_resolved:
                dangling_links.append({
                    "from": path,
                    "to": parent,
                    "reason": "parent file not found"
                })

    return {
        "nodes": nodes,
        "edges": edges,
        "orphans": sorted(set(orphans)),
        "cycles": cycles,
        "dangling_links": dangling_links,
    }


def format_text(root: Path, g: dict) -> str:
    lines = [f"CNS Graph — {root.name}"]
    lines.append(f"Nodes: {len(g['nodes'])}  Edges: {len(g['edges'])}  Orphans: {len(g['orphans'])}  Cycles: {len(g['cycles'])}  Dangling: {len(g.get('dangling_links', []))}")
    lines.append("")

    if g["orphans"]:
        lines.append(f"ORPHANS ({len(g['orphans'])}):")
        for p in g["orphans"]:
            lines.append(f"  ! {p}")

    if g["cycles"]:
        lines.append(f"\nCYCLES ({len(g['cycles'])}):")
        for cyc in g["cycles"]:
            lines.append(f"  {' -> '.join(cyc)}")

    if g.get("dangling_links"):
        lines.append(f"\nDANGLING LINKS ({len(g['dangling_links'])}):")
        for dl in g["dangling_links"]:
            lines.append(f"  ! {dl['from']} -> {dl['to']} ({dl['reason']})")

    if not g["orphans"] and not g["cycles"] and not g.get("dangling_links"):
        lines.append("Graph is valid — no orphans, no cycles, no dangling links.")

    return "\n".join(lines)


def format_json_output(g: dict) -> str:
    return json.dumps(g, indent=2)


def main() -> int:
    args = parse_args()
    cns = args.project_root / ".cns"

    if not cns.is_dir():
        print(f"Error: {cns} not found", file=sys.stderr)
        return 1

    g = build_graph(args.project_root)

    if args.build:
        graph_path = cns / "graph.json"
        output = {
            "generated": datetime.now(timezone.utc).isoformat(),
            "nodes": list(g["nodes"].values()),
            "edges": g["edges"],
            "orphans": g["orphans"],
            "cycles": g["cycles"],
            "dangling_links": g.get("dangling_links", []),
        }
        graph_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"graph.json written — {len(g['nodes'])} nodes, {len(g['edges'])} edges", file=sys.stderr)
        return 0

    if args.check:
        graph_path = cns / "graph.json"
        if not graph_path.exists():
            print("graph.json missing", file=sys.stderr)
            return 1
        try:
            stored = json.loads(graph_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"graph.json unparseable: {e}", file=sys.stderr)
            return 1
        # Compare node count as a quick staleness check
        stored_count = len(stored.get("nodes", []))
        current_count = len(g["nodes"])
        if stored_count != current_count:
            print(f"graph.json stale: has {stored_count} nodes, currently {current_count}", file=sys.stderr)
            return 1
        if g["orphans"] or g["cycles"] or g.get("dangling_links"):
            print(f"graph.json out of sync: orphans={g['orphans']}, cycles={g['cycles']}, dangling={g.get('dangling_links', [])}", file=sys.stderr)
            return 1
        print("graph.json OK")
        return 0

    if args.orphans:
        if args.json:
            print(json.dumps(g["orphans"], indent=2))
        else:
            for p in g["orphans"]:
                print(p)
        return 0

    if args.cycles:
        if args.json:
            print(json.dumps(g["cycles"], indent=2))
        else:
            for cyc in g["cycles"]:
                print(" -> ".join(cyc))
        return 0

    if args.json:
        print(json.dumps(g, indent=2))
        return 0

    # Default: text summary
    print(format_text(args.project_root, g))
    return 0


if __name__ == "__main__":
    sys.exit(main())
