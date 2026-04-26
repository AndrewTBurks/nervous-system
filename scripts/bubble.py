#!/usr/bin/env python3
"""
bubble.py — Bubble analysis for a CNS node.

Traverses the parent chain upward from a node to the project root,
showing each parent in the chain. This is analysis-only — it reads
files and reports the chain; the LLM then decides independently what
(if anything) to write.

The bubble always reaches the project root. What gets written at each
level depends on whether the change is externally relevant — the agent
makes that judgment, not a flag.

USAGE:
    bubble.py <project_root> <node_path>    # analyze chain
    bubble.py <project_root> <node_path> --json   # machine-readable

EXAMPLE:
    bubble.py . src/engine/index.md
"""

import argparse
import sys
import yaml
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from shared import section, field


# ── Frontmatter helpers ───────────────────────────────────────────────────────

def load_frontmatter(md_path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from a markdown file. Returns {} on failure."""
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


def get_body_without_frontmatter(md_path: Path) -> str:
    """Get just the body (everything after the closing ---)."""
    content = md_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content
    return parts[2].lstrip("\n")


# ── Chain builder ─────────────────────────────────────────────────────────────

def build_bubble_chain(node_path: str, root: Path) -> list[dict]:
    """
    Walk upward from node_path following parent links to the project root.
    Returns list of {node, parent, parent_resolved, body_preview} dicts.
    The chain always reaches the root (.cns/index.md or equivalent).
    """
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
        parent_rel = fm.get("parent")
        body = get_body_without_frontmatter(md_path)
        body_preview = body[:120].replace("\n", " ").strip() if body else ""

        entry = {
            "node": current,
            "title": node_title,
            "parent_rel": parent_rel,
            "parent_resolved": None,
            "body_preview": body_preview,
        }

        if parent_rel:
            parent_abs = (md_path.parent / parent_rel).resolve()
            parent_resolved = str(parent_abs.relative_to(root))
            entry["parent_resolved"] = parent_resolved
        else:
            # No parent — this is the root
            chain.append(entry)
            break

        chain.append(entry)
        current = parent_resolved

    return chain


def should_bubble(chain: list[dict]) -> tuple[bool, str]:
    """
    The bubble always reaches the root. Returns (True, reason).
    The judgment of whether to write at each level is left to the LLM.
    """
    if not chain:
        return False, "empty chain"
    return True, "reaches project root"


# ── Output formatter ───────────────────────────────────────────────────────────

def format_bubble(node_path: str, root: Path, as_json: bool = False) -> str:
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
            if entry["parent_resolved"]:
                parent_info = f" -> {entry['parent_resolved']}"
            elif entry["parent_rel"] is None:
                parent_info = " (root)"
            else:
                parent_info = f" -> {entry['parent_rel']} [RESOLVE ERROR]"
            lines.append(f"  [{i}] {entry['node']}{parent_info}")
            lines.append(f"      title: {entry['title']}")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Bubble analysis for a CNS node.")
    parser.add_argument("project_root", type=Path, default=Path.cwd())
    parser.add_argument("node", nargs="?", default=None, help="CNS node path")
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

    result = format_bubble(node_path, root, as_json=args.json)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
