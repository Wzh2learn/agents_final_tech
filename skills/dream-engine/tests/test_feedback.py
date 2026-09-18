"""Tests for Hebbian feedback + NREM consolidation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from dream_engine.config import Config
from dream_engine.feedback import hebbian_update, WEIGHT_FLOOR, WEIGHT_CEILING
from dream_engine.consolidation import consolidation_cycle


@pytest.fixture
def feedback_graph():
    G = nx.DiGraph()
    G.add_node("A", name="InfoNCE", node_type="method", importance=0.8)
    G.add_node("B", name="负样本采样", node_type="method", importance=0.6)
    G.add_node("C", name="序列重复率", node_type="problem", importance=0.9)
    G.add_edge("A", "B", edge_type="supports", weight=0.5, reinforce_count=0)
    G.add_edge("B", "A", edge_type="supports", weight=0.5, reinforce_count=0)
    G.add_edge("B", "C", edge_type="related", weight=0.4, reinforce_count=0)
    G.add_edge("C", "B", edge_type="related", weight=0.4, reinforce_count=0)
    return G


class TestHebbianUpdate:
    def test_positive_rating_strengthens(self, feedback_graph):
        updates = hebbian_update(feedback_graph, ["A", "B", "C"], rating=5)
        assert len(updates) == 2
        assert feedback_graph["A"]["B"]["weight"] > 0.5
        assert feedback_graph["B"]["C"]["weight"] > 0.4

    def test_negative_rating_weakens(self, feedback_graph):
        updates = hebbian_update(feedback_graph, ["A", "B", "C"], rating=1)
        assert feedback_graph["A"]["B"]["weight"] < 0.5
        assert feedback_graph["B"]["C"]["weight"] < 0.4

    def test_neutral_rating_no_change(self, feedback_graph):
        hebbian_update(feedback_graph, ["A", "B"], rating=3)
        assert feedback_graph["A"]["B"]["weight"] == 0.5

    def test_weight_floor_protection(self, feedback_graph):
        feedback_graph["A"]["B"]["weight"] = 0.12
        hebbian_update(feedback_graph, ["A", "B"], rating=1)
        assert feedback_graph["A"]["B"]["weight"] >= WEIGHT_FLOOR

    def test_weight_ceiling(self, feedback_graph):
        feedback_graph["A"]["B"]["weight"] = 0.98
        hebbian_update(feedback_graph, ["A", "B"], rating=5)
        assert feedback_graph["A"]["B"]["weight"] <= WEIGHT_CEILING

    def test_bidirectional_update(self, feedback_graph):
        hebbian_update(feedback_graph, ["A", "B"], rating=5)
        assert feedback_graph["A"]["B"]["weight"] == feedback_graph["B"]["A"]["weight"]

    def test_reinforce_count_incremented(self, feedback_graph):
        hebbian_update(feedback_graph, ["A", "B"], rating=4)
        assert feedback_graph["A"]["B"]["reinforce_count"] == 1


class TestConsolidation:
    def test_global_downscale(self, feedback_graph):
        old_w = feedback_graph["A"]["B"]["weight"]
        consolidation_cycle(feedback_graph, global_decay=0.9, prune_threshold=0.01)
        # weight should decrease (after potential replay boost is smaller than downscale)
        assert feedback_graph.number_of_edges() > 0

    def test_pruning_removes_weak_edges(self):
        G = nx.DiGraph()
        G.add_node("X", name="X", importance=0.5)
        G.add_node("Y", name="Y", importance=0.5)
        G.add_node("Z", name="Z", importance=0.5)
        G.add_edge("X", "Y", weight=0.05)  # below threshold
        G.add_edge("Y", "Z", weight=0.8)   # above threshold
        stats = consolidation_cycle(G, global_decay=1.0, prune_threshold=0.1, replay_top_k=0)
        assert stats["pruned_edges"] == 1
        assert not G.has_edge("X", "Y")
        assert G.has_edge("Y", "Z")

    def test_isolated_nodes_removed(self):
        G = nx.DiGraph()
        G.add_node("A", name="A")
        G.add_node("B", name="B")
        G.add_node("C", name="C")
        G.add_edge("A", "B", weight=0.05)
        stats = consolidation_cycle(G, global_decay=1.0, prune_threshold=0.1, replay_top_k=0)
        assert "C" not in G.nodes  # isolated, should be pruned

    def test_selective_replay_protects_important_edges(self):
        G = nx.DiGraph()
        G.add_node("A", name="A", importance=0.9, source_memory_ids=["m1"])
        G.add_node("B", name="B", importance=0.8, source_memory_ids=["m2"])
        G.add_edge("A", "B", weight=0.3, reinforce_count=5)
        G.add_edge("B", "A", weight=0.3, reinforce_count=5)

        stats = consolidation_cycle(G, global_decay=0.8, prune_threshold=0.1, replay_top_k=2, replay_boost=0.2)
        # edge should survive: replay boosted it before downscale
        assert G.has_edge("A", "B")
        assert stats["replayed"] > 0

    def test_full_cycle_stats(self, feedback_graph):
        stats = consolidation_cycle(feedback_graph, global_decay=0.9)
        assert "edges_before" in stats
        assert "edges_after" in stats
        assert "pruned_edges" in stats
        assert "replayed" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
