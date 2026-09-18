"""NREM memory consolidation: global decay + selective replay + pruning.

Based on:
- Tononi SHY (Synaptic Homeostasis Hypothesis): global multiplicative downscaling
- DeepMind Prioritized Replay: high-surprise edges get replayed first
- ScrapMem EM-Graph Pruning: progressive resolution decay

Three-step cycle:
1. SELECTIVE REPLAY: boost important/surprising edges (protect from decay)
2. GLOBAL DOWNSCALE: w = alpha * w for all edges (SHY)
3. PRUNE: remove edges below threshold
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import networkx as nx

from .config import Config


DEFAULT_GLOBAL_DECAY = 0.9
DEFAULT_PRUNE_THRESHOLD = 0.1
DEFAULT_REPLAY_BOOST = 0.15


def consolidation_cycle(
    graph: nx.DiGraph,
    global_decay: float = DEFAULT_GLOBAL_DECAY,
    prune_threshold: float = DEFAULT_PRUNE_THRESHOLD,
    replay_boost: float = DEFAULT_REPLAY_BOOST,
    replay_top_k: int = 20,
) -> dict:
    """Run one NREM consolidation cycle.

    Returns statistics about what changed.
    """
    stats = {
        "edges_before": graph.number_of_edges(),
        "nodes_before": graph.number_of_nodes(),
        "replayed": 0,
        "pruned_edges": 0,
        "pruned_nodes": 0,
    }

    # Step 1: Selective replay — boost important edges
    replayed = _selective_replay(graph, replay_boost, replay_top_k)
    stats["replayed"] = replayed

    # Step 2: Global multiplicative downscale (SHY)
    _global_downscale(graph, global_decay)

    # Step 3: Prune weak edges and isolated nodes
    pruned_edges = _prune_edges(graph, prune_threshold)
    pruned_nodes = _prune_isolated_nodes(graph)
    stats["pruned_edges"] = pruned_edges
    stats["pruned_nodes"] = pruned_nodes

    stats["edges_after"] = graph.number_of_edges()
    stats["nodes_after"] = graph.number_of_nodes()

    return stats


def _selective_replay(graph: nx.DiGraph, boost: float, top_k: int) -> int:
    """Replay top-k edges by importance score, boosting their weight.

    Priority = weight × reinforce_count × betweenness_proxy
    This protects important edges from the global downscale.
    """
    edge_scores = []
    for u, v, data in graph.edges(data=True):
        weight = data.get("weight", 0.5)
        reinforce = data.get("reinforce_count", 0) + 1
        # betweenness proxy: edges between different source clusters
        src_a = set(graph.nodes[u].get("source_memory_ids", [])) if u in graph else set()
        src_b = set(graph.nodes[v].get("source_memory_ids", [])) if v in graph else set()
        cross_source = 1.5 if not (src_a & src_b) else 1.0

        score = weight * math.log1p(reinforce) * cross_source
        edge_scores.append((u, v, score))

    edge_scores.sort(key=lambda x: x[2], reverse=True)

    replayed = 0
    for u, v, _ in edge_scores[:top_k]:
        old_w = graph[u][v].get("weight", 0.5)
        graph[u][v]["weight"] = min(1.0, old_w + boost)
        replayed += 1

    return replayed


def _global_downscale(graph: nx.DiGraph, decay_factor: float) -> None:
    """SHY: multiply all edge weights by decay_factor (< 1.0)."""
    for u, v, data in graph.edges(data=True):
        data["weight"] = data.get("weight", 0.5) * decay_factor


def _prune_edges(graph: nx.DiGraph, threshold: float) -> int:
    """Remove edges with weight below threshold."""
    to_remove = [
        (u, v) for u, v, data in graph.edges(data=True)
        if data.get("weight", 0.5) < threshold
    ]
    graph.remove_edges_from(to_remove)
    return len(to_remove)


def _prune_isolated_nodes(graph: nx.DiGraph) -> int:
    """Remove nodes with no remaining edges."""
    isolated = [n for n in graph.nodes if graph.degree(n) == 0]
    graph.remove_nodes_from(isolated)
    return len(isolated)


def run_nrem(config: Config) -> dict:
    """Load graph, run consolidation, save graph. Returns stats."""
    graph_path = Path(config.graph_path)
    if not graph_path.exists():
        return {"error": "图谱未构建"}

    graph = nx.node_link_graph(json.loads(graph_path.read_text()))

    decay = config.graph.global_decay
    stats = consolidation_cycle(graph, global_decay=decay)

    graph_path.write_text(json.dumps(nx.node_link_data(graph), ensure_ascii=False, indent=2))

    return stats
