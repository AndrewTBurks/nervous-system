#!/usr/bin/env python3
"""
bootstrap.py — Initialize the Nervous System for a project.

Creates the full .cns/ directory structure with linked index.md nodes.
Can be run with CLI arguments for pre-filled content, or with defaults
for skeleton files that the agent/user fills later.

USAGE:
    bootstrap.py <project_root> [options]

EXAMPLES:
    # Skeleton mode — empty structure with placeholder content
    bootstrap.py .

    # Pre-filled mode — supply project context
    bootstrap.py . --name "MyProject" --description "A distributed task runner"
        --stack "Rust, Tokio, gRPC" --modules "scheduler, worker, api"
"""

import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_index(path: Path, title: str, node_type: str, parent: str | None = None,
                body: str = "", decisions: list | None = None, links: list | None = None) -> None:
    """Write an index.md with proper frontmatter."""
    fm_lines = ["---", f'title: "{title}"', f"type: {node_type}"]
    if parent:
        fm_lines.append(f"parent: {parent}")
    if links:
        fm_lines.append("links:")
        for link in links:
            fm_lines.append(f"  - id: {link['id']}")
            fm_lines.append(f"    path: {link['path']}")
    if decisions:
        fm_lines.append("decisions:")
        for d in decisions:
            fm_lines.append(f"  - id: {d['id']}")
            fm_lines.append(f"    date: {d['date']}")
            fm_lines.append(f"    author: {d['author']}")
            fm_lines.append(f"    summary: {d['summary']}")
    fm_lines.extend(["human_notes: |", "  ", "status: clean", f"last_reconciled: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}", "---", ""])

    content = "\n".join(fm_lines)
    if body:
        content += "\n" + body + "\n"
    path.write_text(content, encoding="utf-8")


def create_log(root: Path) -> None:
    log_path = root / ".cns" / "log.md"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc).strftime("%H:%M")
    log_path.write_text(
        f"## {today}\n\n"
        f"### {now} — bootstrap\n"
        f"- Initialized .cns/ directory structure\n"
        f"- Created central nodes: architecture, design, product, research\n"
        f"- Generated graph.json\n",
        encoding="utf-8"
    )


def create_intent(root: Path) -> None:
    intent_path = root / ".cns" / "intent.md"
    intent_path.write_text(
        "# Planned Work\n\n"
        "Ordered from immediate blockers to long-term execution.\n\n"
        "---\n\n"
        "## Phase 1: Foundation\n\n"
        "- [ ] TASK-001: Initial setup and verification\n",
        encoding="utf-8"
    )


def run_extract(project_root: Path) -> None:
    extract_script = Path(__file__).parent / "extract.py"
    result = subprocess.run(
        [sys.executable, str(extract_script), str(project_root)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Warning: extract.py failed:\n{result.stderr}", file=sys.stderr)
    else:
        print(result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap the Nervous System")
    parser.add_argument("project_root", type=Path, help="Project root directory")
    parser.add_argument("--name", default="", help="Project name")
    parser.add_argument("--description", default="", help="One-line project description")
    parser.add_argument("--stack", default="", help="Tech stack (comma-separated)")
    parser.add_argument("--modules", default="", help="Key modules (comma-separated)")
    parser.add_argument("--decisions", default="", help="Existing decisions, one per line in 'ID|date|author|summary' format")
    args = parser.parse_args()

    root = args.project_root.resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        return 1

    cns = root / ".cns"
    if cns.exists():
        print(f"Warning: {cns} already exists. Bootstrapping will not overwrite existing files.")

    # Create directories
    for subdir in ["architecture", "design", "product", "research", "plans"]:
        ensure_dir(cns / subdir)

    project_name = args.name or root.name
    desc = args.description or "(description pending)"
    stack = args.stack or "(tech stack pending)"
    modules = [m.strip() for m in args.modules.split(",") if m.strip()]

    # Parse pre-existing decisions
    pre_decisions = []
    if args.decisions:
        for line in args.decisions.strip().split("\n"):
            parts = line.split("|", 3)
            if len(parts) == 4:
                pre_decisions.append({
                    "id": parts[0],
                    "date": parts[1],
                    "author": parts[2],
                    "summary": parts[3],
                })

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # --- .cns/index.md (root) ---
    root_links = [
        {"id": "architecture", "path": ".cns/architecture/index.md"},
        {"id": "design", "path": ".cns/design/index.md"},
        {"id": "product", "path": ".cns/product/index.md"},
        {"id": "research", "path": ".cns/research/index.md"},
    ]
    root_body = f"""# {project_name}

{desc}

## Tech Stack

{stack}

## Modules

"""
    if modules:
        for mod in modules:
            root_body += f"- {mod}\n"
    else:
        root_body += "(modules pending)\n"

    root_body += "\n## Overview\n\nThis is the central nervous system for the project.\n"

    write_index(
        cns / "index.md",
        title=project_name,
        node_type="project",
        links=root_links,
        decisions=pre_decisions,
        body=root_body,
    )

    # --- architecture/index.md ---
    arch_body = "# Architecture\n\nSystem architecture, key tradeoffs, and structural decisions.\n"
    if pre_decisions:
        arch_body += "\n## Decisions\n\n"
        for d in pre_decisions:
            arch_body += f"- **{d['id']}** ({d['date']}): {d['summary']}\n"
    write_index(
        cns / "architecture" / "index.md",
        title="Architecture",
        node_type="module",
        parent="../index.md",
        body=arch_body,
    )

    # --- design/index.md ---
    design_body = f"""# Design Language

Conventions, patterns, and UI/UX decisions.

## Tech Stack

{stack}

## Conventions

(conventions pending)
"""
    write_index(
        cns / "design" / "index.md",
        title="Design",
        node_type="module",
        parent="../index.md",
        body=design_body,
    )

    # --- product/index.md ---
    product_body = f"""# Product

Audience, users, goals, and roadmap direction.

## Goals

(goals pending)

## Audience

(audience pending)
"""
    write_index(
        cns / "product" / "index.md",
        title="Product",
        node_type="module",
        parent="../index.md",
        body=product_body,
    )

    # --- research/index.md ---
    research_body = """# Research

Background research, related work, and literature.

## Papers

(papers pending)

## Related Work

(related work pending)
"""
    write_index(
        cns / "research" / "index.md",
        title="Research",
        node_type="module",
        parent="../index.md",
        body=research_body,
    )

    # --- log.md ---
    create_log(root)

    # --- intent.md ---
    create_intent(root)

    # --- graph.json ---
    run_extract(root)

    print(f"\nBootstrapped Nervous System at: {cns}")
    print(f"  Nodes created: 5")
    print(f"  Files created: .cns/index.md, architecture/index.md, design/index.md,")
    print(f"                 product/index.md, research/index.md, log.md, intent.md,")
    print(f"                 graph.json, plans/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
