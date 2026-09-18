"""Smoke tests for Dream Engine v2 (Claude Code native mode).

Run: cd dream-engine && python3 -m pytest tests/smoke_test.py -v
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from dream_engine.config import load_config, Config
from dream_engine.models import MemoryNode, IdeaCandidate, DreamResult
from dream_engine.errors import DreamError, GraphBuildError
from dream_engine.storage import MemoryStore, content_hash
from dream_engine.output import render_dream_report, save_dream_report


# ── Config tests ─────────────────────────────────────────────

class TestConfig:
    def test_load_default_config(self, tmp_path):
        cfg = load_config(tmp_path / "nonexistent.yaml")
        assert cfg.domain.name == "推荐系统与序列建模"
        assert cfg.storage.namespace == "default"

    def test_graph_path_namespace(self):
        cfg = Config()
        assert "default" in cfg.graph_path

    def test_memories_path(self):
        cfg = Config()
        assert cfg.memories_path == "data/memories.jsonl"

    def test_load_real_yaml(self, tmp_path):
        yaml_content = """
domain:
  name: "测试领域"
  reviewer_profile: "测试reviewer"
graph:
  spreading_activation:
    decay_factor: 0.6
    max_hops: 4
  dedup_cosine_threshold: 0.9
storage:
  namespace: "test_ns"
dream:
  mode: "method"
  rounds:
    - name: shallow
      activation_threshold: 0.8
      top_k: 3
"""
        yaml_file = tmp_path / "test_config.yaml"
        yaml_file.write_text(yaml_content)
        cfg = load_config(str(yaml_file))
        assert cfg.domain.name == "测试领域"
        assert cfg.graph.spreading_activation.decay_factor == 0.6
        assert cfg.graph.spreading_activation.max_hops == 4
        assert cfg.storage.namespace == "test_ns"
        assert cfg.dream.mode == "method"
        assert len(cfg.dream.rounds) == 1


# ── Storage tests ────────────────────────────────────────────

class TestStorage:
    def test_add_and_retrieve(self, tmp_path):
        store = MemoryStore(str(tmp_path / "mem.jsonl"))
        node = MemoryNode(content="test content", source_type="paper")
        node.content_hash = content_hash(node.content)
        count = store.add_batch([node])
        assert count == 1
        assert store.count() == 1
        all_nodes = store.get_all()
        assert all_nodes[0].content == "test content"

    def test_dedup(self, tmp_path):
        store = MemoryStore(str(tmp_path / "mem.jsonl"))
        node1 = MemoryNode(content="same content", source_type="paper")
        node1.content_hash = content_hash(node1.content)
        node2 = MemoryNode(content="same content", source_type="paper")
        node2.content_hash = content_hash(node2.content)
        store.add_batch([node1])
        count = store.add_batch([node2])
        assert count == 0
        assert store.count() == 1

    def test_get_all_gists(self, tmp_path):
        store = MemoryStore(str(tmp_path / "mem.jsonl"))
        node = MemoryNode(content="long content here", gist="short gist", source_type="paper", tags=["a", "b"])
        node.content_hash = content_hash(node.content)
        store.add_batch([node])
        gists = store.get_all_gists()
        assert len(gists) == 1
        assert gists[0]["gist"] == "short gist"
        assert gists[0]["tags"] == ["a", "b"]

    def test_get_nodes_by_ids(self, tmp_path):
        store = MemoryStore(str(tmp_path / "mem.jsonl"))
        n1 = MemoryNode(content="a", content_hash=content_hash("a"))
        n2 = MemoryNode(content="b", content_hash=content_hash("b"))
        store.add_batch([n1, n2])
        result = store.get_nodes_by_ids([n1.id])
        assert len(result) == 1
        assert result[0].content == "a"

    def test_content_hash_deterministic(self):
        assert content_hash("hello world") == content_hash("hello  world")
        assert content_hash("hello") != content_hash("world")


# ── Model tests ──────────────────────────────────────────────

class TestModels:
    def test_memory_node_defaults(self):
        node = MemoryNode(content="test content")
        assert node.id
        assert node.content == "test content"
        assert node.importance == 0.5

    def test_memory_node_serialization(self):
        node = MemoryNode(content="test", source_type="paper", source_path="/a/b.md", content_hash="abc123")
        payload = node.to_payload()
        assert payload["content"] == "test"
        assert payload["content_hash"] == "abc123"
        restored = MemoryNode.from_payload(payload)
        assert restored.content == node.content
        assert restored.content_hash == "abc123"

    def test_memory_node_tags_roundtrip(self):
        node = MemoryNode(content="test", tags=["recsys", "seq2item", "序列建模"])
        payload = node.to_payload()
        assert payload["tags"] == "recsys,seq2item,序列建模"
        restored = MemoryNode.from_payload(payload)
        assert restored.tags == ["recsys", "seq2item", "序列建模"]

    def test_idea_candidate_serialization(self):
        idea = IdeaCandidate(title="test idea", novelty_score=0.8)
        d = idea.to_dict()
        restored = IdeaCandidate.from_dict(d)
        assert restored.title == "test idea"
        assert restored.novelty_score == 0.8

    def test_dream_result_serialization(self):
        idea = IdeaCandidate(title="idea1")
        result = DreamResult(ideas=[idea], total_nodes_processed=10)
        d = result.to_dict()
        restored = DreamResult.from_dict(d)
        assert len(restored.ideas) == 1
        assert restored.total_nodes_processed == 10


# ── Error tests ──────────────────────────────────────────────

class TestErrors:
    def test_dream_error_format(self):
        err = DreamError("something broke", "try this fix")
        s = str(err)
        assert "something broke" in s
        assert "try this fix" in s


# ── Output tests ─────────────────────────────────────────────

class TestOutput:
    def test_render_dream_report(self):
        idea = IdeaCandidate(
            title="Test Idea",
            problem="a problem",
            insight="an insight",
            confidence="high",
        )
        result = DreamResult(
            ideas=[idea],
            total_nodes_processed=50,
            total_paths_explored=3,
            duration_seconds=10.5,
            llm_calls=3,
        )
        md = render_dream_report(result, Config())
        assert "做梦报告" in md
        assert "Test Idea" in md

    def test_save_dream_report(self, tmp_path):
        cfg = Config()
        cfg.storage.dreams_dir = str(tmp_path / "dreams")
        idea = IdeaCandidate(title="Test")
        result = DreamResult(ideas=[idea])
        json_path, md_path = save_dream_report(result, cfg)
        assert Path(json_path).exists()
        assert Path(md_path).exists()


# ── Chunking tests ───────────────────────────────────────────

class TestChunking:
    def test_chunk_by_heading(self):
        from dream_engine.collector import MemoryCollector
        from dream_engine.storage import MemoryStore
        content = """## Section A

This is section A with enough content to pass the minimum character threshold for chunking.
It contains multiple sentences to ensure it meets the min_chars requirement of the strategy.

## Section B

This is section B with different content about a completely separate topic.
Again, multiple sentences to ensure minimum character threshold is met properly.
"""
        collector = MemoryCollector.__new__(MemoryCollector)
        chunks = collector._chunk_file(content, "paper")
        assert len(chunks) >= 1

    def test_detect_source_type(self):
        from dream_engine.collector import MemoryCollector
        collector = MemoryCollector.__new__(MemoryCollector)
        assert collector._detect_source_type("调研报告/wiki/01-论文/HLLM.md") == "paper"
        assert collector._detect_source_type("调研报告/wiki/02-概念/foo.md") == "concept"
        assert collector._detect_source_type("code/docs/EXPERIMENTS_LOG.md") == "experiment"


# ── Prompt template tests ────────────────────────────────────

class TestPromptTemplates:
    def test_all_templates_exist(self):
        prompts_dir = Path(__file__).parent.parent / "scripts" / "dream_engine" / "prompts"
        expected = ["p1_extract", "p2_edge_step1", "p2_edge_step2", "p4_rem", "p5_dedup"]
        for name in expected:
            assert (prompts_dir / f"{name}.txt").exists(), f"Missing: {name}.txt"

    def test_schemas_are_valid_json(self):
        prompts_dir = Path(__file__).parent.parent / "scripts" / "dream_engine" / "prompts"
        for schema_file in prompts_dir.glob("*_schema.json"):
            data = json.loads(schema_file.read_text())
            assert "type" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
