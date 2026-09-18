"""Knowledge graph construction — data operations only.

LLM reasoning (concept extraction, dedup judgment, edge classification)
is handled by Claude Code. This module handles:
- Adding concept nodes to the graph
- Building co-occurrence edges (pure algorithm)
- Applying decisions from Claude Code (dedup merges, edge classifications)
- Graph persistence (save/load)
- Statistics
"""
from __future__ import annotations

import json
from pathlib import Path

import networkx as nx

from .config import Config
from .errors import GraphBuildError
from .models import ConceptNode


class KnowledgeGraphConstructor:
    def __init__(self, config: Config):
        self._config = config
        self.graph = nx.DiGraph()
        self._concepts: list[ConceptNode] = []

    def add_concepts(self, concepts: list[ConceptNode]) -> None:
        for concept in concepts:
            self._concepts.append(concept)
            self.graph.add_node(
                concept.id,
                name=concept.name,
                node_type=concept.node_type,
                gist=concept.gist,
                tags=concept.tags,
                source_memory_ids=concept.source_memory_ids,
                importance=concept.importance,
            )

    def build_cooccurrence_edges(self) -> int:
        source_map: dict[str, list[ConceptNode]] = {}
        for c in self._concepts:
            for mid in c.source_memory_ids:
                source_map.setdefault(mid, []).append(c)

        count = 0
        for siblings in source_map.values():
            for i in range(len(siblings)):
                for j in range(i + 1, len(siblings)):
                    a, b = siblings[i], siblings[j]
                    if not self.graph.has_edge(a.id, b.id):
                        self.graph.add_edge(
                            a.id, b.id,
                            edge_type="related",
                            weight=0.6,
                            description="共现于同一文档片段",
                            direction="bidirectional",
                        )
                        self.graph.add_edge(
                            b.id, a.id,
                            edge_type="related",
                            weight=0.6,
                            description="共现于同一文档片段",
                            direction="bidirectional",
                        )
                        count += 1
        return count

    def get_dedup_candidates(self) -> list[dict]:
        """Return concept pairs with similar names/tags for Claude to judge."""
        candidates = []
        concepts = self._concepts
        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):
                a, b = concepts[i], concepts[j]
                sim = self._name_similarity(a, b)
                if sim > 0.4:
                    candidates.append({
                        "a_id": a.id, "a_name": a.name, "a_gist": a.gist,
                        "b_id": b.id, "b_name": b.name, "b_gist": b.gist,
                        "similarity": sim,
                    })
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        return candidates[:100]

    def apply_dedup_decisions(self, merges: list[dict]) -> None:
        """Apply merge decisions from Claude Code.

        merges format: [{"merge": ["name1", "name2"], "canonical": "final_name"}]
        """
        name_to_canonical: dict[str, str] = {}
        for group in merges:
            if "canonical" not in group or "merge" not in group:
                continue
            for name in group["merge"]:
                name_to_canonical[name] = group["canonical"]

        seen_canonical: set[str] = set()
        ids_to_remove = []
        for concept in self._concepts:
            canonical = name_to_canonical.get(concept.name)
            if canonical:
                if canonical in seen_canonical:
                    ids_to_remove.append(concept.id)
                    concept.canonical = False
                    concept.merged_into = canonical
                else:
                    concept.name = canonical
                    self.graph.nodes[concept.id]["name"] = canonical
                    seen_canonical.add(canonical)

        for nid in ids_to_remove:
            if nid in self.graph:
                self.graph.remove_node(nid)

    def get_cross_doc_candidates(self) -> list[dict]:
        """Return concept pairs from different sources for Claude to judge edges."""
        candidates = []
        concepts = [c for c in self._concepts if c.canonical]
        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):
                a, b = concepts[i], concepts[j]
                if set(a.source_memory_ids) & set(b.source_memory_ids):
                    continue
                pair_key = tuple(sorted([a.id, b.id]))
                if self.graph.has_edge(a.id, b.id):
                    continue
                tag_overlap = len(set(a.tags) & set(b.tags))
                if tag_overlap > 0 or self._name_similarity(a, b) > 0.2:
                    candidates.append({
                        "a_id": a.id, "a_name": a.name, "a_gist": a.gist,
                        "b_id": b.id, "b_name": b.name, "b_gist": b.gist,
                        "tag_overlap": tag_overlap,
                    })
        candidates.sort(key=lambda x: x["tag_overlap"], reverse=True)
        return candidates[:200]

    def apply_edge_decisions(self, decisions: list[dict]) -> None:
        """Apply edge decisions from Claude Code.

        decisions format: [{"a_id": "...", "b_id": "...", "edge_type": "supports",
                           "direction": "a_to_b", "description": "..."}]
        """
        for d in decisions:
            a_id = d["a_id"]
            b_id = d["b_id"]
            edge_type = d.get("edge_type", "related")
            direction = d.get("direction", "bidirectional")
            description = d.get("description", "")
            weight = 0.7 if edge_type in ("supports", "contradicts") else 0.5

            if direction == "a_to_b":
                self.graph.add_edge(a_id, b_id, edge_type=edge_type, weight=weight, description=description)
            elif direction == "b_to_a":
                self.graph.add_edge(b_id, a_id, edge_type=edge_type, weight=weight, description=description)
            else:
                self.graph.add_edge(a_id, b_id, edge_type=edge_type, weight=weight, description=description)
                self.graph.add_edge(b_id, a_id, edge_type=edge_type, weight=weight, description=description)

    def save_graph(self) -> None:
        graph_path = Path(self._config.graph_path)
        graph_path.parent.mkdir(parents=True, exist_ok=True)
        data = nx.node_link_data(self.graph)
        graph_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def load_graph(self) -> nx.DiGraph:
        graph_path = Path(self._config.graph_path)
        if not graph_path.exists():
            raise GraphBuildError(
                f"图谱文件不存在: {graph_path}",
                "先运行 graph build 构建图谱",
            )
        data = json.loads(graph_path.read_text())
        self.graph = nx.node_link_graph(data)
        return self.graph

    def get_stats(self) -> dict:
        G = self.graph
        node_types: dict[str, int] = {}
        edge_types: dict[str, int] = {}
        for _, attrs in G.nodes(data=True):
            t = attrs.get("node_type", "unknown")
            node_types[t] = node_types.get(t, 0) + 1
        for _, _, attrs in G.edges(data=True):
            t = attrs.get("edge_type", "unknown")
            edge_types[t] = edge_types.get(t, 0) + 1

        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        components = nx.number_weakly_connected_components(G) if num_nodes > 0 else 0
        avg_degree = sum(d for _, d in G.degree()) / max(num_nodes, 1)

        return {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "node_types": node_types,
            "edge_types": edge_types,
            "connected_components": components,
            "avg_degree": round(avg_degree, 2),
        }

    def _name_similarity(self, a: ConceptNode, b: ConceptNode) -> float:
        """Simple character-level Jaccard similarity for name comparison."""
        chars_a = set(a.name.lower())
        chars_b = set(b.name.lower())
        if not chars_a or not chars_b:
            return 0.0
        intersection = len(chars_a & chars_b)
        union = len(chars_a | chars_b)
        return intersection / union
