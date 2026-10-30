#!/usr/bin/env python3
"""Small task-grounded parser smoke test; run untrusted solutions in a sandbox.

This checks only a minimal task example and is not a complete reference oracle.
"""
import importlib.util
import json
import re
import sys
from collections import deque
from pathlib import Path

EXAMPLE = """[Gate]
Guard: State your purpose. -> Decision

[Decision]
1. I seek shelter. -> Welcome
2. I will leave. -> Exit

[Welcome]
Narrator: The gate opens. -> End

[Exit]
Narrator: The road awaits. -> End
"""


def inspect_graph(graph):
    """Check literal evidence required by the public task's example."""
    if not isinstance(graph, dict):
        return ["result_not_object"]
    nodes, edges = graph.get("nodes"), graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return ["missing_nodes_or_edges"]
    if not all(isinstance(n, dict) for n in nodes) or not all(isinstance(e, dict) for e in edges):
        return ["invalid_node_or_edge_object"]
    issues = []
    if not any(n.get("type") == "choice" for n in nodes):
        issues.append("missing_choice_node")
    all_content = json.dumps(graph, ensure_ascii=False)
    for phrase in ("I seek shelter", "I will leave"):
        if phrase not in all_content:
            issues.append("missing_choice_text:" + phrase)
    targets = {e.get("to") for e in edges}
    for target in ("Welcome", "Exit"):
        if target not in targets:
            issues.append("missing_choice_target:" + target)
    return issues


def evaluate(solution):
    solution = Path(solution)
    if not solution.is_file():
        return ["missing_solution_file"]
    try:
        spec = importlib.util.spec_from_file_location("candidate_solution", solution)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        parser = getattr(module, "parse_script", None)
        if not callable(parser):
            return ["missing_parse_script"]
        return inspect_graph(parser(EXAMPLE))
    except Exception as exc:
        return ["parser_exception:" + type(exc).__name__]


def unreachable_node_ids(graph, start="Start"):
    """Standard directed reachability, including a present terminal End node."""
    nodes = {n["id"] for n in graph["nodes"]}
    adjacency = {}
    for edge in graph["edges"]:
        adjacency.setdefault(edge["from"], []).append(edge["to"])
    queue, visited = deque([start]), set()
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        queue.extend(adjacency.get(current, []))
    return sorted(nodes - visited)


def choice_shape_check(graph, dot):
    """Inspect simple quoted node declarations; not a general DOT parser."""
    diamond_ids = {m.group(1) for m in re.finditer(
        r'^\s*"([^"\\]+)"\s*\[shape=(?:"diamond"|diamond)(?:[,\]])', dot, re.MULTILINE)}
    choice_ids = {n["id"] for n in graph["nodes"] if n.get("type") == "choice"}
    return {"choice_count": len(choice_ids), "diamond_count": len(diamond_ids),
            "missing_choice_diamonds": sorted(choice_ids - diamond_ids),
            "nonchoice_diamonds": sorted(diamond_ids - choice_ids)}


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--shapes":
        graph = json.loads(Path(sys.argv[2]).read_text(encoding="utf8"))
        result = choice_shape_check(graph, Path(sys.argv[3]).read_text(encoding="utf8"))
        print(json.dumps(result))
        raise SystemExit(bool(not result["choice_count"] or result["missing_choice_diamonds"] or result["nonchoice_diamonds"]))
    if len(sys.argv) == 3 and sys.argv[1] == "--reachability":
        graph = json.loads(Path(sys.argv[2]).read_text(encoding="utf8"))
        failures = ["unreachable:" + x for x in unreachable_node_ids(graph)]
    elif len(sys.argv) == 2:
        failures = evaluate(sys.argv[1])
    else:
        raise SystemExit("usage: dialogue_semantic_smoke.py solution.py | --reachability graph.json | --shapes graph.json graph.dot")
    print(json.dumps({"status": "PASS" if not failures else "FAIL", "failures": failures}))
    raise SystemExit(bool(failures))
