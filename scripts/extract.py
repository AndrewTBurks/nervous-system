#!/usr/bin/env python3
"""
extract.py — Nervous System graph extraction

Walks the project directory, finds all index.md files, parses their frontmatter,
builds an adjacency graph, detects cycles and orphans, and outputs .cns/graph.json.

Usage:
    python extract.py [project_root]
    # project_root defaults to current working directory
"""

import os
import sys
import json
import re
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
    YAMLError = yaml.YAMLError  # alias so except doesn't need `yaml` reference (avoids UnboundLocalError)
except ImportError:
    HAS_YAML = False
    YAMLError = Exception
    # Self-install PyYAML if missing — one-shot install for users who lack it
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', 'pyyaml', '--quiet', '--user'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        try:
            import yaml
            HAS_YAML = True
            YAMLError = yaml.YAMLError
        except ImportError:
            HAS_YAML = False


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parse YAML frontmatter from a markdown file.
    Returns (frontmatter_dict, body).
    frontmatter must be wrapped in --- ... --- delimiters.

    Uses PyYAML if available for correct nested YAML parsing;
    falls back to _simple_parse otherwise.
    """
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
    if not match:
        return {}, content

    yaml_text = match.group(1)
    body = match.group(2)

    if HAS_YAML:
        try:
            fm = yaml.safe_load(yaml_text)
            return (fm or {}), body
        except YAMLError as e:
            # Non-fatal — fall through to simple parser
            pass

    # Fallback: simple parser for basic structures
    fm = _simple_parse(yaml_text)
    return fm, body


def _simple_parse(yaml_text: str) -> dict:
    """
    Simple YAML parser that handles:
    - Top-level key: value (including multiline strings)
    - Top-level list of scalar values: [a, b, c]
    - Top-level list of objects: [- id: X, - id: Y]
    """
    result = {}
    current_key = None
    list_key = None  # the key whose list is currently being populated
    current_obj = None
    in_list_of_objects = False

    for line in yaml_text.split('\n'):
        if not line.strip() or line.strip().startswith('#'):
            if current_key and not in_list_of_objects:
                result[current_key] = result.get(current_key, '').rstrip()
            current_key = None
            continue

        indent = len(line) - len(line.lstrip())
        content = line.strip()

        # Top-level key: value
        top_kv = re.match(r'^(\w[\w_]*):\s*(.*)$', content)
        if top_kv and indent == 0:
            key = top_kv.group(1)
            val = top_kv.group(2).strip()

            # Close any open list of objects
            if in_list_of_objects and current_obj:
                if list_key and isinstance(result.get(list_key), list):
                    result[list_key].append(current_obj)
                current_obj = None
            in_list_of_objects = False
            list_key = None
            current_key = None

            if val == '':
                current_key = key
                result[key] = ''
            elif val.startswith('['):
                result[key] = [x.strip() for x in val[1:-1].split(',') if x.strip()]
            else:
                result[key] = val
            continue

        # Continuation of multiline string value
        if indent == 0 and current_key and not content.startswith('-') and not in_list_of_objects:
            result[current_key] += '\n' + content
            continue

        # List item
        if content.startswith('- '):
            item = content[2:].strip()

            # Check if it's an object: "- key: value"
            obj_kv = re.match(r'^(\w[\w_]*):\s*(.*)$', item)
            if obj_kv and not item.startswith('-'):
                # Object item
                if current_obj and list_key:
                    if isinstance(result.get(list_key), list):
                        result[list_key].append(current_obj)
                    else:
                        result[list_key] = [current_obj]
                current_obj = {}
                obj_key = obj_kv.group(1)
                obj_val = obj_kv.group(2).strip()
                current_obj[obj_key] = obj_val
                list_key = current_key or list_key
                current_key = None
                in_list_of_objects = True
            else:
                # Scalar item
                if current_obj and list_key:
                    if isinstance(result.get(list_key), list):
                        result[list_key].append(current_obj)
                    else:
                        result[list_key] = [current_obj]
                    current_obj = None
                in_list_of_objects = False
                if current_key and isinstance(result.get(current_key), list):
                    list_key = current_key
                elif not list_key:
                    list_key = current_key
                if list_key and isinstance(result.get(list_key), list):
                    result[list_key].append(item)
                current_key = None
            continue

        # Continuation of multiline field inside current object
        if indent > 0 and in_list_of_objects and current_obj and current_key:
            if isinstance(current_obj.get(current_key), str):
                current_obj[current_key] += '\n' + content
            continue

    # Flush any open state
    if in_list_of_objects and current_obj and list_key:
        if isinstance(result.get(list_key), list):
            result[list_key].append(current_obj)
        else:
            result[list_key] = [current_obj]

    return result


def find_index_md_files(root: Path) -> list[Path]:
    """Find all index.md files under root, including those in .cns/."""
    results = []
    for dirpath, dirnames, filenames in os.walk(root):
        if 'index.md' in filenames:
            results.append(Path(dirpath) / 'index.md')
    return results


def build_graph(files: list[Path], root: Path) -> dict:
    """
    Build adjacency graph from index.md files.
    Returns graph dict with nodes, edges, orphans, cycles, dangling_links.

    Special handling for .cns/intents/index.md:
    - Must have type: intents_root
    - Each entry in intents[] is validated for required fields
    """
    nodes = []
    edges = []
    orphans = []
    dangling_links = []
    intent_warnings = []

    # Track which paths we've seen
    path_to_node = {}

    for f in files:
        rel = f.relative_to(root)
        fm, _ = parse_frontmatter(f.read_text(encoding='utf-8'))

        node = {
            'path': str(rel),
            'file': str(f),  # captured here for use in the parent-resolve loop
            'title': fm.get('title', rel.stem),
            'type': fm.get('type', 'unknown'),
            'public': fm.get('public', False),
            'parent': fm.get('parent'),
        }
        nodes.append(node)
        path_to_node[str(rel)] = node

        # Validate intents root
        if str(rel) == '.cns/intents/index.md':
            if fm.get('type') != 'intents_root':
                intent_warnings.append({
                    'path': str(rel),
                    'message': '.cns/intents/index.md should have type: intents_root'
                })
            # Validate each intent entry
            intents = fm.get('intents', [])
            if not isinstance(intents, list):
                intent_warnings.append({
                    'path': str(rel),
                    'message': 'intents[] should be an array'
                })
            else:
                for i, intent in enumerate(intents):
                    if isinstance(intent, dict):
                        for field in ('id', 'category', 'summary', 'status'):
                            if field not in intent:
                                intent_warnings.append({
                                    'path': str(rel),
                                    'message': f'intents[{i}] missing "{field}" field'
                                })
                        valid_categories = ('feature', 'refactor', 'research', 'bug', 'exploration', 'thesis')
                        if intent.get('category') not in valid_categories:
                            intent_warnings.append({
                                'path': str(rel),
                                'message': f'intents[{i}] has invalid category "{intent.get("category")}" — must be one of {valid_categories}'
                            })
                        valid_statuses = ('pending', 'in_progress', 'completed', 'cancelled')
                        if intent.get('status') not in valid_statuses:
                            intent_warnings.append({
                                'path': str(rel),
                                'message': f'intents[{i}] has invalid status "{intent.get("status")}" — must be one of {valid_statuses}'
                            })
                    else:
                        intent_warnings.append({
                            'path': str(rel),
                            'message': f'intents[{i}] should be a YAML object, found: {type(intent).__name__}'
                        })

    # Build edges from parent field
    for node in nodes:
        parent = node.get('parent')
        if parent:
            # Parent path is relative to project root
            # Auto-append index.md if parent points to a directory
            parent_path = Path(parent)
            # If parent points to a directory (no extension in the last component), append index.md.
            # "backend" -> "backend/index.md". "../index.md" or "../../.cns/index.md" already
            # point to files and should not be modified.
            if not parent_path.suffix and parent_path.name == parent_path.name.split('.')[0]:
                parent_path = parent_path / 'index.md'
            # Resolve relative to the project root
            # But first we need the absolute path: resolve the file's directory, then the parent from there
            node_dir = Path(node['file']).parent.resolve()
            parent_abs = (node_dir / parent_path).resolve()
            # Try to find a node whose path matches the resolved parent
            found = False
            for n in nodes:
                n_abs = (root / n['path']).resolve()
                if n_abs == parent_abs:
                    edges.append({
                        'from': node['path'],
                        'to': n['path'],
                        'label': 'parent'
                    })
                    found = True
                    break
            if not found:
                dangling_links.append({
                    'from': node['path'],
                    'to': parent,
                    'reason': 'parent file not found'
                })

    # Detect orphans: index.md with no nearby code
    for node in nodes:
        rel = Path(node['path'])
        dir_path = rel.parent
        # Check if there's any non-index.md file in the same directory
        dir_files = list((root / dir_path).iterdir())
        code_files = [f for f in dir_files if f.name != 'index.md' and not f.name.endswith('.md')]
        if not code_files and node['type'] == 'unknown':
            orphans.append(node['path'])

    # Detect cycles via parent edges
    cycles = detect_cycles(nodes, edges)

    return {
        'generated': datetime.now(timezone.utc).isoformat(),
        'nodes': nodes,
        'edges': edges,
        'orphans': orphans,
        'cycles': cycles,
        'dangling_links': dangling_links,
        'intent_warnings': intent_warnings,
    }


def detect_cycles(nodes: list[dict], edges: list[dict]) -> list[list[str]]:
    """
    Detect cycles in the parent-edge graph.
    Returns list of cycles, each cycle is a list of node paths.
    """
    # Build adjacency
    adj = {}
    for node in nodes:
        adj[node['path']] = []
    for edge in edges:
        if edge['label'] == 'parent':
            adj[edge['from']].append(edge['to'])

    cycles = []
    visited = set()
    stack = []

    def dfs(node: str) -> bool:
        """Returns True if a cycle was found."""
        if node in stack:
            # Found cycle — extract it
            idx = stack.index(node)
            cycle = stack[idx:] + [node]
            cycles.append(cycle)
            return True
        if node in visited:
            return False

        visited.add(node)
        stack.append(node)

        for neighbor in adj.get(node, []):
            if dfs(neighbor):
                # Found cycle — continue to find all
                pass

        stack.pop()
        return False

    for node in nodes:
        if node['path'] not in visited:
            dfs(node['path'])

    return cycles


def ensure_cns_dir(root: Path) -> Path:
    """Ensure .cns/ directory exists."""
    cns = root / '.cns'
    cns.mkdir(exist_ok=True)
    return cns


def write_graph(graph: dict, output_path: Path) -> None:
    """Write graph.json, pretty-printed."""
    output_path.write_text(json.dumps(graph, indent=2), encoding='utf-8')


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

    # Find all index.md files
    files = find_index_md_files(root)
    print(f"Found {len(files)} index.md file(s) under {root}")

    # Build graph
    graph = build_graph(files, root)

    # Report issues
    if graph['orphans']:
        print(f"Orphan documents (no nearby code): {graph['orphans']}")
    if graph['cycles']:
        print(f"Cycles detected: {graph['cycles']}")
    if graph['dangling_links']:
        print(f"Dangling parent links: {graph['dangling_links']}")
    if graph['intent_warnings']:
        for w in graph['intent_warnings']:
            print(f"Intent warning [{w['path']}]: {w['message']}")

    # Write output
    cns_dir = ensure_cns_dir(root)
    output_path = cns_dir / 'graph.json'
    write_graph(graph, output_path)
    print(f"Graph written to {output_path}")

    # Return exit code based on issues
    # Intent warnings are non-fatal (informational only)
    has_issues = graph['cycles'] or graph['dangling_links']
    return 1 if has_issues else 0


if __name__ == '__main__':
    sys.exit(main())
