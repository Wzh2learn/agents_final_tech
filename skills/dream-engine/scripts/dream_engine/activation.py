from __future__ import annotations

from typing import Optional

import networkx as nx
import numpy as np

from .config import Config
from .errors import ActivationError


class SpreadingActivation:
    """Collins & Loftus (1975) spreading activation over knowledge graph."""

    def __init__(self, graph: nx.DiGraph, config: Config):
        self.graph = graph
        self.decay = config.graph.spreading_activation.decay_factor
        self.max_hops = config.graph.spreading_activation.max_hops

    def activate(
        self, seed_ids: list[str], threshold: float
    ) -> tuple[dict[str, float], dict[str, list[tuple[str, float]]]]:
        """Spread activation from seeds, return (activated, parents).

        parents maps node_id -> top-3 (source_id, propagated_value) tuples
        for path reconstruction.
        """
        for sid in seed_ids:
            if sid not in self.graph:
                raise ActivationError(
                    f"种子节点不在图谱中: {sid}",
                    "检查节点 ID 是否正确，或先运行 graph build",
                )

        activated: dict[str, float] = {sid: 1.0 for sid in seed_ids}
        parents: dict[str, list[tuple[str, float]]] = {sid: [] for sid in seed_ids}

        for hop in range(self.max_hops):
            new_act: dict[str, float] = {}
            for nid, act in list(activated.items()):
                if nid not in self.graph:
                    continue
                for neighbor in self.graph[nid]:
                    edge = self.graph[nid][neighbor]
                    weight = edge.get("weight", 0.5)
                    prop = act * self.decay * weight

                    if prop <= threshold or neighbor in seed_ids:
                        continue
                    if neighbor in activated and neighbor not in new_act:
                        continue

                    if neighbor not in new_act or prop > new_act[neighbor]:
                        new_act[neighbor] = prop

                    if neighbor not in parents:
                        parents[neighbor] = []
                    parents[neighbor].append((nid, prop))
                    parents[neighbor] = sorted(
                        parents[neighbor], key=lambda x: x[1], reverse=True
                    )[:3]

            activated.update(new_act)

        return activated, parents

    def find_paths(
        self, seed_id: str, threshold: float, top_k: int = 5
    ) -> list[list[str]]:
        """Find top-k activation paths from seed, sorted by interest score."""
        activated, parents = self.activate([seed_id], threshold)
        paths: list[list[str]] = []

        for nid in activated:
            if nid == seed_id:
                continue
            path = [nid]
            cur = nid
            visited = {nid}
            while cur in parents and parents[cur]:
                prev = parents[cur][0][0]
                if prev in visited:
                    break
                path.append(prev)
                visited.add(prev)
                cur = prev
            path.reverse()
            if len(path) >= 3:
                paths.append(path)

        paths.sort(
            key=lambda p: self._interest_score(p, seed_id, activated),
            reverse=True,
        )
        return paths[:top_k]

    def format_path(self, path: list[str]) -> str:
        """Format activation path as readable string for P4 prompt."""
        parts = []
        for i, nid in enumerate(path):
            name = self.graph.nodes[nid].get("name", nid[:8])
            if i < len(path) - 1:
                next_nid = path[i + 1]
                if self.graph.has_edge(nid, next_nid):
                    edge = self.graph[nid][next_nid]
                    etype = edge.get("edge_type", "?")
                else:
                    etype = "?"
                parts.append(f"[{name}] --{etype}-\u2192")
            else:
                parts.append(f"[{name}]")
        return " ".join(parts)

    def _interest_score(
        self, path: list[str], seed_id: str, activated: dict[str, float]
    ) -> float:
        """Score path by: length bonus * terminal activation * semantic distance."""
        if not path:
            return 0.0
        terminal = path[-1]
        terminal_act = activated.get(terminal, 0.0)
        length_bonus = min(len(path) / 3.0, 2.0)

        # semantic distance: use graph shortest path length as proxy
        try:
            dist = nx.shortest_path_length(self.graph, seed_id, terminal)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            dist = len(path)

        return terminal_act * length_bonus * (dist / self.max_hops)


def run_multi_round_dream(
    activation_engine: SpreadingActivation,
    seed_id: str,
    rounds: list[dict],
) -> dict[str, list[list[str]]]:
    """Run multi-round activation with decreasing thresholds.

    Returns paths grouped by round name, with confidence annotation:
    - Paths appearing in multiple rounds -> "high"
    - Paths only in deep round -> "high_risk_high_reward"
    """
    round_paths: dict[str, list[list[str]]] = {}
    all_terminals: dict[str, set[str]] = {}

    for r in rounds:
        name = r["name"]
        threshold = r.get("activation_threshold", r.get("threshold", 0.4))
        top_k = r.get("top_k", 8)
        paths = activation_engine.find_paths(seed_id, threshold, top_k)
        round_paths[name] = paths

        terminals = {p[-1] for p in paths if p}
        all_terminals[name] = terminals

    return round_paths
