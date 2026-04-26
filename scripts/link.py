#!/usr/bin/env python3
"""
link.py — Show outgoing links and/or incoming backlinks for a CNS node.

USAGE:
    link.py <project_root> <node_path>       # both outgoing + incoming
    link.py <project_root> <node_path> --outgoing   # only outgoing
    link.py <project_root> <node_path> --incoming    # only backlinks
    link.py <project_root>                   # show all links across entire CNS
    link.py <project_root> --json            # machine-readable

EXAMPLES:
    link.py /path/to/project .cns/architecture/index.md
    link.py . src/engine/index.md --incoming
    link.py . --outgoing
"""

import argparse
import sys
import yaml
from pathlib import Path
from typing import Any, Optional

# ── Shared formatting ────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from shared import section, field, item, kv, header, resolve_link, link_status, find_all_docs


# ── Link resolution ───────────────────────────────────────────────────────────

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


def build_link_index(root: Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """
    Returns (forward: source -> [resolved_link_paths],
             reverse: resolved_link_path -> [source_paths])
    """
    cns = root / ".cns"
    project_root = root / ".cns" / ".."

    forward: dict[str, list[str]] = {}
    reverse: dict[str, list[str]] = {}

    for md_path in find_all_docs(root):
        rel = str(md_path.relative_to(root))
        fm = load_frontmatter(md_path)
        links_raw = fm.get("links", [])
        if not isinstance(links_raw, list):
            links_raw = []

        resolved_links: list[str] = []
        for entry in links_raw:
            # entry can be a string or a dict with "path"
            link_path = entry if isinstance(entry, str) else entry.get("path", "")
            if not link_path:
                continue
            abs_path = resolve_link(link_path, md_path, root)
            resolved_links.append(str(abs_path))
            # reverse index — target path -> source node
            reverse.setdefault(str(abs_path), []).append(rel)

        if resolved_links or links_raw:
            forward[rel] = resolved_links

    return forward, reverse


def resolve_node_links(node_path: str, root: Path) -> list[tuple[str, str]]:
    """
    Return [(resolved_abs_path, status)] for all links in the given node.
    """
    md_path = root / node_path
    fm = load_frontmatter(md_path)
    links_raw = fm.get("links", [])
    if not isinstance(links_raw, list):
        links_raw = []

    results = []
    for entry in links_raw:
        link_path = entry if isinstance(entry, str) else entry.get("path", "")
        if not link_path:
            continue
        abs_path = resolve_link(link_path, md_path, root)
        results.append((str(abs_path), link_status(abs_path)))
    return results


def resolve_node_backlinks(node_path: str, root: Path, forward: dict[str, list[str]], reverse: dict[str, list[str]]) -> list[tuple[str, str]]:
    """
    Find all nodes that link TO this node.
    The node might be referenced by its CNS path (e.g. .cns/design/index.md)
    or by any of its resolved absolute paths.
    """
    project_root = root / ".cns" / ".."
    candidates = []

    # All possible paths that could reference this node
    abs_node = str((project_root / node_path).resolve())

    # Find in reverse index
    sources = reverse.get(abs_node, [])

    # Also check if any forward entry mentions this node
    for src, links in forward.items():
        if any(abs_node in l or node_path in l for l in links):
            if src not in sources:
                sources.append(src)

    results = []
    for src in sources:
        # Get the link text from the source's frontmatter
        md_path = root / src
        fm = load_frontmatter(md_path)
        links_raw = fm.get("links", [])
        link_text = ""
        for entry in links_raw:
            lp = entry if isinstance(entry, str) else entry.get("path", "")
            if not lp:
                continue
            abs_l = str(resolve_link(lp, md_path, root))
            if abs_l == abs_node or lp == node_path:
                link_text = lp
                break
        results.append((src, link_text or node_path))
    return results


# ── Text output ─────────────────────────────────────────────────────────────

def format_node_links(node_path: str, root: Path, forward: dict[str, list[str]], reverse: dict[str, list[str]], show_outgoing: bool = True, show_incoming: bool = True) -> str:
    project_root = root / ".cns" / ".."
    abs_node = str((project_root / node_path).resolve())

    lines = [section("links", node_path)]

    # Outgoing
    if show_outgoing:
        outgoing = resolve_node_links(node_path, root)
        if outgoing:
            lines.append(field("outgoing", str(len(outgoing))))
            for i, (abs_path, status) in enumerate(outgoing, 1):
                lines.append(item(i, abs_path, status))
        else:
            lines.append(field("outgoing", "0"))

    # Incoming
    if show_incoming:
        backlinks = resolve_node_backlinks(node_path, root, forward, reverse)
        if backlinks:
            lines.append(field("incoming", str(len(backlinks))))
            for i, (src, link_text) in enumerate(backlinks, 1):
                lines.append(item(i, f"{src}  ->  {link_text}"))
        else:
            lines.append(field("incoming", "0"))

    return "\n".join(lines)


def format_all_links(root: Path, forward: dict[str, list[str]], reverse: dict[str, list[str]]) -> str:
    """Show all outgoing links across the entire CNS."""
    lines = [section("links", "(all nodes)")]
    for node_path in sorted(forward.keys()):
        outgoing = resolve_node_links(node_path, root)
        if not outgoing:
            continue
        lines.append(f"\n  {node_path}")
        for abs_path, status in outgoing:
            lines.append(f"    -> {abs_path}  [{status}]")
    return "\n".join(lines)


def format_json(root: Path, node_path: Optional[str], forward: dict, reverse: dict, show_outgoing: bool, show_incoming: bool) -> str:
    import json
    project_root = root / ".cns" / ".."

    if node_path:
        abs_node = str((project_root / node_path).resolve())
        out = []
        for abs_l, status in resolve_node_links(node_path, root):
            out.append({"to": abs_l, "status": status})
        inc = [{"from": src, "link_text": lt} for src, lt in resolve_node_backlinks(node_path, root, forward, reverse)]
        data = {"node": node_path, "outgoing": out, "incoming": inc}
    else:
        data = {"nodes": {}}
        for np in sorted(forward.keys()):
            out = [{"to": str(a), "status": s} for a, s in resolve_node_links(np, root)]
            inc = [{"from": s, "link_text": l} for s, l in resolve_node_backlinks(np, root, forward, reverse)]
            data["nodes"][np] = {"outgoing": out, "incoming": inc}

    return json.dumps(data, indent=2)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Show links for a CNS node.")
    parser.add_argument("project_root", type=Path, default=Path.cwd())
    parser.add_argument("node", nargs="?", default=None, help="CNS node path (e.g. .cns/architecture/index.md)")
    parser.add_argument("--outgoing", action="store_true")
    parser.add_argument("--incoming", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = args.project_root.resolve()
    if not (root / ".cns").is_dir():
        print(f"Error: {root}/.cns/ not found", file=sys.stderr)
        return 1

    forward, reverse = build_link_index(root)

    # Default: show both if a specific node given, all if no node
    show_outgoing = True
    show_incoming = True
    if args.outgoing and not args.incoming:
        show_incoming = False
    if args.incoming and not args.outgoing:
        show_outgoing = False

    if args.json:
        print(format_json(root, args.node, forward, reverse, show_outgoing, show_incoming))
        return 0

    if not args.node:
        if show_outgoing and not show_incoming:
            print("Error: --outgoing requires a node path", file=sys.stderr)
            return 1
        if show_incoming and not show_outgoing:
            print("Error: --incoming requires a node path", file=sys.stderr)
            return 1
        print(format_all_links(root, forward, reverse))
        return 0

    node_path = args.node
    if not (root / node_path).exists():
        print(f"Error: {node_path} not found", file=sys.stderr)
        return 1

    print(format_node_links(node_path, root, forward, reverse, show_outgoing, show_incoming))
    return 0


if __name__ == "__main__":
    sys.exit(main())
