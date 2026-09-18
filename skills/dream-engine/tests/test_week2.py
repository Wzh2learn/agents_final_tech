"""Smoke tests for Dream Engine Week 2: Graph + Activation.

Run: cd dream-engine && python3 -m pytest tests/test_week2.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from dream_engine.config import Config
from dream_engine.errors import ActivationError, GraphBuildError
from dream_engine.models import ConceptNode
from dream_engine.activation import SpreadingActivation, run_multi_round_dream
from dream_engine.graph_builder import KnowledgeGraphConstructor


@pytest.fixture
def sample_graph():
    G = nx.DiGraph()
    G.add_node("A", name="InfoNCE对比学习", node_type="method", gist="对比学习损失函数")
    G.add_node("B", name="负样本采样", node_type="method", gist="构造有效负样本")
    G.add_node("C", name="序列重复率", node_type="problem", gist="用户序列中item重复比例过高")
    G.add_node("D", name="去重策略", node_type="method", gist="减少重复推荐的方法")
    G.add_node("E", name="有效序列长度", node_type="concept", gist="去重后序列的真实有效长度")
    G.add_node("F", name="OSS配置", node_type="concept", gist="对象存储配置")

    G.add_edge("A", "B", edge_type="supports", weight=0.8)
    G.add_edge("B", "A", edge_type="supports", weight=0.8)
    G.add_edge("C", "D", edge_type="related", weight=0.7)
    G.add_edge("D", "C", edge_type="related", weight=0.7)
    G.add_edge("C", "E", edge_type="supports", weight=0.6)
    G.add_edge("E", "C", edge_type="supports", weight=0.6)
    G.add_edge("D", "E", edge_type="related", weight=0.5)
    G.add_edge("E", "D", edge_type="related", weight=0.5)
    G.add_edge("A", "C", edge_type="related", weight=0.4)
    G.add_edge("C", "A", edge_type="related", weight=0.4)
    return G


@pytest.fixture
def config():
    return Config()


class TestSpreadingActivation:
    def test_basic_activation(self, sample_graph, config):
        sa = SpreadingActivation(sample_graph, config)
        activated, parents = sa.activate(["C"], threshold=0.1)
        assert "C" in activated
        assert activated["C"] == 1.0
        assert "D" in activated
        assert "E" in activated

    def test_threshold_filters(self, sample_graph, config):
        sa = SpreadingActivation(sample_graph, config)
        high_t = sa.activate(["C"], threshold=0.5)[0]
        low_t = sa.activate(["C"], threshold=0.1)[0]
        assert len(low_t) >= len(high_t)

    def test_unrelated_not_reached(self, sample_graph, config):
        sa = SpreadingActivation(sample_graph, config)
        activated, _ = sa.activate(["C"], threshold=0.3)
        assert "F" not in activated

    def test_parents_tracking(self, sample_graph, config):
        sa = SpreadingActivation(sample_graph, config)
        _, parents = sa.activate(["C"], threshold=0.1)
        assert "D" in parents
        assert any(src == "C" for src, _ in parents["D"])

    def test_seed_not_in_graph(self, sample_graph, config):
        sa = SpreadingActivation(sample_graph, config)
        with pytest.raises(ActivationError):
            sa.activate(["NONEXISTENT"], threshold=0.1)

    def test_find_paths(self, sample_graph, config):
        sa = SpreadingActivation(sample_graph, config)
        paths = sa.find_paths("C", threshold=0.05, top_k=5)
        assert len(paths) >= 1
        for path in paths:
            assert len(path) >= 3

    def test_format_path(self, sample_graph, config):
        sa = SpreadingActivation(sample_graph, config)
        formatted = sa.format_path(["C", "D", "E"])
        assert "序列重复率" in formatted
        assert "去重策略" in formatted

    def test_multi_round(self, sample_graph, config):
        sa = SpreadingActivation(sample_graph, config)
        rounds = [
            {"name": "shallow", "threshold": 0.5, "top_k": 3},
            {"name": "deep", "threshold": 0.05, "top_k": 8},
        ]
        result = run_multi_round_dream(sa, "C", rounds)
        assert "shallow" in result
        assert "deep" in result


class TestGraphBuilder:
    def test_save_and_load(self, config, tmp_path):
        config.storage.graph_path = str(tmp_path / "graph_{namespace}.json")
        config.storage.namespace = "test"
        builder = KnowledgeGraphConstructor(config)
        builder.graph.add_node("n1", name="test", node_type="concept")
        builder.save_graph()
        assert (tmp_path / "graph_test.json").exists()

        builder2 = KnowledgeGraphConstructor(config)
        loaded = builder2.load_graph()
        assert "n1" in loaded.nodes

    def test_load_nonexistent(self, config, tmp_path):
        config.storage.graph_path = str(tmp_path / "graph_{namespace}.json")
        config.storage.namespace = "missing"
        builder = KnowledgeGraphConstructor(config)
        with pytest.raises(GraphBuildError):
            builder.load_graph()

    def test_add_concepts_and_cooccurrence(self, config):
        builder = KnowledgeGraphConstructor(config)
        concepts = [
            ConceptNode(id="c1", name="A", node_type="concept", source_memory_ids=["m1"]),
            ConceptNode(id="c2", name="B", node_type="method", source_memory_ids=["m1"]),
            ConceptNode(id="c3", name="C", node_type="finding", source_memory_ids=["m2"]),
        ]
        builder.add_concepts(concepts)
        count = builder.build_cooccurrence_edges()
        assert count == 1
        assert builder.graph.has_edge("c1", "c2")
        assert not builder.graph.has_edge("c1", "c3")

    def test_get_stats(self, sample_graph, config):
        builder = KnowledgeGraphConstructor(config)
        builder.graph = sample_graph
        stats = builder.get_stats()
        assert stats["num_nodes"] == 6
        assert stats["num_edges"] == 10

    def test_apply_edge_decisions(self, config):
        builder = KnowledgeGraphConstructor(config)
        builder.graph.add_node("a", name="A")
        builder.graph.add_node("b", name="B")
        decisions = [{"a_id": "a", "b_id": "b", "edge_type": "supports", "direction": "a_to_b", "description": "test"}]
        builder.apply_edge_decisions(decisions)
        assert builder.graph.has_edge("a", "b")
        assert builder.graph["a"]["b"]["edge_type"] == "supports"


class TestIntegration:
    def test_graph_activation_pipeline(self, sample_graph, config, tmp_path):
        config.storage.graph_path = str(tmp_path / "graph_{namespace}.json")
        config.storage.namespace = "default"
        (tmp_path / "graph_default.json").write_text(json.dumps(nx.node_link_data(sample_graph)))

        builder = KnowledgeGraphConstructor(config)
        loaded = builder.load_graph()
        sa = SpreadingActivation(loaded, config)
        paths = sa.find_paths("C", threshold=0.05, top_k=3)
        assert len(paths) >= 1
        for path in paths:
            assert "[" in sa.format_path(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
