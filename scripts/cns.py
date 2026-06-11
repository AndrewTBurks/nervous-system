#!/usr/bin/env python3
"""cns.py — small command wrapper for nervous-system scripts."""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def run(args):
    print("$ " + " ".join(str(a) for a in args))
    return subprocess.run([sys.executable] + [str(a) for a in args]).returncode


def cmd_health(project_root: Path) -> int:
    code = run([SCRIPT_DIR / "extract.py", project_root])
    if code != 0:
        return code
    code = run([SCRIPT_DIR / "validate.py", project_root])
    if code != 0:
        return code
    return run([SCRIPT_DIR / "graph.py", project_root, "--check"])


def cmd_status(project_root: Path) -> int:
    root = project_root.resolve()
    print(f"CNS status for: {root}")
    print(f".cns exists: {(root / '.cns').is_dir()}")
    for rel in [".cns/index.md", ".cns/intent.md", ".cns/log.md", ".cns/graph.json"]:
        print(f"{rel}: {(root / rel).exists()}")
    plans = root / ".cns" / "plans"
    if plans.is_dir():
        print(f".cns/plans: {len(list(plans.glob('*.md')))} markdown file(s)")
    return cmd_health(root)


def cmd_bootstrap(project_root: Path, passthrough) -> int:
    return run([SCRIPT_DIR / "bootstrap.py", project_root] + passthrough)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Nervous-system command wrapper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("health", help="Run extract, validate, and graph --check")
    p.add_argument("project_root", nargs="?", default=".")

    p = sub.add_parser("status", help="Show CNS file presence and run health")
    p.add_argument("project_root", nargs="?", default=".")

    p = sub.add_parser("bootstrap", help="Run bootstrap.py; remaining args pass through")
    p.add_argument("project_root")
    p.add_argument("args", nargs=argparse.REMAINDER)

    args = parser.parse_args(argv)
    if args.command == "health":
        return cmd_health(Path(args.project_root))
    if args.command == "status":
        return cmd_status(Path(args.project_root))
    if args.command == "bootstrap":
        return cmd_bootstrap(Path(args.project_root), args.args)
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
