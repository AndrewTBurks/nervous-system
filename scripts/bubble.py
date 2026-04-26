#!/usr/bin/env python3
"""
bubble.py — Dry-run bubble analysis for a CNS node.

Shows the full bubble chain (which parents would be updated, in what order),
but does NOT write anything. The LLM reads the files and decides what to write.

USAGE:
    bubble.py <project_root> <node_path>       # dry-run (default)
    bubble.py <project_root> <node_path> --execute   # actually run bubble
    bubble.py <project_root> <node_path> --json       # machine-readable

EXAMPLES:
    bubble.py . src/engine/index.md
    bubble.py . .cns/architecture/index.md --execute
"""

import argparse
import sys
import yaml
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).parent))
from shared import section, field, item, kv, header, resolve_link


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
    """Returns (frontmatter_dict, body_without_frontmatter)"""
    content = md_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    fm = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return fm, body


def get_body_without_frontmatter(md_path: Path) -> str:
    """Get just the body (everything after the closing ---)."""
    content = md_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content
    return parts[2].lstrip("\n")


def resolve_parent(parent_rel: str, child_path: Path, root: Path) -> Path:
    """
    Resolve a parent path as stored in frontmatter.

    Parent paths in CNS frontmatter are relative to the child file's directory.
    E.g. if child is .cns/architecture/index.md and parent is "../index.md",
    the resolved parent is .cns/index.md.
    """
    # parent is relative to child's directory
    parent_abs = (child_path.parent / parent_rel).resolve()
    # make it relative to root
    return parent_abs.relative_to(root)


# ── Chain builder ─────────────────────────────────────────────────────────────

def build_bubble_chain(node_path: str, root: Path) -> list[dict]:
    """
    Walk upward from node_path following parent links.
    Returns list of {node, public, parent, parent_resolved, body_summary} dicts.
    Stops when: public=false, parent missing, or project root reached.
    """
    cns = root / ".cns"
    chain = []
    current = node_path
    visited: set[str] = set()

    while current:
        if current in visited:
            break
        visited.add(current)

        md_path = root / current
        if not md_path.exists():
            break

        fm = load_frontmatter(md_path)
        node_title = fm.get("title", current)
        is_public = fm.get("public", False)
        parent_rel = fm.get("parent")
        body = get_body_without_frontmatter(md_path)
        body_preview = body[:120].replace("\n", " ").strip() if body else ""

        entry = {
            "node": current,
            "title": node_title,
            "public": is_public,
            "parent_rel": parent_rel,
            "parent_resolved": None,
            "body_preview": body_preview,
        }

        if parent_rel:
            parent_resolved = str(resolve_parent(parent_rel, md_path, root))
            entry["parent_resolved"] = parent_resolved
        else:
            # No parent — this is the root
            chain.append(entry)
            break

        chain.append(entry)

        if not is_public:
            # Private nodes update their parent but don't continue upward
            break

        current = parent_resolved

    return chain


def should_bubble(chain: list[dict]) -> tuple[bool, str]:
    """
    Determine if bubble should proceed and where it stops.
    Returns (should_bubble, stop_reason).
    """
    if not chain:
        return False, "empty chain"
    last = chain[-1]
    if last["parent_resolved"] is None:
        return True, "reached project root"
    if not last["public"]:
        return False, "parent is public: false"
    return True, "reached project root"


# ── Bubble execution ─────────────────────────────────────────────────────────

def synthesize_bubble_entry(child_node: dict, parent_body: str) -> str:
    """
    Synthesize a 1-3 sentence summary of a child change to insert into the parent body.
    """
    date = ""
    decisions = []
    # Try to find date from decisions if present
    child_path = child_node["node"]
    root = Path("/").resolve()  # placeholder — resolved at call site

    return (
        f"> **<{child_node['title']}>** ({child_node['node']}): "
        f"Change detected in this subtree. "
        f"Review {child_node['node']} for details."
    )


def execute_bubble(node_path: str, root: Path) -> tuple[int, list[str]]:
    """
    Actually perform the bubble writes.
    Returns (files_written_count, list_of_messages).
    """
    chain = build_bubble_chain(node_path, root)
    if not chain:
        return 0, ["No chain found"]

    written = []
    for i, entry in enumerate(chain[:-1]):  # skip root (nothing above it)
        child = entry
        parent_entry = chain[i + 1]
        parent_path = parent_entry["node"]

        md_parent = root / parent_path
        md_child = root / child["node"]

        fm, body = split_frontmatter(md_parent)

        # Build the insertion text
        insertion = (
            f"\n> **<{child['title']}>** ({child['node']}): "
            f"Change detected in this subtree. "
            f"Review {child['node']} for details.\n"
        )

        # Append to body (after frontmatter)
        new_body = body.rstrip("\n") + "\n" + insertion.lstrip("\n")

        save_frontmatter(md_parent, new_body, fm)
        written.append(f"WROTE: {parent_path}")

    return len(written), written


# ── Output formatters ────────────────────────────────────────────────────────

def format_bubble(node_path: str, root: Path, execute: bool = False, as_json: bool = False) -> str:
    chain = build_bubble_chain(node_path, root)
    should_bub, stop_reason = should_bubble(chain)

    if as_json:
        import json
        return json.dumps({
            "node": node_path,
            "chain": chain,
            "would_bubble": should_bub,
            "stop_reason": stop_reason,
            "chain_length": len(chain),
        }, indent=2)

    lines = [section("bubble", node_path)]

    # Chain summary
    lines.append(field("start", node_path))
    lines.append(field("chain_length", str(len(chain))))
    lines.append(field("would_bubble", "true" if should_bub else "false"))
    lines.append(field("stop_reason", stop_reason))
    lines.append("")

    lines.append("chain:")
    if not chain:
        lines.append("  (empty)")
    else:
        for i, entry in enumerate(chain, 1):
            parent_info = ""
            if entry["parent_resolved"]:
                parent_info = f" -> {entry['parent_resolved']}"
            elif entry["parent_rel"] is None:
                parent_info = " (root)"
            else:
                parent_info = f" -> {entry['parent_rel']} [RESOLVE ERROR]"
            pub = "public" if entry["public"] else "private"
            lines.append(f"  [{i}] {entry['node']} ({pub}){parent_info}")
            lines.append(f"      title: {entry['title']}")

    if execute and should_bub:
        lines.append("")
        written_count, written_msgs = execute_bubble(node_path, root)
        lines.append(f"executed: {written_count} file(s) written")
        for msg in written_msgs:
            lines.append(f"  {msg}")
    elif execute and not should_bub:
        lines.append("")
        lines.append("executed: no bubble performed (stop_reason: {stop_reason})")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Bubble dry-run (or execute) for a CNS node.")
    parser.add_argument("project_root", type=Path, default=Path.cwd())
    parser.add_argument("node", nargs="?", default=None, help="CNS node path")
    parser.add_argument("--execute", action="store_true", help="Actually perform bubble (default is dry-run)")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()

    root = args.project_root.resolve()
    if not (root / ".cns").is_dir():
        print(f"Error: {root}/.cns/ not found", file=sys.stderr)
        return 1

    if not args.node:
        print("Error: node path required", file=sys.stderr)
        return 1

    node_path = args.node
    if not (root / node_path).exists():
        print(f"Error: {node_path} not found", file=sys.stderr)
        return 1

    result = format_bubble(node_path, root, execute=args.execute, as_json=args.json)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
