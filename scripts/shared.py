#!/usr/bin/env python3
"""
shared.py — Shared output formatting for CNS agent scripts.

Text format:
  ## [<section>] <path>
  key: value
  key: value
    [1] item
    [2] item

Numbered items [N] allow the LLM to reference specific entries concisely.
"""

import sys
from pathlib import Path
from typing import Any
from typing import Optional


# ─── Text helpers ────────────────────────────────────────────────────────────

def section(label: str, path: str) -> str:
    return f"## [{label}] {path}\n"


def field(key: str, value: str) -> str:
    return f"{key}: {value}"


def item(n: int, text: str, status: Optional[str] = None) -> str:
    prefix = f"  [{n}] "
    if status:
        return f"{prefix}{text}  [{status}]"
    return f"{prefix}{text}"


def kv(key: str, value: Any) -> str:
    return f"  {key}: {value}"


def yesno(cond: bool, yes: str = "yes", no: str = "no") -> str:
    return yes if cond else no


def divider() -> str:
    return ""


# ─── JSON helpers ────────────────────────────────────────────────────────────

def json_out(data: dict) -> str:
    import json
    return json.dumps(data, indent=2)


# ─── Resolve link relative to a given source file ────────────────────────────

def resolve_link(link_path: str, source_file: Path, root: Path) -> Path:
    """
    Resolve a links[] path as it would appear in `source_file`'s frontmatter.

    links[] paths in CNS frontmatter are relative to the project root
    (where .cns/ lives), NOT relative to the source file's directory.
    validate.py confirms this pattern.

    But for rebasing during a move, we need to re-resolve relative to
    the source file's directory — so we compute the absolute target by
    joining link_path to the project root.
    """
    project_root = root / ".cns" / ".."
    return (project_root / link_path).resolve()


def link_status(abs_path: Path) -> str:
    if not abs_path.exists():
        return "MISSING"
    if abs_path.is_dir():
        return "DIR"
    return "EXISTS"


def header(script: str, subcmd: Optional[str] = None) -> str:
    label = script if not subcmd else f"{script} {subcmd}"
    return f"## [{label}]\n"


def parse_args(script: str, argv: list[str]) -> tuple:
    """
    Shared argument parser for link/bubble/move.

    Returns (project_root, json_flag).
    Override this in scripts that need extra args.
    """
    import argparse
    parser = argparse.ArgumentParser(prog=script)
    parser.add_argument("project_root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args, unknown = parser.parse_known_args(argv)
    return args.project_root.resolve(), args.json, unknown


# ─── Nervous-system document discovery ───────────────────────────────────────

def find_all_docs(root: Path) -> list[Path]:
    """
    Return all nervous-system documents:
      - *.md in .cns/ (minus log.md)
      - all index.md files outside .cns/

    Sorted, deduplicated by resolved path.
    """
    cns = root / ".cns"
    seen: set[Path] = set()
    docs: list[Path] = []

    for p in sorted(cns.rglob("*.md")):
        if p.name in ("log.md", "intent.md"):
            continue
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            docs.append(p)

    for p in sorted(root.rglob("index.md")):
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            docs.append(p)

    docs.sort(key=lambda p: str(p))
    return docs
