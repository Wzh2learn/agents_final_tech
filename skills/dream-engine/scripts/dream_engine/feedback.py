"""Hebbian feedback loop: user ratings adjust graph edge weights.

Based on:
- Three-factor Hebbian rule (Remnic pattern): delta_w = eta * activation * signal
- SHY-inspired floor protection: edges never drop below 0.1
- FSRS-inspired stability: frequently reinforced edges decay slower

Algorithm:
1. User rates idea → find dream_path (concept node sequence)
2. For each edge along the path: apply Hebbian weight update
3. Positive rating → strengthen edges (potentiation)
4. Negative rating → weaken edges (depression)
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import networkx as nx

from .config import Config

WEIGHT_FLOOR = 0.1
WEIGHT_CEILING = 1.0
DEFAULT_LEARNING_RATE = 0.05


def hebbian_update(
    graph: nx.DiGraph,
    dream_path: list[str],
    rating: int,
    learning_rate: float = DEFAULT_LEARNING_RATE,
) -> list[dict]:
    """Apply Hebbian weight update to edges along a dream path.

    Args:
        graph: the knowledge graph
        dream_path: list of node IDs forming the dream path
        rating: user rating 1-5
        learning_rate: η in the Hebbian rule

    Returns:
        list of edge update records for logging
    """
    signal = (rating - 3.0) / 2.0  # normalize to [-1, +1]
    updates = []

    for i in range(len(dream_path) - 1):
        src, tgt = dream_path[i], dream_path[i + 1]

        if not graph.has_edge(src, tgt):
            continue

        edge = graph[src][tgt]
        old_weight = edge.get("weight", 0.5)

        src_importance = graph.nodes[src].get("importance", 0.5) if src in graph else 0.5
        tgt_importance = graph.nodes[tgt].get("importance", 0.5) if tgt in graph else 0.5
        activation = (src_importance + tgt_importance) / 2.0

        delta_w = learning_rate * activation * signal
        new_weight = _clamp(old_weight + delta_w, WEIGHT_FLOOR, WEIGHT_CEILING)

        graph[src][tgt]["weight"] = new_weight
        reinforce_count = edge.get("reinforce_count", 0)
        graph[src][tgt]["reinforce_count"] = reinforce_count + 1

        # bidirectional: update reverse edge too if exists
        if graph.has_edge(tgt, src):
            graph[tgt][src]["weight"] = new_weight
            graph[tgt][src]["reinforce_count"] = graph[tgt][src].get("reinforce_count", 0) + 1

        updates.append({
            "edge": f"{src[:8]}→{tgt[:8]}",
            "old_weight": round(old_weight, 3),
            "new_weight": round(new_weight, 3),
            "delta": round(delta_w, 4),
            "signal": signal,
        })

    return updates


def apply_rating_feedback(
    config: Config,
    idea_id: str,
    rating: int,
) -> dict:
    """Full feedback pipeline: find idea → update graph edges → save.

    Returns summary of what changed.
    """
    from .output import load_dream_results

    # find the idea and its dream path
    results = load_dream_results(config, limit=50)
    target_idea = None
    for result in results:
        for idea in result.ideas:
            if idea.id == idea_id or idea.id.startswith(idea_id):
                target_idea = idea
                break
        if target_idea:
            break

    if not target_idea:
        return {"error": f"Idea not found: {idea_id}"}

    if not target_idea.dream_path:
        return {"warning": "Idea has no dream_path, cannot update graph edges", "idea": target_idea.title}

    # load graph
    graph_path = Path(config.graph_path)
    if not graph_path.exists():
        return {"warning": "Graph not built yet, rating saved but no edge updates", "idea": target_idea.title}

    graph = nx.node_link_graph(json.loads(graph_path.read_text()))

    # find node IDs matching dream_path names
    name_to_id = {}
    for nid, attrs in graph.nodes(data=True):
        name = attrs.get("name", "")
        name_to_id[name] = nid

    path_ids = []
    for name in target_idea.dream_path:
        if name in name_to_id:
            path_ids.append(name_to_id[name])

    if len(path_ids) < 2:
        return {"warning": "Could not resolve dream path to graph nodes", "path": target_idea.dream_path}

    # apply Hebbian update
    updates = hebbian_update(graph, path_ids, rating)

    # save graph
    graph_path.write_text(json.dumps(nx.node_link_data(graph), ensure_ascii=False, indent=2))

    return {
        "idea": target_idea.title,
        "rating": rating,
        "edges_updated": len(updates),
        "updates": updates,
    }


def _clamp(value: float, floor: float, ceiling: float) -> float:
    return max(floor, min(ceiling, value))
